#!/usr/bin/env python3
"""One harness comment per Jira story: its linked tests and their latest results, updated in place.

For every story in the suite's requirements-map.json, the comment lists the tests that cover it
(TC id, title, QMetry key when synced), each test's result in the given run, and the open bug of a
failing test. It is ONE comment per story, found by its first line
`[gene2-live <slug> story-status]` and edited in place on the next run, never a new comment per run.
`gene2 clean --jira` removes it.

    gene2 stories --slug S --junit <junit.xml> [--run <run id>] [--app-url URL]         # dry run
    gene2 stories --slug S --junit <junit.xml> --apply --confirm-host <your-site>.atlassian.net

Safety: dry run by default; --apply needs --confirm-host equal to the ATLASSIAN_BASE_URL host.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jira_live  # noqa: E402
from qmetry_sync import junit_outcomes  # noqa: E402

LIVE = "gene2-live"
WORD = {"passed": "passed", "failed": "FAILED", "skipped": "not run"}


def marker(slug: str) -> str:
    return f"[{LIVE} {slug} story-status]"


def story_tests(slug: str, root: pathlib.Path) -> dict[str, list[dict]]:
    suite = root / "consolidated" / slug
    req_map = json.loads((suite / "requirements-map.json").read_text())
    scen = {s["key"]: s for s in json.loads((suite / "suite-manifest.json").read_text())["scenarios"] if not s.get("orphan")}
    out: dict[str, list[dict]] = {}
    for key, stories in req_map.items():
        if key in scen:
            for st in stories:
                out.setdefault(st, []).append(scen[key])
    for st in out:
        out[st].sort(key=lambda s: s.get("tc_id", ""))
    return out


def bugs_by_test(slug: str, root: pathlib.Path) -> dict[str, str]:
    p = root / "consolidated" / slug / "bugs.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    rows = d.get("bugs", []) if isinstance(d, dict) else d
    return {r["test"].split("::")[-1]: r.get("jira", "") for r in rows
            if isinstance(r, dict) and r.get("test") and r.get("status") == "open" and r.get("jira")}


def render(slug: str, story: str, tests: list[dict], outcomes: dict[str, str], run: str, app_url: str,
           bugs: dict[str, str], qmetry: dict[str, str]) -> str:
    counted = [outcomes.get(t["test_name"]) for t in tests]
    n_pass, n_fail = counted.count("passed"), counted.count("failed")
    lines = [marker(slug),
             f"Gen-e2 automated tests for {story} (suite {slug}). This comment is updated in place by each run.",
             f"Latest run {run} on {app_url or os.environ.get('GENE2_BASE_URL', '(app not given)')}: "
             f"{len(tests)} test(s), {n_pass} passed, {n_fail} failed"
             + (f", {len(tests) - n_pass - n_fail} not in this run" if len(tests) - n_pass - n_fail else "") + "."]
    for t in tests:
        res = WORD.get(outcomes.get(t["test_name"], ""), "not in this run")
        extra = []
        if qmetry.get(t.get("tc_id", "")):
            extra.append(f"QMetry {qmetry[t['tc_id']]}")
        if res == "FAILED" and bugs.get(t["test_name"]):
            extra.append(f"bug {bugs[t['test_name']]}")
        lines.append(f"- {t.get('tc_id', '')} {t['title']}: {res}" + (f" ({', '.join(extra)})" if extra else ""))
    lines.append(f"QMetry cycle: gene2 {slug} {run}")
    return "\n".join(lines)


def sync(client, slug: str, texts: dict[str, str], apply: bool, out=print) -> dict:
    counts = {"create": 0, "update": 0, "unchanged": 0}
    for story, text in texts.items():
        mine = [c for c in (client.comments(story) if client else [])
                if jira_live.adf_text(c.get("body")).startswith(marker(slug))]
        if not mine:
            counts["create"] += 1
            out(f"{'' if apply else 'would '}create  comment on {story}")
            if apply:
                client.add_comment(story, text)
            continue
        keep, extra = mine[0], mine[1:]
        if jira_live.adf_text(keep.get("body")).strip() == text.strip():
            counts["unchanged"] += 1
            out(f"unchanged        {story}")
        else:
            counts["update"] += 1
            out(f"{'' if apply else 'would '}update  comment {keep['id']} on {story}")
            if apply:
                client.update_comment(story, keep["id"], text)
        for c in extra:  # at most one harness comment per story
            out(f"{'' if apply else 'would '}delete  duplicate harness comment {c['id']} on {story}")
            if apply:
                client.delete_comment(story, c["id"])
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--junit", required=True)
    ap.add_argument("--run", help="default: the junit file's run folder name")
    ap.add_argument("--app-url", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-host")
    ap.add_argument("--offline", action="store_true", help="dry run without reading Jira")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()
    junit = pathlib.Path(a.junit)
    run = a.run or junit.resolve().parents[1].name
    qpath = root / "consolidated" / a.slug / "qmetry-cases.json"
    qmetry = json.loads(qpath.read_text()) if qpath.exists() else {}
    outcomes = junit_outcomes(junit)
    by_story = story_tests(a.slug, root)
    bugs = bugs_by_test(a.slug, root)
    texts = {st: render(a.slug, st, tests, outcomes, run, a.app_url, bugs, qmetry) for st, tests in sorted(by_story.items())}
    if a.offline:
        if a.apply:
            sys.exit("--apply cannot be --offline")
        print(f"DRY RUN (offline): {len(texts)} stories; nothing is read or written\n")
        for st, tx in texts.items():
            print(f"--- {st}\n{tx}\n")
        return 0
    client = jira_live.JiraClient()
    host = jira_live.host_of(client.base)
    if a.apply and (a.confirm_host or "").strip().lower() != host:
        print(f"refused: --apply needs --confirm-host {host} (the configured Jira site). Nothing was called.", file=sys.stderr)
        return 2
    print(f"Jira site: {host}   {len(texts)} stories   {'APPLY' if a.apply else 'DRY RUN: reading only'}   "
          f"{datetime.datetime.now():%Y-%m-%d %H:%M}")
    counts = sync(client, a.slug, texts, a.apply)
    print(f"\nsummary: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
