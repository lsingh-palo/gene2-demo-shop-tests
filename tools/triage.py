#!/usr/bin/env python3
"""Failure triage: the evidence for every failed test, a proposed class, and a recorded decision.

Only a failure confirmed as a product bug is filed in Jira (`jira_bug.py --from-triage`). Code
collects the evidence and proposes; the model (or a person) confirms each row with `set`, giving
the reason. A row nobody confirmed is never filed.

    gene2 triage build --slug S --junit <junit.xml> [--parity parity.json] [--reports <dir>] [--out <dir>]
    gene2 triage set   --file <triage.json> --test <test name> --class product_bug \\
                       --reason "value wrong, element found, passes on the reference build" \\
                       [--module M] [--title "<expected behaviour, one line>"] [--severity High]
                       [--duplicate-of KEY]   # an open bug that already describes it: comment, not a new bug
    gene2 triage show  --file <triage.json>

Classes:
    product_bug   the app is wrong: the element was found and the value or state is wrong
    known_bug     a @pytest.mark.bug reproduction (or a ledger bug) failed as designed
    test_defect   the test is wrong or stale: locator drift, bad wait (-> the healer, never a bug)
    environment   the app or browser was unreachable (-> rerun, never a bug)
    needs_review  the evidence does not decide it; a person looks

Evidence per row: the assertion message, expected vs actual (as Playwright or assert reported
them), screenshot and trace on failure, the scenario (TC id, key, title, module, requirement ids),
the linked Jira stories (requirements-map.json), and, with --parity, the result on the reference
build. Writes triage.json (the record) and triage.md (for a person).
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

CLASSES = ("product_bug", "known_bug", "test_defect", "environment", "needs_review")

# same rule as the conftest template's _looks_like_drift: drift only when the element itself was
# not found (or matched ambiguously); "locator resolved to <" / "unexpected value" means the
# element exists and the value is wrong
_RESOLVED = re.compile(r"locator resolved to <|unexpected value|resolved to [1-9]\d* elements?", re.I)
_ZERO = re.compile(r"resolved to 0 elements", re.I)
_NEVER_FOUND = re.compile(r"resolved to 0 elements|waiting for (?:selector|locator)", re.I)
_TIMED_OUT = re.compile(r"timeout|timed out", re.I)
_ENV = re.compile(r"net::ERR_|ECONNREFUSED|Connection refused|Target (?:page, context or browser )?(?:has been )?closed"
                  r"|browser has been closed|NS_ERROR_CONNECTION_REFUSED|Could not connect", re.I)
_ACTUAL = re.compile(r"^(?:E\s+)?(?:actual value|received(?: string| value)?)\s*:\s*(.*?)\s*$", re.I | re.M)
_ASSERT = re.compile(r"assert (.+?) == (.+?)$", re.M)


def looks_like_drift(err: str) -> bool:
    if re.search(r"strict mode violation", err, re.I):
        return True
    if _RESOLVED.search(err):
        return False
    return bool(_NEVER_FOUND.search(err) and _TIMED_OUT.search(err))


def expected_actual(msg: str) -> tuple[str, str]:
    """(expected, actual) as the assertion reported them; empty strings when it did not say."""
    head = msg.split("Call log:")[0]
    act = _ACTUAL.search(head)
    if act:
        exp = (re.search(r"expected (?:to (?:have|contain) [\w ]+?|string|value|pattern)\s*:?\s*['\"](.*)['\"]\s*$", head, re.I | re.M)
               or re.search(r"expected (to be \w+)", head, re.I))
        return (exp.group(1) if exp else ""), act.group(1).strip()
    m = _ASSERT.search(msg)
    if m:
        return m.group(2).strip(), m.group(1).strip()
    return "", ""


def failures(junit: pathlib.Path) -> list[dict]:
    out = []
    for tc in ET.parse(junit).getroot().iter("testcase"):
        bad = next((c for c in tc if c.tag in ("failure", "error")), None)
        if bad is None:
            continue
        out.append({"test": re.sub(r"\[.*\]$", "", tc.get("name", "")), "param": (re.search(r"\[(.*)\]$", tc.get("name", "")) or [None, ""])[1],
                    "classname": tc.get("classname", ""), "kind": bad.tag,
                    "message": (bad.get("message") or "").strip(), "detail": (bad.text or "")[-2000:]})
    return out


def is_bug_marked(suite: pathlib.Path, test_file: str, test_name: str) -> bool:
    src = suite / test_file
    if not src.exists():
        return False
    lines = src.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"\s*def {re.escape(test_name)}\(", line):
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("@"):
                if "mark.bug" in lines[j]:
                    return True
                j -= 1
            return False
    return False


def error_text(message: str, detail: str) -> str:
    """The assertion error only (the `E ` lines), never the test's source code: a source line such
    as `page.wait_for_selector(..., timeout=...)` must not make a wrong value look like drift."""
    e_lines = [l[1:].strip() for l in detail.splitlines() if l.startswith("E ")]
    return "\n".join(e_lines) or message


def propose(row: dict) -> tuple[str, str]:
    msg = error_text(row["message"], row["detail"])
    if row.get("known_bug"):
        return "known_bug", "a known-bug reproduction failed as designed"
    if _ENV.search(msg):
        return "environment", "the app or browser was unreachable"
    if _ZERO.search(msg) and re.search(r"^Actual value: \[\]", msg, re.M | re.I):
        return "needs_review", ("no element matched: the page shows no result (a product bug) or the locator "
                                "is stale (a test defect); the screenshot decides")
    if looks_like_drift(msg):
        return "test_defect", "the element was never found: locator drift or a bad wait (healer)"
    if row.get("reference") is False:
        return "needs_review", "also fails on the reference build: a shared bug or a wrong test"
    if _RESOLVED.search(msg) or _ASSERT.search(msg) or row["expected"]:
        why = "the element was found and the value or state is wrong"
        return "product_bug", why + ("; passes on the reference build" if row.get("reference") else "")
    return "needs_review", "the evidence does not decide it"


def build(slug: str, junit: pathlib.Path, root: pathlib.Path, parity: pathlib.Path | None,
          reports: pathlib.Path | None) -> dict:
    suite = root / "consolidated" / slug
    scen = {s["test_name"]: s for s in json.loads((suite / "suite-manifest.json").read_text())["scenarios"]}
    req_map = json.loads((suite / "requirements-map.json").read_text()) if (suite / "requirements-map.json").exists() else {}
    ledger = json.loads((suite / "bugs.json").read_text()) if (suite / "bugs.json").exists() else {}
    ledger_rows = ledger.get("bugs", []) if isinstance(ledger, dict) else ledger
    ledger_tests = {v["test"].split("::")[-1]: v for v in ledger_rows
                    if isinstance(v, dict) and v.get("test") and v.get("status") == "open"}
    ref = {}
    if parity and parity.exists():
        for r in json.loads(parity.read_text()).get("rows", []):
            ref[re.sub(r"\[.*\]$", "", r["test"].split("::")[-1])] = r.get("legacy")
    reports = reports or junit.parent
    rows = []
    for f in failures(junit):
        s = scen.get(f["test"], {})
        exp, act = expected_actual(error_text(f["message"], f["detail"]))
        shots = sorted(str(p) for p in (reports / "screenshots" / "errors").glob(f"{f['test']}*.png")) if reports.exists() else []
        traces = sorted(str(p) for p in (reports / "traces").glob(f"{f['test']}*.zip")) if reports.exists() else []
        row = {
            "test": f["test"], "test_file": s.get("test_file", ""), "param": f["param"],
            "tc_id": s.get("tc_id", ""), "key": s.get("key", ""), "title": s.get("title", f["test"]),
            "module": s.get("module", ""), "requirements": s.get("requirement", []),
            "stories": req_map.get(s.get("key", ""), []),
            "message": f["message"].split("Call log:")[0].strip()[:600], "detail": f["detail"],
            "expected": exp, "actual": act, "screenshots": shots, "traces": traces,
            "reference": ref.get(f["test"]),
            "known_bug": bool(s and is_bug_marked(suite, s.get("test_file", ""), f["test"])) or f["test"] in ledger_tests,
        }
        row["proposed"], row["proposed_reason"] = propose(row)
        row.update({"class": row["proposed"], "confirmed": False, "reason": "",
                    "bug_module": row["module"], "bug_title": row["title"], "severity": "Medium",
                    "duplicate_of": ""})
        rows.append(row)
    return {"slug": slug, "junit": str(junit), "run": junit.resolve().parents[1].name,
            "built": datetime.datetime.now().isoformat(timespec="seconds"), "rows": rows}


def render_md(t: dict) -> str:
    counts = {c: sum(1 for r in t["rows"] if r["class"] == c) for c in CLASSES}
    out = [f"# Failure triage - {t['slug']} ({t['run']})", "",
           f"{len(t['rows'])} failed tests. " + ", ".join(f"{c}: {n}" for c, n in counts.items() if n) + ".",
           f"Confirmed: {sum(r['confirmed'] for r in t['rows'])} of {len(t['rows'])}. "
           "Only confirmed product_bug rows are filed; known_bug rows add a comment to the open bug.", "",
           "| TC | Test | Class | Confirmed | Expected | Actual | Reference build | Stories |",
           "|---|---|---|---|---|---|---|---|"]
    for r in t["rows"]:
        refs = {True: "passed", False: "failed", None: "not run"}[r["reference"]]
        out.append(f"| {r['tc_id']} | `{r['test']}` | {r['class']} | {'yes' if r['confirmed'] else 'no'} | "
                   f"{r['expected'][:40]} | {r['actual'][:40]} | {refs} | {', '.join(r['stories'])} |")
    out.append("")
    for r in t["rows"]:
        out += [f"## {r['tc_id']} {r['title']}", "",
                f"- class: **{r['class']}** (proposed {r['proposed']}: {r['proposed_reason']})"
                + (f"; confirmed: {r['reason']}" if r["confirmed"] else "; NOT confirmed"),
                f"- test: `{r['test_file']}::{r['test']}`  requirements: {', '.join(r['requirements']) or '-'}",
                f"- assertion: {r['message'].splitlines()[0] if r['message'] else '-'}",
                f"- expected: {r['expected'] or '-'}   actual: {r['actual'] or '-'}",
                f"- evidence: {', '.join(r['screenshots'] + r['traces']) or 'no screenshot or trace found'}", ""]
    return "\n".join(out) + "\n"


def write(t: dict, out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "triage.json").write_text(json.dumps(t, indent=2) + "\n")
    (out / "triage.md").write_text(render_md(t))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--slug", required=True)
    b.add_argument("--junit", required=True)
    b.add_argument("--parity")
    b.add_argument("--reports", help="the reports folder with screenshots/ and traces/ (default: next to the junit file)")
    b.add_argument("--out", help="default: the run's docs/ folder (sibling of the junit file's folder)")
    s = sub.add_parser("set")
    s.add_argument("--file", required=True)
    s.add_argument("--test", required=True)
    s.add_argument("--class", dest="cls", required=True, choices=CLASSES)
    s.add_argument("--reason", required=True)
    s.add_argument("--module")
    s.add_argument("--title")
    s.add_argument("--severity", choices=["Low", "Medium", "High", "Critical"])
    s.add_argument("--duplicate-of", help="the key of an OPEN bug that already describes this failure")
    sh = sub.add_parser("show")
    sh.add_argument("--file", required=True)
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()

    if a.cmd == "build":
        junit = pathlib.Path(a.junit)
        t = build(a.slug, junit, root, pathlib.Path(a.parity) if a.parity else None,
                  pathlib.Path(a.reports) if a.reports else None)
        out = pathlib.Path(a.out) if a.out else junit.resolve().parents[1] / "docs"
        write(t, out)
        n = len(t["rows"])
        print(f"{n} failure(s) triaged -> {out / 'triage.md'}")
        for r in t["rows"]:
            print(f"  {r['tc_id'] or '-':6} {r['test']:<50} proposed {r['proposed']}")
        print("Confirm each row: gene2 triage set --file ... --test ... --class ... --reason \"...\"")
        return 0

    path = pathlib.Path(a.file)
    t = json.loads(path.read_text())
    if a.cmd == "show":
        print(render_md(t))
        return 0
    row = next((r for r in t["rows"] if r["test"] == a.test), None)
    if row is None:
        print(f"no failed test {a.test!r} in {path}", file=sys.stderr)
        return 2
    if not a.reason.strip():
        print("--reason must say why (the evidence you used)", file=sys.stderr)
        return 2
    row.update({"class": a.cls, "confirmed": True, "reason": a.reason.strip()})
    if a.module:
        row["bug_module"] = a.module
    if a.title:
        row["bug_title"] = a.title
    if a.severity:
        row["severity"] = a.severity
    if a.duplicate_of:
        row["duplicate_of"] = a.duplicate_of.strip()
    write(t, path.parent)
    print(f"{row['tc_id']} {a.test}: {a.cls} (confirmed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
