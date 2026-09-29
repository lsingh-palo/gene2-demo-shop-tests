#!/usr/bin/env python3
"""./gene2 <command>: every step of a run with one short command, the same from a terminal or any AI tool.

    ./gene2 preflight                    ready? anything left over? (read-only)
    ./gene2 clean [--apply]              what runs created in Jira + QMetry, and local leftovers; --apply
                                         deletes it after YOU type the Jira host (so no script or AI can)
    ./gene2 clean local                  local run leftovers only (no host to type)
    ./gene2 run <level> [v2] [headed]    run here: smoke | functional | extended | exploratory | full, on v1 (or v2);
                                         then QMetry sync (env test, next version) and the run report
    ./gene2 ci <level> [v2]              the same level in GitHub Actions: start, wait, fetch the report
    ./gene2 triage [run id]              evidence and a proposed class for every failure of a run
    ./gene2 accept [run id]              confirm every proposed product/known-bug row (after you agreed)
    ./gene2 bugs [run id] [--dry-run]    file the confirmed bugs in Jira now, attach them in QMetry, refresh
    ./gene2 promote <test> --module M --title "T"   add a new exploratory test to the suite manifest
                                         (scenario key, next TC id), so CI syncs it to QMetry as a new case
    ./gene2 report [run id] | status     one run's report | the table of every run
    ./gene2 allure [ci]                  open the Allure report in the browser (last local run | live CI)
    ./gene2 open ci|repo|actions         open the CI run / the repo / the Actions page
    ./gene2 tool <script> [args]         any script in tools/ with the suite's Python

Run reports, their junit, QMetry record and triage are kept in .gene2-local/runs/ (never committed):
<run id>.md per run and INDEX.md for all of them. Default level app: v1 (current release) on :8801;
v2 is the release candidate (it has regressions, so its failures are real bugs to file).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import run_report  # noqa: E402

SLUG = os.environ.get("GENE2_TARGET_SLUG") or next(p.name for p in sorted((ROOT / "consolidated").iterdir()) if p.is_dir())
SUITE = ROOT / "consolidated" / SLUG
RUNS = ROOT / ".gene2-local" / "runs"
PY = sys.executable
LEVELS = ("smoke", "functional", "extended", "exploratory", "full")


def sh(*args, check=False, env=None, cwd=ROOT) -> int:
    print("$ " + " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=cwd, env={**os.environ, **(env or {})}, check=check).returncode


def tool(script: str, *args, check=False) -> int:
    return sh(PY, TOOLS / script, *args, check=check)


def secret(name: str) -> str:
    try:
        import _secrets
        return _secrets.get(name)
    except SystemExit:
        return ""


def app_url() -> str:
    c = json.loads((SUITE / "config" / "suite-config.json").read_text())
    return c.get("website_url") or c.get("base_url")


def stop_own_app(port: int) -> None:
    """A demo app left running on the port would answer instead of the one this run starts (maybe
    the other version): stop it, but only if it is this repo's own demo-app/serve.py."""
    pids = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True, text=True).stdout.split()
    for pid in pids:
        cmd = subprocess.run(["ps", "-p", pid, "-o", "command="], capture_output=True, text=True).stdout
        if "demo-app/serve.py" in cmd:
            print(f"stopping the demo app already on :{port} (pid {pid})")
            os.kill(int(pid), signal.SIGTERM)
        else:
            sys.exit(f"port {port} is used by another program ({cmd.strip()[:80]}): stop it first")
    if pids:
        time.sleep(1)


def qmetry_host() -> str:
    return urllib.parse.urlparse(secret("QMETRY_BASE_URL") or "https://qtmcloud.qmetry.com").hostname


def latest_run() -> str:
    runs = sorted((p for p in RUNS.glob("*.json") if p.stem != "INDEX"), key=lambda p: p.stat().st_mtime)
    if not runs:
        sys.exit("no run yet: ./gene2 run smoke (or ./gene2 ci smoke)")
    return runs[-1].stem


def run_dir(run_id: str) -> pathlib.Path:
    d = RUNS / run_id
    if not (d / "junit.xml").exists():
        sys.exit(f"no junit for run {run_id} in {d}")
    return d


def report(run_id: str) -> None:
    """(Re)build the run report from what is in .gene2-local/runs/<run id>/ (local and CI runs)."""
    d = RUNS / run_id
    prev = run_report._json(RUNS / f"{run_id}.json", {})
    where = prev.get("where") or ("ci" if run_id.startswith("gh-") else "local")
    level = prev.get("level") or next((l for l in LEVELS if f"-{l}" in run_id), "")
    links = prev.get("links") or {}
    args = ["--slug", SLUG, "--junit", d / "junit.xml", "--run", run_id, "--level", level, "--where", where,
            "--out-dir", RUNS]
    if links.get("ci_run"):
        args += ["--ci-url", links["ci_run"]]
    if where == "local":
        args += ["--allure-cmd", "./gene2 allure"]
    tool("run_report.py", *args)


# ------------------------------------------------------------------------------------------ commands
def c_preflight(args):
    os.environ["GENE2_LOCAL_CLEAN_CMD"] = "./gene2 clean local"
    os.environ["GENE2_REMOTE_CLEAN_CMD"] = "./gene2 clean --apply"
    return tool("preflight.py", "--slug", SLUG, *args)


def c_clean(args):
    if "local" in args:  # local run leftovers only: nothing remote, no host to type
        return tool("clean.py", "--slug", SLUG, "--apply")
    apply = "--apply" in args
    if apply:
        print("You will be asked to type the Jira host before anything remote is deleted.")
    rc = tool("clean.py", "--slug", SLUG, "--jira", "--qmetry", "--reset-bugs", *(["--apply"] if apply else []))
    if apply:
        bl = SUITE / "bugs.json"
        if subprocess.run(["git", "diff", "--quiet", "--", str(bl)], cwd=ROOT).returncode:
            print(f"\nThe bug ledger changed (deleted bugs removed). Push it so CI stops linking them:\n"
                  f"  git add {bl.relative_to(ROOT)} && git commit -m 'Reset the bug ledger for a clean start' && git push")
    return rc


def c_run(args):
    level = next((a for a in args if a in LEVELS), None) or sys.exit(f"which level? {', '.join(LEVELS)}")
    variant = "v2" if "v2" in args else "v1"
    headed = "headed" in args
    url = app_url()
    port = urllib.parse.urlparse(url).port or 80
    stop_own_app(port)
    run_id = f"local-{level}{'-v2' if variant == 'v2' else ''}-{time.strftime('%Y%m%d-%H%M%S')}"
    marker = "not flaky" if level == "full" else level
    env = {"GENE2_APP_START": f"python3 {ROOT / 'demo-app' / 'serve.py'} --variant {variant} --port {port}",
           "GENE2_BASE_URL": url, "ATLASSIAN_BASE_URL": secret("ATLASSIAN_BASE_URL")}
    if headed:
        env["GENE2_WORKERS"] = "1"
    print(f"\n== {run_id}: {level} on app {variant} ({'headed' if headed else 'headless'}) ==")
    sh("bash", SUITE / "run.sh", "--ci", "-m", marker, "--clean-alluredir", *(["--headed"] if headed else []), env=env)
    d = RUNS / run_id
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(SUITE / "reports" / "junit.xml", d / "junit.xml")
    if secret("QMETRY_API_KEY"):
        tool("qmetry_sync.py", "results", "--slug", SLUG, "--junit", d / "junit.xml", "--run", run_id,
             "--apply", "--confirm-host", qmetry_host())
    else:
        print("QMetry sync skipped: no QMETRY_API_KEY")
    report(run_id)
    print(f"\nnext: ./gene2 allure (opens this run's report)" + ("; ./gene2 triage (there are failures)"
          if run_report._json(RUNS / f"{run_id}.json", {}).get("totals", {}).get("failed") else ""))
    return 0


def c_ci(args):
    level = next((a for a in args if a in LEVELS), None) or sys.exit(f"which level? {', '.join(LEVELS)}")
    extra = []
    if "v2" in args:
        port = urllib.parse.urlparse(app_url()).port or 80
        extra = ["--app-start", f"python3 demo-app/serve.py --variant v2 --port {port}"]
    rc = tool("ci.py", "trigger", "--level", level, "--wait", *extra)
    RUNS.mkdir(parents=True, exist_ok=True)
    tool("ci.py", "fetch", "--runs-dir", RUNS)
    print("\nnext: ./gene2 allure ci (opens the live report)" + ("; ./gene2 triage (there are failures)" if rc else ""))
    return 0


def c_triage(args):
    run_id = args[0] if args else latest_run()
    d = run_dir(run_id)
    reports = SUITE / "reports" if run_id.startswith("local-") else d
    tool("triage.py", "build", "--slug", SLUG, "--junit", d / "junit.xml", "--reports", reports, "--out", d, "--run", run_id)
    tool("triage.py", "show", "--file", d / "triage.json")
    print(f"\nnext: after you agree with the proposed classes, ./gene2 accept {run_id}; then ./gene2 bugs {run_id}")
    return 0


def c_accept(args):
    run_id = args[0] if args else latest_run()
    t = run_dir(run_id) / "triage.json"
    if not t.exists():
        sys.exit(f"triage this run first: ./gene2 triage {run_id}")
    rows = json.loads(t.read_text())["rows"]
    for r in rows:
        if r["proposed"] in ("product_bug", "known_bug") and not r["confirmed"]:
            tool("triage.py", "set", "--file", t, "--test", r["test"], "--class", r["proposed"],
                 "--reason", f"accepted as proposed: {r['proposed_reason']}")
        elif not r["confirmed"]:
            print(f"left for a person: {r['test']} proposed {r['proposed']} ({r['proposed_reason']})")
    return 0


def c_bugs(args):
    run_id = next((a for a in args if not a.startswith("--")), None) or latest_run()
    d = run_dir(run_id)
    t = d / "triage.json"
    if not t.exists():
        sys.exit(f"triage this run first: ./gene2 triage {run_id}")
    dry = "--dry-run" in args
    variant = "v2" if "-v2-" in run_id or run_id.endswith("-v2") else "v1"
    tool("jira_bug.py", "--slug", SLUG, "--from-triage", t, "--app-url", app_url(), "--variant", variant,
         *(["--dry-run"] if dry else []))
    if dry:
        return 0
    if secret("QMETRY_API_KEY"):  # same run id: finds its cycle and only attaches the new bugs
        tool("qmetry_sync.py", "results", "--slug", SLUG, "--junit", d / "junit.xml", "--run", run_id,
             "--apply", "--confirm-host", qmetry_host())
    report(run_id)
    bl = SUITE / "bugs.json"
    if subprocess.run(["git", "diff", "--quiet", "--", str(bl)], cwd=ROOT).returncode:
        print(f"\nThe bug ledger has the new bugs. Push it so CI links them on its next runs:\n"
              f"  git add {bl.relative_to(ROOT)} && git commit -m 'Record bugs filed in run {run_id}' && git push")
    return 0


def c_report(args):
    run_id = args[0] if args else latest_run()
    print((RUNS / f"{run_id}.md").read_text())
    print(f"file: {RUNS / (run_id + '.md')}")
    return 0


def c_status(args):
    idx = run_report.rebuild_index(RUNS) if RUNS.exists() else None
    print(idx.read_text() if idx else "no runs yet")
    print(f"file: {idx}" if idx else "")
    return 0


def _open(url: str) -> None:
    print(f"opening {url}")
    subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", url], check=False)


def c_allure(args):
    import ci
    if args and args[0] == "ci":
        _open(ci.repo(ROOT)[2])
        return 0
    results = SUITE / "reports" / "allure-results"
    out = SUITE / "reports" / "allure-report"
    if shutil.which("allure") is None:
        sys.exit("no allure CLI here (brew install allure); or open the live CI report: ./gene2 allure ci")
    sh("allure", "generate", results, "-o", out, "--clean", check=True)
    port = 8765
    if subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True, text=True).stdout.strip() == "":
        subprocess.Popen([PY, "-m", "http.server", str(port)], cwd=out, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        time.sleep(1)
    _open(f"http://localhost:{port}/")  # served, not file://: a file:// Allure report cannot load its data
    return 0


def c_open(args):
    import ci
    full, web, pages = ci.repo(ROOT)
    what = args[0] if args else "actions"
    if what == "ci":
        rep = run_report._json(RUNS / f"{latest_run()}.json", {}) if RUNS.exists() else {}
        _open((rep.get("links") or {}).get("ci_run") or f"{web}/actions")
    elif what == "repo":
        _open(web)
    else:
        _open(f"{web}/actions")
    return 0


STOP_WORDS = {"the", "a", "an", "with", "should", "and", "or", "of", "to", "on", "in", "for"}


def scenario_key(module: str, title: str, test_type: str) -> str:
    """The harness's scenario key (tools/suite_audit.py): the same scenario always gets the same key."""
    import hashlib
    words = [w for w in re.sub(r"[^a-z0-9\s]", " ", title.lower()).split() if w not in STOP_WORDS]
    return hashlib.sha1(f"{module.strip().lower()}|{' '.join(words)}|{test_type.strip().lower()}".encode()).hexdigest()[:12]


def c_promote(args):
    import argparse
    ap = argparse.ArgumentParser(prog="./gene2 promote")
    ap.add_argument("test")
    ap.add_argument("--module", required=True)
    ap.add_argument("--title", required=True, help="the expected behaviour, one line")
    ap.add_argument("--requirement", action="append", default=[])
    a = ap.parse_args(args)
    src = next((f for f in sorted((SUITE / "tests").glob("test_*.py")) if f"def {a.test}(" in f.read_text()), None)
    if not src:
        sys.exit(f"no test named {a.test} under {SUITE / 'tests'}: write it first")
    text = src.read_text()
    lines = text.splitlines()
    i = next(n for n, l in enumerate(lines) if l.lstrip().startswith(f"def {a.test}("))
    decorators = [l.strip() for l in lines[max(0, i - 4):i] if l.strip().startswith("@")]
    if "@pytest.mark.exploratory" not in decorators:
        sys.exit(f"mark it first: add @pytest.mark.exploratory above def {a.test}( in {src.name}")
    mpath = SUITE / "suite-manifest.json"
    manifest = json.loads(mpath.read_text())
    key = scenario_key(a.module, a.title, "exploratory")
    if any(s["key"] == key or s["test_name"] == a.test for s in manifest["scenarios"]):
        sys.exit(f"already in the manifest ({key}): nothing to add")
    tc = "TC%03d" % (max(int(s["tc_id"][2:]) for s in manifest["scenarios"]) + 1)
    today = time.strftime("%Y%m%d")
    manifest["scenarios"].append({
        "key": key, "tc_id": tc, "level": "exploratory", "module": a.module, "title": a.title, "type": "exploratory",
        "test_file": str(src.relative_to(SUITE)), "test_name": a.test, "app": "primary", "state": "active",
        "orphan": False, "source_run": f"exploratory-{today}", "last_verified_run": f"exploratory-{today}",
        "verified_count": 0, "trust": "provisional",
        "provenance": f"found in an exploratory session on {time.strftime('%Y-%m-%d')}",
        "plan_step": "", "plan_file": "", "requirement": a.requirement})
    manifest["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    mpath.write_text(json.dumps(manifest, indent=2) + "\n")
    j = i + 1
    tag = f"{tc} [key:{key}] [exploratory]"
    if j < len(lines) and lines[j].strip().startswith('"""'):
        if "[key:" not in lines[j]:
            lines[j] = lines[j].replace('"""', f'"""{tag} ', 1)
    else:
        indent = re.match(r"\s*", lines[i]).group(0) + "    "
        lines.insert(j, f'{indent}"""{tag} provenance: found in an exploratory session."""')
    src.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    print(f"added {tc} [{key}] {a.title} ({a.module}) <- {src.relative_to(ROOT)}::{a.test}")
    print("next: ./gene2 run exploratory v2 (see it run and sync as a new QMetry case), then commit the test and "
          "suite-manifest.json and push; ./gene2 ci full (or ci exploratory) shows it in CI")
    return 0


def c_tool(args):
    return tool(args[0] if args[0].endswith(".py") else f"{args[0]}.py", *args[1:])


def main(argv: list[str]) -> int:
    cmds = {"preflight": c_preflight, "clean": c_clean, "run": c_run, "ci": c_ci, "triage": c_triage,
            "accept": c_accept, "bugs": c_bugs, "promote": c_promote, "report": c_report, "status": c_status, "allure": c_allure,
            "open": c_open, "tool": c_tool}
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 0 if not argv or argv[0] in ("help", "-h", "--help") else 2
    RUNS.mkdir(parents=True, exist_ok=True)
    return cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
