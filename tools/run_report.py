#!/usr/bin/env python3
"""One report per run: verdict, every link, failed tests -> bugs, new test cases, what is pending.

Reads what the run already left behind - the JUnit file, the QMetry sync record next to it
(qmetry-run.json, written by qmetry_sync.py results), the suite manifest and the bug ledger - and
never calls a remote service, so it is the same locally and in CI and it cannot drift from what
actually happened.

    gene2 report --slug S --junit <junit.xml> [--run <id>] [--level smoke] [--where local|ci]
                 [--out-dir <dir>] [--report-url <live Allure URL>] [--ci-url <run URL>] [--copy-to <dir>]

Writes <out-dir>/<run id>.md and .json (default out-dir: consolidated/<slug>/reports/runs) and
rebuilds <out-dir>/INDEX.md from every report there. In GitHub Actions it also appends the report
to the run's summary page; --copy-to writes run-report.md/.json into a folder (the Allure site).

A failed test's bug is "filed now" when the ledger's filed time is at or after the run's start,
"pre-existing" when it is older, and "none yet" when there is no open bug (triage it).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


# ------------------------------------------------------------------------------------------ inputs
def read_junit(path: pathlib.Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    started = next((s.get("timestamp") for s in suites if s.get("timestamp")), None)
    tests = {}
    crash = ""
    for tc in root.iter("testcase"):
        name = re.sub(r"\[.*\]$", "", tc.get("name", ""))
        fail = next((c for c in tc if c.tag in ("failure", "error")), None)
        if name == "internal" and not tc.get("classname"):  # pytest/xdist crashed: not a test
            crash = ((fail.get("message") if fail is not None else "") or "pytest internal error").strip()[:160]
            continue
        skip = next((c for c in tc if c.tag == "skipped"), None)
        outcome = "failed" if fail is not None else ("skipped" if skip is not None else "passed")
        text = ((fail.get("message") or fail.text or "") if fail is not None else "").strip()
        msg = reason(text, fail.text or "" if fail is not None else "")
        tests[name] = {"outcome": outcome, "message": msg, "time": float(tc.get("time") or 0),
                       "classname": tc.get("classname", "")}
    return {"started": started, "tests": tests, "time": sum(float(s.get("time") or 0) for s in suites),
            "runner_crash": crash}


def _json(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def git(root: pathlib.Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def web_remote(url: str) -> str:
    """git@github.com:o/r.git or https://x@github.com/o/r.git -> https://github.com/o/r"""
    url = url.strip()
    m = re.match(r"git@([^:]+):(.+?)(\.git)?$", url)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    m = re.match(r"https?://(?:[^@/]+@)?([^/]+)/(.+?)(\.git)?$", url)
    return f"https://{m.group(1)}/{m.group(2)}" if m else url


def pages_url(remote_web: str) -> str:
    """The GitHub Pages address of a github.com repo (where the pipeline publishes Allure)."""
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", remote_web)
    return f"https://{m.group(1).lower()}.github.io/{m.group(2)}/" if m else ""


def _parse_time(s: str | None):
    if not s:
        return None
    try:
        t = dt.datetime.fromisoformat(s)
        return t if t.tzinfo else t.astimezone()
    except ValueError:
        return None


# ------------------------------------------------------------------------------------------ model
def build(slug: str, junit: pathlib.Path, root: pathlib.Path, run_id: str = "", level: str = "", where: str = "",
          qmetry_run: pathlib.Path | None = None, report_url: str = "", ci_url: str = "", jira_base: str = "",
          previous: dict | None = None, allure_results: pathlib.Path | None = None, allure_cmd: str = "") -> dict:
    suite = root / "consolidated" / slug
    j = read_junit(junit)
    manifest = {s["test_name"]: s for s in _json(suite / "suite-manifest.json", {}).get("scenarios", [])}
    qrun = _json(qmetry_run or junit.parent / "qmetry-run.json", {})
    tc_keys = {**_json(suite / "qmetry-cases.json", {}), **(qrun.get("tc_keys") or {})}
    ledger, by_title = {}, {}
    for b in _json(suite / "bugs.json", {"bugs": []}).get("bugs", []):
        if b.get("jira") and b.get("status") == "open":
            if b.get("test"):
                ledger[b["test"].split("::")[-1]] = b
            elif b.get("title"):  # filed from a triage before the test was named: its title is the scenario's
                by_title[b["title"].strip().lower()] = b
    started = _parse_time(j["started"])
    import triage  # is_bug_marked: the same known-bug rule the triage uses

    rows, modules = [], {}
    for name, t in sorted(j["tests"].items()):
        s = manifest.get(name, {})
        mod = s.get("module") or t["classname"].split(".")[-1].replace("test_", "") or "-"
        m = modules.setdefault(mod, {"passed": 0, "failed": 0, "skipped": 0})
        m[t["outcome"]] += 1
        if t["outcome"] != "failed":
            continue
        bug = ledger.get(name) or by_title.get((s.get("title") or "").strip().lower())
        filed = _parse_time((bug or {}).get("filed"))
        when = ("none yet" if not bug else
                "filed now" if (filed and started and filed >= started) else
                f"pre-existing ({(bug.get('filed') or '')[:10]})")
        rows.append({"test": name, "tc_id": s.get("tc_id", "-"), "title": s.get("title", ""), "module": mod,
                     "qmetry_case": tc_keys.get(s.get("tc_id", ""), ""), "message": t["message"],
                     "known_bug": bool(s) and triage.is_bug_marked(suite, s.get("test_file", ""), name),
                     "bug": (bug or {}).get("jira", ""), "bug_title": (bug or {}).get("title", ""), "filed": when})

    new_cases = [{"tc_id": tc, "title": next((s.get("title", "") for s in manifest.values() if s.get("tc_id") == tc), ""),
                  "qmetry_key": tc_keys.get(tc, "")} for tc in qrun.get("new_cases", [])]
    new_tests = sorted(set(j["tests"]) - set((previous or {}).get("tests", []))) if previous else []

    remote = web_remote(git(root, "remote", "get-url", "origin"))
    branch, commit = git(root, "rev-parse", "--abbrev-ref", "HEAD"), git(root, "rev-parse", "--short", "HEAD")
    if os.environ.get("GITHUB_REPOSITORY"):  # in a CI container git may not read the checkout: ask the runner
        remote = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ['GITHUB_REPOSITORY']}"
        branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or branch
        commit = (os.environ.get("GITHUB_SHA") or commit)[:7]
    totals = {k: sum(1 for t in j["tests"].values() if t["outcome"] == k) for k in ("passed", "failed", "skipped")}
    unexpected = [r for r in rows if not r["known_bug"]]
    return {
        "slug": slug, "run_id": run_id or junit.parent.name, "level": level, "where": where or ("ci" if ci_url else "local"),
        "started": j["started"], "duration_s": round(j["time"], 1), "totals": {**totals, "total": len(j["tests"])},
        "verdict": "FAIL" if unexpected or j["runner_crash"] else "PASS",
        "runner_crash": j["runner_crash"],
        "known_bugs_failed": sum(1 for r in rows if r["known_bug"]),
        "modules": modules, "failed": rows, "new_cases": new_cases, "new_tests": new_tests,
        "tests": sorted(j["tests"]),
        "bugs": sorted({r["bug"] for r in rows if r["bug"]}),
        "bugs_filed_now": sorted({r["bug"] for r in rows if r["filed"] == "filed now"}),
        "qmetry": {k: qrun.get(k) for k in ("cycle_key", "cycle_summary", "env", "version", "host", "applied",
                                              "cycle_created", "defects")} if qrun else {},
        "links": {"ci_run": ci_url, "allure_live": report_url, "remote_repo": remote,
                  "branch": branch, "commit": commit,
                  "local_repo": "" if (where == "ci" or ci_url) else str(root), "jira_base": jira_base.rstrip("/"),
                  "allure_local": allure_cmd or f"allure serve {allure_results or suite / 'reports' / 'allure-results'}",
                  "jira_project_bugs": (f"{jira_base.rstrip('/')}/issues/?jql=labels%20%3D%20%22gene2-suite-{slug}%22"
                                        if jira_base else "")},
    }


def reason(message: str, full: str = "") -> str:
    """One line a person can act on: "expected to have text '$3.40', actual $4.25"."""
    first = (message.strip().splitlines() or [""])[0]
    first = re.sub(r"^(AssertionError|Error|Exception):\s*", "", first)
    first = re.sub(r"^Locator expected", "expected", first)
    actual = re.search(r"Actual value:[ \t]*([^\n]*)", full or message)
    value = actual.group(1).strip() if actual else ""
    if value and "actual" not in first.lower():
        first += ", not found" if value == "None" else f", actual {value}"
    return first[:160]


def failure_lines(r: dict) -> list[str]:
    """The same failure and bug block on every end screen (a local run, a pipeline run, a build):
    each failure with its reason and its bug, then the bugs linked to the suite."""
    failed = r.get("failed") or []
    bugs = r.get("bugs") or []
    out = []
    if r.get("runner_crash"):
        out.append("  RUNNER     pytest crashed mid-run, so some tests have no result: rerun (not a product bug)")
    if failed:
        known = sum(1 for x in failed if x.get("known_bug"))
        open_bug = sum(1 for x in failed if not x.get("known_bug") and x.get("bug"))
        new = len(failed) - known - open_bug
        parts = [f"{new} new (no bug yet)" if new else "", f"{open_bug} with an open bug" if open_bug else "",
                 f"{known} known bug{'' if known == 1 else 's'} (failing as designed)" if known else ""]
        out.append(f"  failures   {len(failed)}: " + ", ".join(x for x in parts if x))
        w = max(len(x["test"]) for x in failed)
        # new first, then with an open bug, then known bugs; the unfiled ones last, next to their hint
        rank = lambda x: (x.get("known_bug", False), bool(x.get("bug")) != x.get("known_bug", False), x["test"])  # noqa: E731
        for x in sorted(failed, key=rank):
            tag = x.get("bug") or ("unfiled" if x.get("known_bug") else "NEW")
            msg = x.get("message") or "(no message)"
            out.append(f"    {tag:<9} {x['test']:<{w}}  {msg if len(msg) <= 90 else msg[:87] + '...'}")
        if any(x.get("known_bug") and not x.get("bug") for x in failed):
            out.append("             unfiled = a known bug with no open Jira bug yet: file it (gene2 triage)")
    link = (r.get("links") or {}).get("jira_project_bugs", "")
    out.append(f"  bugs       {', '.join(bugs) + ' linked' if bugs else 'none linked'}"
               + (f"  ({len(r.get('bugs_filed_now') or [])} filed now)" if r.get("bugs_filed_now") else "")
               + (f"  {link}" if link else ""))
    return out


def pending(r: dict) -> list[str]:
    out = []
    no_bug = [x for x in r["failed"] if not x["bug"]]
    if no_bug:
        out.append(f"{len(no_bug)} failed test(s) have no bug yet: triage them (build, confirm each row), then file "
                   f"the confirmed ones with jira_bug.py --from-triage and re-run the QMetry sync for run "
                   f"{r['run_id']} so the new bugs attach to its executions.")
    if r["failed"] and r["qmetry"] and set(r["qmetry"].get("defects") or {}) != {x["tc_id"] for x in r["failed"] if x["bug"]}:
        out.append("Some failed executions in QMetry do not carry their bug yet: re-run the QMetry sync for this run id.")
    if not r["qmetry"]:
        out.append("Not synced to QMetry: run qmetry_sync.py results for this junit (dry run, then --apply).")
    elif not r["qmetry"].get("applied"):
        out.append("QMetry sync was a dry run: re-run it with --apply --confirm-host to create the cycle.")
    fixed = [x for x in r["failed"] if x["known_bug"] and not x["bug"]]
    if fixed:
        out.append("Known-bug tests failed with no open bug in the ledger: file them now (they are real, reproducible).")
    return out


# ------------------------------------------------------------------------------------------ render
def _link(url: str, text: str) -> str:
    return f"[{text}]({url})" if url else text


def render(r: dict) -> str:
    L, t, q = r["links"], r["totals"], r["qmetry"]
    jb = L["jira_base"]
    bug = (lambda k: _link(f"{jb}/browse/{k}" if jb else "", k)) if jb else (lambda k: k)
    known = f"; {r['known_bugs_failed']} known bug(s) failed as designed" if r["known_bugs_failed"] else ""
    out = [f"# Gen-e2 run `{r['run_id']}`: {r['level'] or 'suite'} ({r['where']})", "",
           f"**{r['verdict']}**: {t['passed']} passed, {t['failed']} failed, {t['skipped']} skipped of {t['total']}"
           f" in {r['duration_s']} s{known}. Started {r['started'] or '-'}.", ""]
    out += ["## Links", "", "| What | Where |", "|---|---|"]
    if L["ci_run"]:
        out.append(f"| CI run | {L['ci_run']} |")
    if L["allure_live"]:
        label = "this run" if r["where"] == "ci" else "the latest CI run, not this local one"
        out.append(f"| Allure report, live ({label}) | {L['allure_live']} |")
    if r["where"] != "ci":
        out.append(f"| Allure report, this run | `{L['allure_local']}` (opens it in the browser) |")
    if q:
        out.append(f"| QMetry cycle | **{q.get('cycle_key') or '(dry run: not created)'}** `{q.get('cycle_summary')}`, "
                   f"Environment `{q.get('env')}`, Version `{q.get('version')}` (Jira > Apps > QMetry > Test Cycles, "
                   f"search the key; {q.get('host') or 'offline'}) |")
    if r["bugs"]:
        out.append(f"| Jira bugs linked to failures | {', '.join(bug(k) for k in r['bugs'])} |")
    if L.get("jira_project_bugs"):
        out.append(f"| Every bug this suite's runs filed | {L['jira_project_bugs']} |")
    if L.get("local_repo"):
        out.append(f"| Local repo | `{L['local_repo']}` |")
    if L["remote_repo"]:
        out.append(f"| Remote repo | {L['remote_repo']} (branch `{L['branch']}`, commit `{L['commit']}`) |")
    out.append("")
    out += ["## Results by module", "", "| Module | Passed | Failed | Skipped |", "|---|--:|--:|--:|"]
    out += [f"| {m} | {v['passed']} | {v['failed']} | {v['skipped']} |" for m, v in sorted(r["modules"].items())]
    out.append("")
    out += ["## Failed tests and their bugs", ""]
    if r["failed"]:
        out += ["| Test | TC id | QMetry case | Failure | Jira bug | Bug status |", "|---|---|---|---|---|---|"]
        for x in r["failed"]:
            kind = " (known bug)" if x["known_bug"] else ""
            msg = x["message"].replace("|", "\\|") or "-"
            out.append(f"| `{x['test']}`{kind} | {x['tc_id']} | {x['qmetry_case'] or '-'} | {msg} | "
                       f"{bug(x['bug']) if x['bug'] else '-'} | {x['filed']} |")
        out.append("")
        out.append(f"Bugs linked: {len(r['bugs'])} (filed during this run: {len(r['bugs_filed_now'])}).")
    else:
        out.append("No test failed.")
    out.append("")
    out += ["## New test cases", ""]
    if r["new_cases"]:
        out += ["| TC id | Title | QMetry key |", "|---|---|---|"]
        out += [f"| {c['tc_id']} | {c['title']} | {c['qmetry_key'] or '-'} |" for c in r["new_cases"]]
    else:
        out.append("None created in QMetry by this run" + (" (sync not run)." if not q else "."))
    if r["new_tests"]:
        out += ["", "Tests in this run that were not in the previous report: " + ", ".join(f"`{n}`" for n in r["new_tests"])]
    out.append("")
    out += ["## Pending", ""]
    out += [f"- {p}" for p in pending(r)] or [
        "- Nothing: every failure has its bug and QMetry is in sync." if r["failed"] else "- Nothing: all green, QMetry is in sync."]
    out.append("")
    return "\n".join(out)


def rebuild_index(out_dir: pathlib.Path) -> pathlib.Path:
    reports = []
    for p in out_dir.glob("*.json"):
        d = _json(p, None)
        if isinstance(d, dict) and d.get("run_id") and "totals" in d:
            reports.append(d)
    reports.sort(key=lambda d: d.get("started") or "")
    lines = ["# Run reports", "", "| Started | Run | Level | Where | Version | Passed | Failed | QMetry cycle | Bugs (filed now) | Report |",
             "|---|---|---|---|---|--:|--:|---|---|---|"]
    for d in reports:
        q = d.get("qmetry") or {}
        lines.append(f"| {(d.get('started') or '')[:16]} | {d['run_id']} | {d.get('level') or '-'} | {d.get('where')} | "
                     f"{q.get('version') or '-'} | {d['totals']['passed']} | {d['totals']['failed']} | "
                     f"{q.get('cycle_key') or '-'} | {len(d.get('bugs', []))} ({len(d.get('bugs_filed_now', []))}) | "
                     f"[{d['run_id']}.md]({d['run_id']}.md) |")
    idx = out_dir / "INDEX.md"
    idx.write_text("\n".join(lines) + "\n")
    return idx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--junit", required=True)
    ap.add_argument("--run", default="")
    ap.add_argument("--level", default="")
    ap.add_argument("--where", choices=["local", "ci"])
    ap.add_argument("--qmetry-run")
    ap.add_argument("--out-dir")
    ap.add_argument("--report-url", default=os.environ.get("GENE2_REPORT_URL", ""))
    ap.add_argument("--ci-url", default="")
    ap.add_argument("--copy-to")
    ap.add_argument("--allure-results", help="where this run's allure-results are (local runs)")
    ap.add_argument("--allure-cmd", default="", help="the command that opens this run's report, shown as is")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()
    junit = pathlib.Path(a.junit)
    if not junit.exists():
        print(f"no junit file at {junit}: run the suite first", file=sys.stderr)
        return 2
    ci_url = a.ci_url
    if not ci_url and os.environ.get("GITHUB_ACTIONS") == "true":
        ci_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    elif not ci_url and os.environ.get("CI_JOB_URL"):
        ci_url = os.environ["CI_JOB_URL"]
    report_url = a.report_url or pages_url(web_remote(git(root, "remote", "get-url", "origin")))
    try:
        import _secrets
        jira_base = _secrets.get("ATLASSIAN_BASE_URL")
    except Exception:
        jira_base = os.environ.get("ATLASSIAN_BASE_URL", "")
    out_dir = pathlib.Path(a.out_dir) if a.out_dir else root / "consolidated" / a.slug / "reports" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = a.run or junit.parent.name
    prev = sorted((d for d in (_json(p, None) for p in out_dir.glob("*.json"))
                   if isinstance(d, dict) and d.get("run_id") not in (None, run_id) and d.get("level") == a.level),
                  key=lambda d: d.get("started") or "")
    r = build(a.slug, junit, root, run_id, a.level, a.where or "", pathlib.Path(a.qmetry_run) if a.qmetry_run else None,
              report_url, ci_url, jira_base, prev[-1] if prev else None,
              pathlib.Path(a.allure_results) if a.allure_results else None, a.allure_cmd)
    md = render(r)
    (out_dir / f"{r['run_id']}.md").write_text(md)
    (out_dir / f"{r['run_id']}.json").write_text(json.dumps(r, indent=2) + "\n")
    idx = rebuild_index(out_dir)
    if a.copy_to:
        dest = pathlib.Path(a.copy_to)
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(out_dir / f"{r['run_id']}.md", dest / "run-report.md")
        shutil.copy(out_dir / f"{r['run_id']}.json", dest / "run-report.json")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(md + "\n")
    print(md)
    print(f"report: {out_dir / (r['run_id'] + '.md')}\nindex:  {idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
