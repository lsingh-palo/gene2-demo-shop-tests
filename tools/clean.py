#!/usr/bin/env python3
"""gene2 clean: remove what runs of one suite created, locally and (on request) in Jira and QMetry.

    gene2 clean --slug S                          # dry run: lists every path, issue, comment, case, cycle
    gene2 clean --slug S --apply                  # local only: the suite folder, its runs, its warehouse
    gene2 clean --slug S --jira --apply           # + Jira: you TYPE the Jira host before anything is deleted
    gene2 clean --slug S --qmetry --apply         # + QMetry: you TYPE the Jira host (QMetry lives in it)
    [--protect LABEL]                             # never delete an issue carrying LABEL (repeatable)
    [--reset-bugs]                                # with --jira: also every bug in the ledger, ledger cleared
    [--no-local]                                  # remote only: the suite and its runs stay as they are

What is found, never by key number or range, only by label and marker:
  local   consolidated/<slug>/ and test_runs/<slug>-*/ that git does NOT track. A committed suite or a
          frozen run is listed as kept and never deleted (remove those with a reviewed commit); its
          untracked run outputs (reports/, qmetry-version.json, qmetry-cases.json, app log) do go.
  jira    issues labelled `gene2-live` AND `gene2-suite-<slug>` (the bugs runs filed), and comments
          whose first line is a run marker `[gene2-live <slug> run ...]` or the story status marker
          `[gene2-live <slug> story-status]` (on any issue: a duplicate bug, a story). With
          --reset-bugs, also every bug in the suite's ledger that a run filed: fingerprint label
          `gene2:<slug>:<bugkey>` AND jira_bug.py's title "[<slug>] <module>: <title>" (a bug filed
          before the gene2-live label existed has only those). A seeded bug that carries a
          fingerprint on purpose keeps its own title, so it is never taken.
          Ledger entries of deleted issues are removed from bugs.json.
  qmetry  test cases labelled `gene2-live` and `<slug>`; test cycles named `gene2 <slug> ...`, and with
          them their executions (an execution only exists inside its cycle).

Safety: dry run by default. Each remote delete asks you to type the host at the terminal; there is
no flag that skips it, so a pipeline or an AI assistant cannot run it. Counts are printed before and
after. Jira issue keys are never reused, so numbers keep climbing after a clean: that is expected.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jira_live  # noqa: E402

LIVE = "gene2-live"


def suite_label(slug: str) -> str:
    return f"gene2-suite-{slug}"


def run_marker_prefix(slug: str) -> str:
    return f"[{LIVE} {slug} run "


def story_marker(slug: str) -> str:
    return f"[{LIVE} {slug} story-status]"


# ------------------------------------------------------------------------------------------ local
def _tracked(root: pathlib.Path, path: pathlib.Path) -> int:
    r = subprocess.run(["git", "ls-files", "--", str(path.relative_to(root))], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:  # not a git repository: nothing counts as tracked
        return 0
    return len([l for l in r.stdout.splitlines() if l.strip()])


RUN_OUTPUTS = ("reports", "qmetry-version.json", "qmetry-cases.json", "app-under-test.log")


def local_plan(root: pathlib.Path, slug: str) -> dict:
    suite = root / "consolidated" / slug
    cands = [suite, *sorted((root / "test_runs").glob(f"{slug}-*"))]
    if suite.exists() and _tracked(root, suite):  # a committed suite stays; its untracked run outputs go
        cands += [suite / n for n in RUN_OUTPUTS]
    remove, kept = [], []
    for p in cands:
        if not p.exists():
            continue
        n = _tracked(root, p)
        (kept if n else remove).append((p, n))
    return {"remove": [p for p, _ in remove], "kept": kept}


# ------------------------------------------------------------------------------------------ jira
def is_harness_comment(text: str, slug: str) -> bool:
    first = text.strip().splitlines()[0] if text.strip() else ""
    return first.startswith(run_marker_prefix(slug)) or first == story_marker(slug)


def _labels(issue: dict) -> list[str]:
    return (issue.get("fields") or {}).get("labels") or []


def jira_plan(client, project: str, slug: str, protect: list[str], extra_keys: list[str],
              fingerprints: list[str] = ()) -> dict:
    issues = client.search(f'project = "{project}" AND labels = "{LIVE}" AND labels = "{suite_label(slug)}"',
                           fields="summary,labels")
    if fingerprints:  # --reset-bugs: the bugs runs filed, by fingerprint AND jira_bug.py's title format
        seen = {i["key"] for i in issues}
        fp = ", ".join(f'"{f}"' for f in fingerprints)
        # a seeded bug may carry a fingerprint too (so a run comments on it instead of duplicating it),
        # but only jira_bug.py titles a bug "[<slug>] <module>: <title>": that is what a run filed
        issues += [i for i in client.search(f'project = "{project}" AND labels in ({fp})', fields="summary,labels")
                   if i["key"] not in seen and ((i.get("fields") or {}).get("summary") or "").startswith(f"[{slug}] ")]
    delete, protected = [], []
    for i in issues:
        (protected if set(_labels(i)) & set(protect) else delete).append(i)
    doomed = {i["key"] for i in delete}
    # where comments can be: issues a text search finds, plus the suite's stories and ledger bugs
    try:
        found = [i["key"] for i in client.search(f'project = "{project}" AND comment ~ "{LIVE}"', fields="summary")]
    except Exception:
        found = []
    comments = []
    for key in sorted(set(found) | set(extra_keys)):
        if key in doomed:
            continue
        for c in client.comments(key):
            if is_harness_comment(jira_live.adf_text(c.get("body")), slug):
                comments.append((key, c["id"]))
    return {"issues": delete, "protected": protected, "comments": comments}


def suite_issue_keys(root: pathlib.Path, slug: str) -> list[str]:
    """Stories from requirements-map.json and bugs from the ledger: where harness comments live."""
    suite = root / "consolidated" / slug
    keys = set()
    rm = suite / "requirements-map.json"
    if rm.exists():
        keys |= {k for v in json.loads(rm.read_text()).values() for k in v}
    bl = suite / "bugs.json"
    if bl.exists():
        d = json.loads(bl.read_text())
        keys |= {b["jira"] for b in (d.get("bugs", []) if isinstance(d, dict) else d) if isinstance(b, dict) and b.get("jira")}
    return sorted(keys)


def ledger_fingerprints(root: pathlib.Path, slug: str) -> list[str]:
    """The fingerprint label jira_bug.py puts on every bug it files: gene2:<slug>:<bugkey>."""
    bl = root / "consolidated" / slug / "bugs.json"
    if not bl.exists():
        return []
    d = json.loads(bl.read_text())
    return sorted(f"gene2:{slug}:{b['bugkey']}" for b in (d.get("bugs", []) if isinstance(d, dict) else d)
                  if isinstance(b, dict) and b.get("bugkey"))


def prune_ledger(root: pathlib.Path, slug: str, deleted_keys: set[str]) -> int:
    """Drop ledger entries whose Jira issue was just deleted, so nothing links a bug that is gone and
    a bug filed again starts a new entry (with a new filed date)."""
    bl = root / "consolidated" / slug / "bugs.json"
    if not bl.exists() or not deleted_keys:
        return 0
    d = json.loads(bl.read_text())
    bugs = d.get("bugs", []) if isinstance(d, dict) else d
    keep = [b for b in bugs if not (isinstance(b, dict) and b.get("jira") in deleted_keys)]
    if len(keep) == len(bugs):
        return 0
    bl.write_text(json.dumps({"bugs": keep} if isinstance(d, dict) else keep, indent=2) + "\n")
    return len(bugs) - len(keep)


# ------------------------------------------------------------------------------------------ qmetry
def _label_names(case: dict) -> set[str]:
    out = set()
    for l in case.get("labels") or []:
        out.add(l.get("name") if isinstance(l, dict) else str(l))
    return out


def qmetry_plan(client, project: str, slug: str) -> dict:
    pid = client.project_id(project)
    if not pid:
        raise SystemExit(f"Jira project {project} is not QMetry-enabled (or not visible to this key)")
    cases = [c for c in client.cases_with_label(pid, LIVE) if {LIVE, slug} <= _label_names(c)]
    prefix = f"gene2 {slug} "
    cycles = [c for c in client.search_cycles(pid, prefix, max_results=500) if (c.get("summary") or "").startswith(prefix)]
    return {"pid": pid, "cases": cases, "cycles": cycles}


# ------------------------------------------------------------------------------------------ confirm
def tty_prompt(text: str) -> str | None:
    """Read the typed host from the terminal itself, never from stdin or a flag."""
    try:
        with open("/dev/tty", "r+") as tty:
            tty.write(text)
            tty.flush()
            return tty.readline().strip()
    except OSError:
        return None


def confirm_host(host: str, what: str, prompt=tty_prompt) -> bool:
    typed = prompt(f"\n{what}\nType the host to confirm ({host}): ")
    if typed is None:
        print("refused: no terminal to type the host on. Remote deletes are run by a person.", file=sys.stderr)
        return False
    if typed.lower() != host.lower():
        print(f"refused: {typed!r} is not {host!r}. Nothing was deleted.", file=sys.stderr)
        return False
    return True


# ------------------------------------------------------------------------------------------ main
def run(a, root: pathlib.Path, jira=None, qmetry=None, prompt=tty_prompt, project: str = "", host: str = "") -> int:
    rc = 0
    if getattr(a, "no_local", False):  # remote only: the suite, its runs and its repo are kept as they are
        lp = {"remove": [], "kept": []}
        print(f"LOCAL ({root}): kept as it is (--no-local)")
    else:
        lp = local_plan(root, a.slug)
        print(f"LOCAL ({root})")
    for p in lp["remove"]:
        print(f"  {'remove' if a.apply else 'would remove'}  {p.relative_to(root)}")
    for p, n in lp["kept"]:
        print(f"  kept          {p.relative_to(root)}  (tracked in git: {n} files; remove with a reviewed commit)")
    if not lp["remove"] and not lp["kept"] and not getattr(a, "no_local", False):
        print("  nothing for this slug")

    if a.qmetry:
        qp = qmetry_plan(qmetry, project, a.slug)
        print(f"\nQMETRY (project {project}): {len(qp['cases'])} test case(s), {len(qp['cycles'])} cycle(s)")
        for c in qp["cycles"]:
            print(f"  cycle {c.get('key', c.get('id'))}  {c.get('summary')}")
        for c in qp["cases"]:
            print(f"  case  {c.get('key', c.get('id'))}  {c.get('summary')}")
        if a.apply and (qp["cases"] or qp["cycles"]):
            if confirm_host(host, f"Delete {len(qp['cases'])} QMetry test case(s) and {len(qp['cycles'])} cycle(s) for {a.slug}?", prompt):
                for c in qp["cycles"]:
                    qmetry.delete_cycle(c["id"])
                for c in qp["cases"]:
                    qmetry.delete_case(c["id"])
                after = qmetry_plan(qmetry, project, a.slug)
                print(f"  QMetry after: {len(after['cases'])} case(s), {len(after['cycles'])} cycle(s) left")
            else:
                rc = 2

    if a.jira:
        fps = ledger_fingerprints(root, a.slug) if getattr(a, "reset_bugs", False) else []
        jp = jira_plan(jira, project, a.slug, a.protect, suite_issue_keys(root, a.slug), fps)
        print(f"\nJIRA (project {project}): {len(jp['issues'])} issue(s), {len(jp['comments'])} comment(s)"
              + (f", {len(jp['protected'])} protected (kept)" if jp["protected"] else ""))
        for i in jp["issues"]:
            print(f"  issue   {i['key']}  {(i.get('fields') or {}).get('summary', '')}")
        for key, cid in jp["comments"]:
            print(f"  comment {cid} on {key}")
        for i in jp["protected"]:
            print(f"  kept    {i['key']}  (carries a protected label)")
        if a.apply and (jp["issues"] or jp["comments"]):
            if confirm_host(host, f"Delete {len(jp['issues'])} Jira issue(s) and {len(jp['comments'])} comment(s) for {a.slug}?", prompt):
                for key, cid in jp["comments"]:
                    jira.delete_comment(key, cid)
                for i in jp["issues"]:
                    jira.delete_issue(i["key"])
                after = jira_plan(jira, project, a.slug, a.protect, suite_issue_keys(root, a.slug), fps)
                print(f"  Jira after: {len(after['issues'])} issue(s), {len(after['comments'])} comment(s) left")
                pruned = prune_ledger(root, a.slug, {i["key"] for i in jp["issues"]})
                if pruned:
                    print(f"  bug ledger: removed {pruned} entr{'y' if pruned == 1 else 'ies'} for the deleted issues "
                          f"(consolidated/{a.slug}/bugs.json - commit and push it so CI stops linking them)")
            else:
                rc = 2

    if a.jira and getattr(a, "reset_bugs", False) and fps:
        # a bug another clean already deleted (the harness copy and an app repo share one Jira) still
        # sits in this ledger: drop every ledger entry whose fingerprinted bug is gone from Jira
        alive = {i["key"] for i in jira.search(f'project = "{project}" AND labels in ({", ".join(f"{chr(34)}{f}{chr(34)}" for f in fps)})',
                                               fields="summary")}
        ledger = json.loads((root / "consolidated" / a.slug / "bugs.json").read_text()).get("bugs", [])
        gone = {b["jira"] for b in ledger if b.get("jira") and b.get("bugkey") and b["jira"] not in alive}
        if gone:
            if a.apply:
                n = prune_ledger(root, a.slug, gone)
                print(f"  bug ledger: removed {n} entr{'y' if n == 1 else 'ies'} for bugs no longer in Jira ({', '.join(sorted(gone))})")
            else:
                print(f"  bug ledger: would remove {len(gone)} entr{'y' if len(gone) == 1 else 'ies'} for bugs no longer in Jira "
                      f"({', '.join(sorted(gone))})")

    # local last: the remote plans read the suite's requirements map and bug ledger
    if a.apply:
        for p in lp["remove"]:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        print(f"\nlocal: removed {len(lp['remove'])} path(s), kept {len(lp['kept'])}")
    else:
        print("\nDRY RUN: nothing was deleted. Add --apply to delete (remote parts ask for the typed host).")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--jira", action="store_true")
    ap.add_argument("--qmetry", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--protect", action="append", default=[], help="never delete an issue with this label")
    ap.add_argument("--no-local", action="store_true",
                    help="remote only (QMetry, Jira): keep the local suite, its runs and outputs as they are")
    ap.add_argument("--reset-bugs", action="store_true",
                    help="with --jira: also delete the bugs runs filed that are in the suite's ledger (fingerprint "
                         "label + jira_bug.py's title format; seeded bugs are never taken) and clear those ledger entries")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()
    jira = qmetry = None
    project = host = ""
    if a.jira or a.qmetry:
        import _secrets
        project = _secrets.get("JIRA_PROJECT_KEY") or sys.exit("Set JIRA_PROJECT_KEY (keychain, credentials file, or env)")
        host = jira_live.host_of(_secrets.get("ATLASSIAN_BASE_URL"))
    if a.jira:
        jira = jira_live.JiraClient()
    if a.qmetry:
        import _secrets
        import qmetry_sync
        key = _secrets.get("QMETRY_API_KEY")
        if not key:
            print("missing QMETRY_API_KEY (see tools/qmetry_sync.py for how to save it)", file=sys.stderr)
            return 2
        qmetry = qmetry_sync.Client((_secrets.get("QMETRY_BASE_URL") or qmetry_sync.DEFAULT_BASE).rstrip("/"), key)
    return run(a, root, jira, qmetry, project=project, host=host)


if __name__ == "__main__":
    raise SystemExit(main())
