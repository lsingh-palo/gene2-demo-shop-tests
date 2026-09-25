#!/usr/bin/env python3
"""A stakeholder report from a run's allure-results: HTML, then PDF through Playwright page.pdf().

For people who will not open Allure: one PDF with the verdict, pass / fail by module and by
requirement, each failure with its evidence (expected vs actual, the screenshot) and its Jira link,
known bugs listed apart, the build and environment the run used, and the suite's scorecard.

    gene2 pdf --slug S                                   # consolidated/S/reports/allure-results
    gene2 pdf --slug S --results allure-results --out report.pdf \\
              [--app-url URL] [--variant NAME] [--html-only]

Reads (all optional except the results): the suite manifest (titles, TC ids), the bug ledger
(bugs.json: the Jira key of a known bug's reproduction), SUITE.md's "Harness intelligence" block
(the scorecard, committed with the suite so a CI job has it). The environment comes from the
arguments, then GENE2_BASE_URL / GENE2_APP_VARIANT / GENE2_BROWSERS, the CI run id
(GITHUB_RUN_ID, CI_PIPELINE_ID, BUILD_ID), git (commit, branch) and the harness VERSION.

Latest run only: a local allure-results folder can hold several runs (CI cleans it each run). The
results are split into sessions wherever two consecutive test starts are more than 10 minutes
apart; the report covers the last session, and for a retried test only its last attempt counts.
"""
from __future__ import annotations

import argparse
import base64
import collections
import datetime
import html
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from triage import expected_actual  # noqa: E402

SESSION_GAP_MS = 10 * 60 * 1000
FAILED = ("failed", "broken")


def harness_version() -> str:
    for f in (HERE.parent / "VERSION", HERE.parent / ".claude-plugin" / "plugin.json"):
        if f.exists():
            t = f.read_text().strip()
            return json.loads(t).get("version", "?") if f.suffix == ".json" else t
    return "?"


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def _labels(r: dict, name: str) -> list[str]:
    return [l["value"] for l in r.get("labels", []) if l.get("name") == name]


def load_results(folder: pathlib.Path) -> list[dict]:
    """The last session's results, one per test (its last attempt)."""
    rs = [json.loads(p.read_text()) for p in sorted(folder.glob("*-result.json"))]
    if not rs:
        return []
    rs.sort(key=lambda r: r.get("start", 0))
    session = [rs[-1]]
    for prev, cur in zip(reversed(rs[:-1]), reversed(rs)):
        if cur.get("start", 0) - prev.get("start", 0) > SESSION_GAP_MS:
            break
        session.append(prev)
    last: dict[str, dict] = {}
    for r in sorted(session, key=lambda r: r.get("stop", 0)):
        key = r.get("historyId") or r.get("fullName") or r.get("name")
        last[key] = r
    return list(last.values())


def load_suite(root: pathlib.Path, slug: str) -> dict:
    suite = root / "consolidated" / slug
    out = {"titles": {}, "ledger": {}, "scorecard": []}
    mf = suite / "suite-manifest.json"
    if mf.exists():
        for s in json.loads(mf.read_text()).get("scenarios", []):
            out["titles"][s["test_name"]] = (s.get("tc_id", ""), s.get("title", ""), s.get("module", ""))
    bl = suite / "bugs.json"
    if bl.exists():
        d = json.loads(bl.read_text())
        for b in (d.get("bugs", []) if isinstance(d, dict) else d):
            if isinstance(b, dict) and b.get("test") and b.get("jira"):
                out["ledger"][b["test"].split("::")[-1]] = b["jira"]
    sm = suite / "SUITE.md"
    if sm.exists():
        m = re.search(r"<!-- gene2:intelligence:start -->(.*?)<!-- gene2:intelligence:end -->", sm.read_text(), re.S)
        if m:
            for line in m.group(1).splitlines():
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if line.startswith("|") and len(cells) == 3 and cells[0] not in ("Metric",) and not set(cells[0]) <= set("-"):
                    out["scorecard"].append(cells)
    return out


def summarise(results: list[dict], suite: dict, jira_base: str = "") -> dict:
    tests = []
    for r in results:
        name = r.get("name", "")
        tc, title, module = suite["titles"].get(name, ("", "", ""))
        tc = tc or next(iter(_labels(r, "tc_id")), "")
        module = module or next(iter(_labels(r, "feature")), "") or "(no module)"
        known = "known-bug" in _labels(r, "tag")
        links = [(l.get("name") or l.get("url"), l.get("url")) for l in r.get("links", []) if l.get("type") == "issue"]
        if known and not links and name in suite["ledger"]:
            key = suite["ledger"][name]
            links = [(key, f"{jira_base}/browse/{key}" if jira_base else "")]
        msg = (r.get("statusDetails") or {}).get("message", "")
        exp, act = expected_actual(msg) if r.get("status") in FAILED else ("", "")
        shot = next((a["source"] for a in r.get("attachments", []) if a.get("type") == "image/png"), None)
        params = {p.get("name"): p.get("value") for p in r.get("parameters", [])}
        tests.append({"name": name, "tc": tc, "title": title or name, "module": module,
                      "requirements": _labels(r, "requirement") or ["(none)"], "status": r.get("status", "unknown"),
                      "known": known, "links": links, "message": msg.split("Call log:")[0].strip(),
                      "expected": exp, "actual": act, "screenshot": shot,
                      "browser": next(iter(_labels(r, "browser")), "") or params.get("browser_name") or "",
                      "start": r.get("start", 0), "stop": r.get("stop", 0)})
    tests.sort(key=lambda t: (t["module"], t["tc"], t["name"]))
    return {"tests": tests}


def environment(tests: list[dict], app_url: str, variant: str) -> list[tuple[str, str]]:
    ci = next((f"{k}={os.environ[k]}" for k in ("GITHUB_RUN_ID", "CI_PIPELINE_ID", "BUILD_ID") if os.environ.get(k)), "local")
    browsers = sorted({t["browser"] for t in tests if t["browser"]}) or \
        [b for b in os.environ.get("GENE2_BROWSERS", "").split() if b] or ["(not recorded)"]
    start = min((t["start"] for t in tests if t["start"]), default=0)
    stop = max((t["stop"] for t in tests if t["stop"]), default=0)
    fmt = lambda ms: datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")  # noqa: E731
    variant = variant or os.environ.get("GENE2_APP_VARIANT", "")
    return [("App under test", (app_url or os.environ.get("GENE2_BASE_URL", "(not given)")) + (f"  (variant {variant})" if variant else "")),
            ("Browsers", ", ".join(browsers)),
            ("Run", f"{fmt(start)} to {fmt(stop)}" if start else "(no timing)"),
            ("CI run", ci),
            ("Commit / branch", f"{_git('rev-parse', '--short', 'HEAD') or '?'} / {_git('rev-parse', '--abbrev-ref', 'HEAD') or '?'}"),
            ("Harness", f"Gen-e2 {harness_version()}"),
            ("Report generated", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))]


def _count(tests: list[dict], key) -> list[tuple[str, int, int, int]]:
    c = collections.defaultdict(lambda: [0, 0, 0])
    for t in tests:
        for k in key(t):
            c[k][0 if t["status"] == "passed" else 1 if t["status"] in FAILED else 2] += 1
    return [(k, *v) for k, v in sorted(c.items())]


def render_html(slug: str, s: dict, env: list[tuple[str, str]], scorecard: list[list[str]], results: pathlib.Path) -> str:
    tests = s["tests"]
    e = html.escape
    passed = sum(t["status"] == "passed" for t in tests)
    failed = [t for t in tests if t["status"] in FAILED and not t["known"]]
    known = [t for t in tests if t["status"] in FAILED and t["known"]]
    fixed = [t for t in tests if t["status"] == "passed" and t["known"]]
    skipped = len(tests) - passed - len(failed) - len(known)
    verdict = "PASS" if not failed and not fixed else "FAIL"
    why = ("only known bugs failed" if verdict == "PASS" and known else "every test passed" if verdict == "PASS"
           else f"{len(failed)} failure(s) that are not known bugs" + (f"; {len(fixed)} known bug(s) now pass: flip them" if fixed else ""))

    def table(head, rows):
        return ("<table>" + ("<tr>" + "".join(f"<th>{e(h)}</th>" for h in head) + "</tr>" if head else "")
                + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</table>")

    def link_list(t):
        return ", ".join(f'<a href="{e(u)}">{e(n)}</a>' if u else e(n) for n, u in t["links"]) or "-"

    def shot(t):
        p = results / t["screenshot"] if t["screenshot"] else None
        if p and p.exists():
            return f'<img src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}" alt="screenshot on failure">'
        return "<p class=muted>no screenshot</p>"

    parts = [f"<h1>Test report: {e(slug)}</h1>",
             f'<p class="verdict {verdict.lower()}"><b>{verdict}</b>: {len(tests)} tests, {passed} passed, '
             f"{len(failed)} failed, {len(known)} known bugs, {skipped} skipped ({e(why)}).</p>",
             "<h2>Build and environment</h2>", table(None, [(f"<b>{e(k)}</b>", e(v)) for k, v in env]),
             "<h2>By module</h2>", table(["Module", "Passed", "Failed", "Skipped"],
                                         [(e(k), p, f, sk) for k, p, f, sk in _count(tests, lambda t: [t["module"]])]),
             "<h2>By requirement</h2>", table(["Requirement", "Passed", "Failed", "Skipped"],
                                              [(e(k), p, f, sk) for k, p, f, sk in _count(tests, lambda t: t["requirements"])])]
    parts.append(f"<h2>Failures ({len(failed)})</h2>")
    if not failed:
        parts.append("<p>None.</p>")
    for t in failed:
        parts.append(f'<div class="fail"><h3>{e(t["tc"])} {e(t["title"])}</h3>'
                     f'<p>Module {e(t["module"])}; requirement {e(", ".join(t["requirements"]))}; test <code>{e(t["name"])}</code>; '
                     f'Jira: {link_list(t)}</p>'
                     + (f'<p>Expected <b>{e(t["expected"])}</b>, actual <b>{e(t["actual"])}</b>.</p>' if t["expected"] or t["actual"] else "")
                     + f'<pre>{e(t["message"][:600])}</pre>{shot(t)}</div>')
    parts.append(f"<h2>Known bugs ({len(known)} still failing{f', {len(fixed)} now passing' if fixed else ''})</h2>")
    parts.append(table(["TC", "Test", "Status", "Jira"],
                       [(e(t["tc"]), e(t["title"]), "still failing" if t in known else "<b>now passes: flip it</b>", link_list(t))
                        for t in known + fixed]) if known or fixed else "<p>None.</p>")
    parts.append("<h2>Scorecard</h2>")
    parts.append(table(["Metric", "Value", "n"], [[e(c) for c in row] for row in scorecard]) if scorecard
                 else "<p class=muted>No scorecard in SUITE.md (run gene2 learn scorecard).</p>")
    parts.append(f'<p class="muted">Generated by Gen-e2 {e(harness_version())} from {e(str(results))}. '
                 f"Re-run the tests: <code>consolidated/{e(slug)}/run.sh --ci</code>.</p>")
    style = """@page { size: A4; margin: 14mm 12mm; }
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10px; color: #1f2933; }
h1 { font-size: 18px; color: #1e4d73; margin: 0 0 6px; } h2 { font-size: 13px; color: #1e4d73; margin: 14px 0 6px;
border-bottom: 1px solid #d7e3ec; } h3 { font-size: 11px; margin: 0 0 4px; }
table { border-collapse: collapse; width: 100%; margin-bottom: 6px; } th, td { border: 1px solid #d7e3ec; padding: 3px 5px;
text-align: left; vertical-align: top; } th { background: #eef4f8; }
.verdict { padding: 6px 8px; border-radius: 4px; } .pass { background: #e6f4ea; } .fail-v, .verdict.fail { background: #fdecea; }
.fail { border: 1px solid #f3c2bd; padding: 6px; margin-bottom: 8px; page-break-inside: avoid; }
pre { white-space: pre-wrap; background: #f6f8fa; padding: 4px; font-size: 9px; } img { max-width: 100%; max-height: 260px;
border: 1px solid #ccc; } .muted { color: #6b7785; } a { color: #1e4d73; }"""
    return f"<!doctype html><html><head><meta charset=utf-8><title>Test report {e(slug)}</title><style>{style}</style></head><body>{''.join(parts)}</body></html>"


def to_pdf(html_path: pathlib.Path, pdf_path: pathlib.Path) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.goto(html_path.resolve().as_uri())
        page.pdf(path=str(pdf_path), format="A4", print_background=True)
        b.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--results", help="default: consolidated/<slug>/reports/allure-results")
    ap.add_argument("--out", help="default: consolidated/<slug>/reports/test-report.pdf")
    ap.add_argument("--app-url", default="")
    ap.add_argument("--variant", default="")
    ap.add_argument("--html-only", action="store_true")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()
    results = pathlib.Path(a.results) if a.results else root / "consolidated" / a.slug / "reports" / "allure-results"
    out = pathlib.Path(a.out) if a.out else root / "consolidated" / a.slug / "reports" / "test-report.pdf"
    rs = load_results(results)
    if not rs:
        print(f"no allure results in {results}", file=sys.stderr)
        return 2
    suite = load_suite(root, a.slug)
    jira_base = os.environ.get("ATLASSIAN_BASE_URL", "").rstrip("/")
    s = summarise(rs, suite, jira_base)
    page = render_html(a.slug, s, environment(s["tests"], a.app_url, a.variant), suite["scorecard"], results)
    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix(".html")
    html_path.write_text(page, encoding="utf-8")
    if a.html_only:
        print(f"HTML: {html_path}")
        return 0
    to_pdf(html_path, out)
    print(f"PDF: {out} ({len(s['tests'])} tests)   HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
