#!/usr/bin/env python3
"""Drive the GitHub Actions pipeline from the terminal: start a level, wait for it, read it back.

    gene2 ci trigger --level smoke [--app-start "<command>"] [--ref <branch>] [--wait]
    gene2 ci wait    [--run <id>] [--timeout 1500]      # default: the newest run of this branch
    gene2 ci runs    [--n 5]                            # the last runs with level, event and result
    gene2 ci fetch   [--run <id>] [--out-dir <dir> | --runs-dir <dir>]   # the run's report, junit, QMetry record

`trigger` is a workflow_dispatch of .github/workflows/gene2-tests.yml on the pushed branch (so push
first: it runs what GitHub has, not your working tree). `wait` prints each job's result, the run
URL and, once the pages job has published it, the live Allure URL and the run report. `fetch`
downloads run-report.md/.json, junit.xml and qmetry-run.json from the live report site, which is
what lets a laptop re-run the QMetry sync for a CI run (to attach bugs filed after it finished).

Reads need no credentials on a public repo; `trigger` needs a token: GITHUB_TOKEN / GH_TOKEN, or
the one git already uses for github.com (git credential fill). The token is never printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_report  # noqa: E402  (web_remote, pages_url)

API = "https://api.github.com"
WORKFLOW = "gene2-tests.yml"


def repo(root: pathlib.Path) -> tuple[str, str, str]:
    """(owner/name, web URL, Pages URL) from the origin remote."""
    web = run_report.web_remote(run_report.git(root, "remote", "get-url", "origin"))
    m = re.match(r"https://github\.com/([^/]+/[^/]+)$", web)
    if not m:
        sys.exit(f"origin is not a github.com repository: {web or '(no origin)'}")
    return m.group(1), web, os.environ.get("GENE2_REPORT_URL") or run_report.pages_url(web)


def token(required: bool = False) -> str:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not t:
        r = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, text=True, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        t = next((l.split("=", 1)[1] for l in r.stdout.splitlines() if l.startswith("password=")), "")
    if required and not t:
        sys.exit("no GitHub token: set GITHUB_TOKEN, or sign git in to github.com once (a push asks for it)")
    return t


def call(method: str, path: str, body: dict | None = None, auth: bool = False):
    req = urllib.request.Request(path if path.startswith("http") else API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "gene2-ci"})
    t = token(required=auth)
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub {method} {path}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")


def fetch_text(url: str) -> str | None:
    try:
        req = urllib.request.Request(f"{url}{'&' if '?' in url else '?'}t={int(time.time())}",
                                     headers={"User-Agent": "gene2-ci", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode()
    except (urllib.error.URLError, TimeoutError):
        return None


def branch(root: pathlib.Path) -> str:
    return run_report.git(root, "rev-parse", "--abbrev-ref", "HEAD")


def runs(full: str, ref: str | None = None, n: int = 5, event: str | None = None) -> list[dict]:
    q = f"/repos/{full}/actions/workflows/{WORKFLOW}/runs?per_page={n}" + (f"&branch={ref}" if ref else "") \
        + (f"&event={event}" if event else "")
    return call("GET", q).get("workflow_runs", [])


def describe(r: dict) -> str:
    return (f"{r['id']}  {r['created_at'][:16].replace('T', ' ')}  {r['event']:<17} {r.get('display_title', '')[:44]:<44} "
            f"{r['status']:<11} {r.get('conclusion') or '-'}")


# ------------------------------------------------------------------------------------------ commands
def cmd_trigger(a, root) -> int:
    full, web, _ = repo(root)
    ref = a.ref or branch(root)
    local, remote = run_report.git(root, "rev-parse", "HEAD"), run_report.git(root, "rev-parse", f"origin/{ref}")
    if local and remote and local != remote:
        print(f"warning: your {ref} ({local[:7]}) is not what GitHub has ({remote[:7]}); CI runs GitHub's. Push first.")
    inputs = {"level": a.level}
    if a.app_start:
        inputs["app_start"] = a.app_start
    t0 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=10)
    call("POST", f"/repos/{full}/actions/workflows/{WORKFLOW}/dispatches", {"ref": ref, "inputs": inputs}, auth=True)
    print(f"started: {a.level} on {ref} ({', '.join(f'{k}={v}' for k, v in inputs.items())})")
    for _ in range(30):
        time.sleep(3)
        for r in runs(full, ref, 5, "workflow_dispatch"):
            if dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) >= t0:
                print(f"run {r['id']}: {r['html_url']}")
                if a.wait:
                    a.run = r["id"]
                    return cmd_wait(a, root)
                return 0
    print(f"dispatched, but the run did not show up yet: see {web}/actions")
    return 0


def cmd_wait(a, root) -> int:
    full, web, pages = repo(root)
    run_id = a.run or (runs(full, branch(root), 1) or [{}])[0].get("id")
    if not run_id:
        sys.exit("no run found for this branch")
    deadline = time.time() + a.timeout
    last = ""
    while True:
        r = call("GET", f"/repos/{full}/actions/runs/{run_id}")
        jobs = call("GET", f"/repos/{full}/actions/runs/{run_id}/jobs").get("jobs", [])
        line = ", ".join(f"{j['name']}: {j.get('conclusion') or j['status']}" for j in jobs) or r["status"]
        if line != last:
            print(f"[{time.strftime('%H:%M:%S')}] {line}")
            last = line
        if r["status"] == "completed":
            break
        if time.time() > deadline:
            print(f"still running after {a.timeout}s: {r['html_url']}")
            return 1
        time.sleep(15)
    print(f"\nrun {run_id}: {r.get('conclusion')}  {r['html_url']}")
    pages_job = next((j for j in jobs if j["name"] == "pages"), None)
    if pages_job and pages_job.get("conclusion") == "success":
        print(f"live Allure report: {pages}")
        for _ in range(12):  # the Pages CDN can lag the deploy by a minute
            txt = fetch_text(f"{pages}run-report.json")
            if txt and str(run_id) in (json.loads(txt).get("links") or {}).get("ci_run", ""):
                print("\n" + (fetch_text(f"{pages}run-report.md") or ""))
                break
            time.sleep(10)
        else:
            print("(the report site has not refreshed yet: open the live URL in a minute)")
    else:
        print("no live report for this run (a pull_request run, or the pages job did not succeed): "
              f"the zipped report is under Artifacts at {r['html_url']}")
    return 0 if r.get("conclusion") == "success" else 1


def cmd_runs(a, root) -> int:
    full, web, pages = repo(root)
    print(f"{web}/actions   live report: {pages}")
    for r in runs(full, None, a.n):
        print(describe(r))
    return 0


def cmd_fetch(a, root) -> int:
    full, _, pages = repo(root)
    rep = fetch_text(f"{pages}run-report.json")
    if not rep:
        sys.exit(f"no run report at {pages}run-report.json yet")
    d = json.loads(rep)
    if a.run and str(a.run) not in (d.get("links") or {}).get("ci_run", ""):
        sys.exit(f"the live site holds run {d.get('run_id')}, not {a.run} (it keeps only the latest published run)")
    if a.runs_dir:  # file it with the local run reports: <dir>/<run id>/ + <dir>/<run id>.md/.json + INDEX.md
        out = pathlib.Path(a.runs_dir) / d["run_id"]
    else:
        out = pathlib.Path(a.out_dir) if a.out_dir else root / "consolidated" / d["slug"] / "reports" / "ci" / d["run_id"]
    out.mkdir(parents=True, exist_ok=True)
    for name in ("run-report.md", "run-report.json", "junit.xml", "qmetry-run.json"):
        txt = fetch_text(f"{pages}{name}")
        if txt is not None:
            (out / name).write_text(txt)
            print(f"  {out / name}")
    if a.runs_dir:
        runs_dir = pathlib.Path(a.runs_dir)
        (runs_dir / f"{d['run_id']}.md").write_text((out / "run-report.md").read_text())
        (runs_dir / f"{d['run_id']}.json").write_text((out / "run-report.json").read_text())
        print(f"  {run_report.rebuild_index(runs_dir)}")
    print(f"run id {d['run_id']} (use it with qmetry_sync.py results --run {d['run_id']} --junit {out / 'junit.xml'})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trigger")
    t.add_argument("--level", required=True, choices=["smoke", "functional", "extended", "full"])
    t.add_argument("--app-start", default="", help="override GENE2_APP_START for this run (e.g. another app version)")
    t.add_argument("--ref")
    t.add_argument("--wait", action="store_true")
    t.add_argument("--timeout", type=int, default=1500)
    t.set_defaults(run=None)
    w = sub.add_parser("wait")
    w.add_argument("--run", type=int)
    w.add_argument("--timeout", type=int, default=1500)
    r = sub.add_parser("runs")
    r.add_argument("--n", type=int, default=5)
    f = sub.add_parser("fetch")
    f.add_argument("--run", type=int)
    f.add_argument("--out-dir")
    f.add_argument("--runs-dir", help="file the run with the local run reports (as run_report.py --out-dir does)")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()
    return {"trigger": cmd_trigger, "wait": cmd_wait, "runs": cmd_runs, "fetch": cmd_fetch}[a.cmd](a, root)


if __name__ == "__main__":
    raise SystemExit(main())
