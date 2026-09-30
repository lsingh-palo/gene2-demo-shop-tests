#!/usr/bin/env python3
"""Before a run you will show people: is everything ready, and is anything left over from the last one?

    gene2 preflight --slug S [--offline]

Read-only: it never deletes, creates or starts anything. It checks the repo (branch, uncommitted,
unpushed), local leftovers of earlier runs, whether the app under test is already answering,
which credentials are set (names only, never values), what `gene2 clean` would remove in Jira and
QMetry (with --reset-bugs, so bugs filed before today count as leftovers), the bug ledger, the last
CI runs and the live report site - then prints what to clear and the exact command for each.
--offline skips every network check.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import socket
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_report  # noqa: E402

CREDENTIALS = ("QMETRY_API_KEY", "JIRA_PROJECT_KEY", "ATLASSIAN_BASE_URL", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN")


def app_url(suite: pathlib.Path) -> str:
    c = run_report._json(suite / "config" / "suite-config.json", {})
    return c.get("website_url") or c.get("base_url") or ""


def answering(url: str) -> bool:
    u = urllib.parse.urlparse(url)
    if not u.hostname:
        return False
    try:
        with socket.create_connection((u.hostname, u.port or (443 if u.scheme == "https" else 80)), timeout=1):
            return True
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()
    suite = root / "consolidated" / a.slug
    if not suite.exists():
        print(f"no suite at {suite}", file=sys.stderr)
        return 2
    rows, todo = [], []  # (check, state, detail)

    def row(check, ok, detail, fix=None):
        rows.append((check, "OK" if ok is True else ("CLEAR" if ok is False else ok), detail))
        if fix:
            todo.append(fix)

    git = lambda *x: run_report.git(root, *x)  # noqa: E731
    # a wrapper (such as an app repo's launcher) can name its own commands for the fixes
    local_clean = os.environ.get("GENE2_LOCAL_CLEAN_CMD") or "python tools/clean.py --slug %s --apply" % a.slug
    remote_clean = (os.environ.get("GENE2_REMOTE_CLEAN_CMD")
                    or "python tools/clean.py --slug %s --jira --qmetry --reset-bugs --apply" % a.slug)
    br = git("rev-parse", "--abbrev-ref", "HEAD")
    remote = run_report.web_remote(git("remote", "get-url", "origin"))
    if not a.offline:
        git("fetch", "-q", "origin", br)
    dirty = [l for l in git("status", "--porcelain").splitlines() if l.strip()]
    ahead = git("rev-list", "--count", f"origin/{br}..HEAD") or "?"
    row("Repo", True, f"`{root}` on `{br}` ({remote or 'no remote'})")
    row("Uncommitted changes", not dirty or "WARN",
        f"{len(dirty)} file(s): " + ", ".join(l.split(maxsplit=1)[-1] for l in dirty[:6]) if dirty else "none")
    row("Unpushed commits", ahead in ("0", "?") or "WARN", f"{ahead} ahead of origin/{br}",
        f"push them so CI runs what you have: git push origin {br}" if ahead not in ("0", "?") else None)

    leftovers = [n for n in ("reports", "qmetry-version.json", "qmetry-cases.json", "app-under-test.log") if (suite / n).exists()]
    row("Local run leftovers", not leftovers, ", ".join(f"consolidated/{a.slug}/{n}" for n in leftovers) or "none",
        f"{local_clean}   (local only, no host to type)" if leftovers else None)

    url = app_url(suite)
    up = answering(url) if url else False
    row("App under test", "RUNNING" if up else "stopped", f"{url or '(no url in config)'} "
        + ("is answering: a run would reuse it, whatever version it is" if up else "is not running: run.sh starts it via GENE2_APP_START"),
        f"stop the app on {url} before a run (a run that starts its own app must not find another one there)" if up else None)

    try:
        import _secrets
        have = {n: bool(_secrets.get(n)) for n in CREDENTIALS}
    except SystemExit as e:
        have = {n: False for n in CREDENTIALS}
        print(f"credentials: {e}", file=sys.stderr)
    missing = [n for n, v in have.items() if not v]
    row("Credentials (names only)", not missing or "MISSING",
        "all set" if not missing else "missing: " + ", ".join(missing),
        "save the missing ones: security add-generic-password -U -s gene2 -a <NAME> -w \"$(pbpaste)\"" if missing else None)

    ledger = run_report._json(suite / "bugs.json", {"bugs": []}).get("bugs", [])
    open_bugs = [b for b in ledger if b.get("status") == "open" and b.get("jira")]
    row("Bug ledger", not open_bugs or "OLD BUGS",
        f"{len(open_bugs)} open bug(s) from earlier runs: {', '.join(b['jira'] for b in open_bugs[:12])}" if open_bugs else "empty",
        None)

    if not a.offline and not missing:
        import clean
        import jira_live
        import qmetry_sync
        project = _secrets.get("JIRA_PROJECT_KEY")
        try:
            jp = clean.jira_plan(jira_live.JiraClient(), project, a.slug, [], clean.suite_issue_keys(root, a.slug),
                                 clean.ledger_fingerprints(root, a.slug))
            n_i, n_c = len(jp["issues"]), len(jp["comments"])
            row("Jira leftovers", not (n_i or n_c), f"{n_i} bug(s) ({', '.join(i['key'] for i in jp['issues'][:12])}), "
                f"{n_c} harness comment(s)" if (n_i or n_c) else "none")
        except Exception as e:  # noqa: BLE001
            n_i = n_c = 0
            row("Jira leftovers", "ERROR", str(e)[:120])
        try:
            q = qmetry_sync.Client((_secrets.get("QMETRY_BASE_URL") or qmetry_sync.DEFAULT_BASE).rstrip("/"),
                                   _secrets.get("QMETRY_API_KEY"))
            qp = clean.qmetry_plan(q, project, a.slug)
            n_cy, n_ca = len(qp["cycles"]), len(qp["cases"])
            row("QMetry leftovers", not (n_cy or n_ca), f"{n_cy} cycle(s) with their executions, {n_ca} test case(s)"
                if (n_cy or n_ca) else "none (next run is Version 1.0)")
        except Exception as e:  # noqa: BLE001
            n_cy = n_ca = 0
            row("QMetry leftovers", "ERROR", str(e)[:120])
        if n_i or n_c or n_cy or n_ca or open_bugs:
            todo.append(f"YOU type this one (it asks for the Jira host): {remote_clean}"
                        + (" ; then commit and push the emptied bugs.json" if open_bugs else ""))

    if not a.offline and remote.startswith("https://github.com/"):
        import ci
        try:
            full, web, pages = ci.repo(root)
            last = ci.runs(full, None, 3)
            row("Last CI runs", True, "<br>".join(ci.describe(r) for r in last) or "none")
            rep = ci.fetch_text(f"{pages}run-report.json")
            held = json.loads(rep).get("run_id") if rep else None
            row("Live Allure report", bool(ci.fetch_text(pages)) or "DOWN", f"{pages} (holds run {held or '-'})")
        except SystemExit as e:
            row("CI", "ERROR", str(e)[:120])

    print(f"# Preflight: {a.slug}\n\n| Check | State | Detail |\n|---|---|---|")
    for c, s, d in rows:
        print(f"| {c} | {s} | {d} |")
    print("\n## To clear before you start\n")
    print("\n".join(f"{i}. {t}" for i, t in enumerate(todo, 1)) if todo else "Nothing: ready for a clean start.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
