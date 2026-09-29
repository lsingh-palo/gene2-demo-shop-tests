#!/usr/bin/env python3
"""Create or update a Jira bug from a Gen-e2 bug report, idempotently.

Idempotency: each Gen-e2 bug carries a stable fingerprint label `gene2:<slug>:<bugkey>` where
`bugkey` is a hash of (slug, module, normalized title). Before creating, this script searches
for an open issue with that label. If found, it adds a comment (new occurrence / still failing)
instead of creating a duplicate. When the reproduction test passes again, call with --resolve to
add a "reproduction test now green" comment and transition the issue.

Cleanup by label, never by key number: every issue this script creates carries `gene2-live` and
`gene2-suite-<slug>`, and every comment it writes starts with the marker line
`[gene2-live <slug> run <run id>]`, so `gene2 clean --jira` removes exactly what runs created.

--from-triage files the rows of a triage.json (`gene2 triage`) that were CONFIRMED as product_bug
or known_bug, one issue per fingerprint (several tests showing one defect become one bug listing
every test): steps from the reproduction test, expected vs actual, the screenshot attached, a
build + environment block, a "relates to" link to each Jira story of the requirement, and the test
cases (TC id, test path, QMetry key when synced). A duplicate gets one marker comment instead.

Env: ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN, JIRA_PROJECT_KEY
Optional: JIRA_BUG_ISSUETYPE (default "Bug")

Usage:
    python tools/jira_bug.py --report reports/bugs_20260908.md --slug app-example-com
    python tools/jira_bug.py --slug app-example-com --module cart --title "badge not updated" \\
        --severity High --steps steps.txt --expected "..." --actual "..." [--test <path::name>] [--dry-run]
        [--label release-42]
    python tools/jira_bug.py --slug app-example-com --bugkey <hash> --resolve
    python tools/jira_bug.py --slug app-example-com --from-triage test_runs/<run>/docs/triage.json \
        [--app-url URL --variant NAME --browser chromium] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

import requests

import _secrets
import bug_ledger


def _auth():
    base, auth = _secrets.atlassian()
    proj = _secrets.get("JIRA_PROJECT_KEY")
    if not proj:
        sys.exit("Set JIRA_PROJECT_KEY (keychain, credentials file, or env)")
    return base, auth, proj


def bugkey(slug: str, module: str, title: str) -> str:
    norm = re.sub(r"[^a-z0-9 ]", "", title.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    return hashlib.sha1(f"{slug}|{module}|{norm}".encode()).hexdigest()[:10]


def label(slug: str, bk: str) -> str:
    return f"gene2:{slug}:{bk}"


LIVE = "gene2-live"


def suite_label(slug: str) -> str:
    return f"gene2-suite-{slug}"


def marker(slug: str, run: str) -> str:
    """First line of every comment a run writes: what `gene2 clean --jira` looks for."""
    return f"[{LIVE} {slug} run {run or 'manual'}]"


def harness_version() -> str:
    here = pathlib.Path(__file__).resolve().parent
    for f in (here.parent / "VERSION", here.parent / ".claude-plugin" / "plugin.json"):
        if f.exists():
            t = f.read_text().strip()
            return json.loads(t).get("version", "?") if f.suffix == ".json" else t
    return "?"


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def env_block(run: str, app_url: str = "", variant: str = "", browser: str = "") -> str:
    ci_run = next((f"{k}={os.environ[k]}" for k in ("GITHUB_RUN_ID", "CI_PIPELINE_ID", "BUILD_ID") if os.environ.get(k)), "local")
    return "\n".join([
        "Build and environment:",
        f"- app: {app_url or os.environ.get('GENE2_BASE_URL', '(not given)')}"
        + (f"  variant: {variant or os.environ.get('GENE2_APP_VARIANT')}" if (variant or os.environ.get('GENE2_APP_VARIANT')) else ""),
        f"- browser: {browser or os.environ.get('GENE2_PRIMARY_BROWSER', 'chromium')}",
        f"- run: {run or 'manual'}   CI: {ci_run}",
        f"- commit: {_git('rev-parse', '--short', 'HEAD') or '?'}   branch: {_git('rev-parse', '--abbrev-ref', 'HEAD') or '?'}",
        f"- harness: Gen-e2 {harness_version()}   date: {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC",
    ])


def test_steps(suite: pathlib.Path, test_file: str, test_name: str) -> str:
    """The reproduction steps are the test's own statements (docstring removed), numbered."""
    import ast
    src = suite / test_file
    if not src.exists():
        return "(see the reproduction test)"
    text = src.read_text(encoding="utf-8")
    fn = next((n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef) and n.name == test_name), None)
    if fn is None:
        return "(see the reproduction test)"
    body = [n for n in fn.body if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant)
                                       and isinstance(n.value.value, str))]
    steps = [" ".join((ast.get_source_segment(text, n) or "").split()) for n in body]
    return "\n".join(f"{i}. {st}" for i, st in enumerate(steps, 1)) or "(see the reproduction test)"


def _adf(text: str) -> dict:
    return {
        "type": "doc", "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": line}]}
            for line in text.splitlines() or [text]
        ],
    }


def find_open(base, auth, lbl: str):
    jql = f'labels = "{lbl}" AND statusCategory != Done ORDER BY created DESC'
    # /rest/api/3/search is deprecated (Atlassian retiring it) - /search/jql is the replacement.
    r = requests.get(f"{base}/rest/api/3/search/jql", params={"jql": jql, "fields": "key,summary,status"},
                     auth=auth, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    issues = r.json().get("issues", [])
    return issues[0] if issues else None


def create(base, auth, proj, summary, body, lbl, severity, extra_labels=(), slug=""):
    payload = {
        "fields": {
            "project": {"key": proj},
            "issuetype": {"name": _secrets.get("JIRA_BUG_ISSUETYPE", "Bug")},
            "summary": summary[:250],
            "description": _adf(body),
            "labels": [lbl, "gene2", LIVE, *([suite_label(slug)] if slug else []),
                       f"severity-{severity.lower()}", *extra_labels],
        }
    }
    r = requests.post(f"{base}/rest/api/3/issue", json=payload, auth=auth,
                      headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()["key"]


def attach(base, auth, key, path):
    """Jira REST v3 Add attachment: multipart field `file`, header X-Atlassian-Token: no-check."""
    with open(path, "rb") as fh:
        r = requests.post(f"{base}/rest/api/3/issue/{key}/attachments", files={"file": (os.path.basename(path), fh)},
                          auth=auth, headers={"X-Atlassian-Token": "no-check", "Accept": "application/json"}, timeout=60)
    r.raise_for_status()


def link(base, auth, bug_key, story_key):
    """A "Relates" link from the bug to the story of the requirement it breaks."""
    r = requests.post(f"{base}/rest/api/3/issueLink", json={"type": {"name": "Relates"}, "inwardIssue": {"key": bug_key},
                                                            "outwardIssue": {"key": story_key}},
                      auth=auth, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()


def comment(base, auth, key, text):
    r = requests.post(f"{base}/rest/api/3/issue/{key}/comment", json={"body": _adf(text)},
                      auth=auth, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()


def triage_groups(t: dict) -> list[dict]:
    """Confirmed product_bug / known_bug rows, one group per fingerprint (module + title)."""
    groups: dict[tuple, dict] = {}
    for r in t["rows"]:
        if not r.get("confirmed") or r["class"] not in ("product_bug", "known_bug"):
            continue
        g = groups.setdefault((r["bug_module"], r["bug_title"]), {"module": r["bug_module"], "title": r["bug_title"],
                                                                   "severity": r.get("severity", "Medium"), "rows": []})
        g["rows"].append(r)
    return list(groups.values())


def triage_body(slug: str, g: dict, run: str, env: str, fp: str, qmetry: dict) -> str:
    suite = pathlib.Path("consolidated") / slug
    first = g["rows"][0]
    tests = "\n".join(f"- {r['tc_id']} {r['title']}: consolidated/{slug}/{r['test_file']}::{r['test']}"
                      + (f" (QMetry {qmetry[r['tc_id']]})" if qmetry.get(r["tc_id"]) else "")
                      + f"\n  expected: {r['expected'] or '-'}   actual: {r['actual'] or '-'}" for r in g["rows"])
    reqs = sorted({q for r in g["rows"] for q in r.get("requirements", [])})
    return (f"Reported by Gen-e2 test harness after triage (confirmed: {first['reason']}).\n"
            f"Target: {slug}   Module: {g['module']}   Severity: {g['severity']}\n"
            f"Fingerprint: {fp}\n"
            f"Requirement: {', '.join(reqs) or '-'}\n\n"
            f"Steps to reproduce (from {first['test_file']}::{first['test']}):\n"
            f"{test_steps(suite, first['test_file'], first['test'])}\n\n"
            f"Expected: {first['expected'] or g['title']}\n"
            f"Actual: {first['actual'] or '(see the assertion)'}\n"
            f"Assertion: {first['message'].splitlines()[0] if first['message'] else '-'}\n\n"
            f"Test cases that show it:\n{tests}\n\n{env}\n"
            + ("\nScreenshot on failure attached." if first.get("screenshots") else ""))


def from_triage(a, base, auth, proj) -> int:
    t = json.loads(pathlib.Path(a.from_triage).read_text())
    slug, run = t["slug"], a.run or t.get("run", "")
    qpath = pathlib.Path("consolidated") / slug / "qmetry-cases.json"
    qmetry = json.loads(qpath.read_text()) if qpath.exists() else {}
    groups = triage_groups(t)
    unconfirmed = [r["test"] for r in t["rows"] if not r.get("confirmed")]
    if unconfirmed:
        print(f"note: {len(unconfirmed)} row(s) not confirmed, never filed: {', '.join(unconfirmed)}")
    env = env_block(run, a.app_url, a.variant, a.browser)
    for g in groups:
        bk = bugkey(slug, g["module"], g["title"])
        fp = label(slug, bk)
        stories = sorted({s for r in g["rows"] for s in r.get("stories", [])})
        shot = next((p for r in g["rows"] for p in r.get("screenshots", []) if os.path.exists(p)), None)
        summary = f"[{slug}] {g['module']}: {g['title']}"
        body = triage_body(slug, g, run, env, fp, qmetry)
        tests = ", ".join(r["tc_id"] or r["test"] for r in g["rows"])
        if a.dry_run:
            dup = next((r.get("duplicate_of") for r in g["rows"] if r.get("duplicate_of")), "")
            if dup:
                print(f"\n[dry-run] {summary}\n  duplicate of {dup} (triage): one comment on {dup}, no new issue; tests: {tests}")
                continue
            print(f"\n[dry-run] {summary}\n  fingerprint {fp}; if open -> one comment, else create with labels "
                  f"{LIVE}, {suite_label(slug)}; links: {', '.join(stories) or 'none'}; screenshot: {shot or 'none'}; tests: {tests}")
            print("  " + body.replace("\n", "\n  "))
            continue
        dup = next((r.get("duplicate_of") for r in g["rows"] if r.get("duplicate_of")), "")
        existing = {"key": dup} if dup else find_open(base, auth, fp)
        if existing:
            key = existing["key"]
            comment(base, auth, key, f"{marker(slug, run)}\nGen-e2: this bug reproduced again ({tests}). "
                                     f"Still failing. No duplicate created.\n\n{env}")
            print(f"duplicate {key}: commented ({tests})")
        else:
            key = create(base, auth, proj, summary, body, fp, g["severity"], a.label, slug=slug)
            for st in stories:
                link(base, auth, key, st)
            if shot:
                attach(base, auth, key, shot)
            print(f"created {key} ({tests}); linked {', '.join(stories) or 'no story'}; "
                  f"{'screenshot attached' if shot else 'no screenshot'}")
        first = g["rows"][0]
        bug_ledger.record(slug, bk, "open", jira=key, title=g["title"], module=g["module"], severity=g["severity"],
                          test=f"{first['test_file']}::{first['test']}")
    print(f"{len(groups)} bug group(s) from {sum(len(g['rows']) for g in groups)} confirmed row(s)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    p.add_argument("--report")
    p.add_argument("--module")
    p.add_argument("--title")
    p.add_argument("--severity", default="Medium")
    p.add_argument("--steps")
    p.add_argument("--expected", default="")
    p.add_argument("--actual", default="")
    p.add_argument("--bugkey")
    p.add_argument("--test", help="the reproduction test, e.g. tests/test_checkout.py::test_x")
    p.add_argument("--resolve", action="store_true")
    p.add_argument("--label", action="append", default=[],
                   help="extra label on a new issue (repeatable), e.g. release-42 or a team label")
    p.add_argument("--from-triage", help="file the confirmed rows of a triage.json (gene2 triage)")
    p.add_argument("--run", default="", help="run id for the comment marker and the env block")
    p.add_argument("--app-url", default="")
    p.add_argument("--variant", default="")
    p.add_argument("--browser", default="")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    base, auth, proj = (None, None, None) if a.dry_run else _auth()
    if a.from_triage:
        return from_triage(a, base, auth, proj)

    if a.resolve:
        bk = a.bugkey or sys.exit("--resolve needs --bugkey")
        lbl = label(a.slug, bk)
        if a.dry_run:
            print(f"[dry-run] would find open issue labelled {lbl}, comment 'reproduction test "
                  f"now green', and transition toward Done")
            return 0
        issue = find_open(base, auth, lbl)
        if not issue:
            print(f"no open issue for {lbl}; nothing to resolve")
            return 0
        comment(base, auth, issue["key"], f"{marker(a.slug, a.run)}\nGen-e2: the reproduction test for this bug "
                "now passes. Please verify and close.")
        bug_ledger.record(a.slug, bk, "fixed", jira=issue["key"])
        print(f"commented on {issue['key']}; ledger: fixed")
        return 0

    if not (a.module and a.title):
        sys.exit("need --module and --title (or parse --report first)")

    bk = bugkey(a.slug, a.module, a.title)
    lbl = label(a.slug, bk)
    steps = open(a.steps).read() if a.steps else "(see reproduction test)"
    body = (
        f"Reported by Gen-e2 test harness.\n"
        f"Target: {a.slug}   Module: {a.module}   Severity: {a.severity}\n"
        f"Fingerprint: {lbl}\n\n"
        f"Steps to reproduce:\n{steps}\n\n"
        f"Expected: {a.expected}\n"
        f"Actual: {a.actual}\n\n"
        f"Reproduction test: consolidated/{a.slug}/{a.test or f'tests/test_bug_{bk}.py'} "
        f"(fails until fixed)."
    )
    summary = f"[{a.slug}] {a.module}: {a.title}"

    if a.dry_run:
        print(f"[dry-run] fingerprint label: {lbl}" + (f"  extra labels: {a.label}" if a.label else ""))
        print(f"[dry-run] would search for an open issue with that label;")
        print(f"[dry-run] if none, create:\n  summary: {summary}\n  {body}")
        return 0

    existing = find_open(base, auth, lbl)
    if existing:
        comment(base, auth, existing["key"],
                f"{marker(a.slug, a.run)}\nGen-e2: this bug reproduced again on the latest run ({a.severity}). "
                f"Still failing. No duplicate created.")
        print(f"updated existing {existing['key']} ({existing['fields']['status']['name']})")
        key = existing["key"]
    else:
        key = create(base, auth, proj, summary, body, lbl, a.severity, a.label, slug=a.slug)
        print(f"created {key}  ({base}/browse/{key})")
    bug_ledger.record(a.slug, bk, "open", jira=key, title=a.title, module=a.module,
                      severity=a.severity, **({"test": a.test} if a.test else {}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
