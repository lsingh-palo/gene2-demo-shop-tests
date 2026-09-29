#!/usr/bin/env python3
"""QMetry Test Management for Jira Cloud (QTM4J) live sync: test cases from the suite manifest,
and each run's results into a test cycle - so QMetry, CI and the Allure report agree.

Endpoints follow the QTM4J Cloud Open API spec (SwaggerHub qmetry-ada/qtm4j_cloud, base path
/rest/api/latest/, header `apiKey`; checked 2026-09-24). Not the JUnit automation-import endpoint:
that one matches cases by JUnit names and would create duplicates without our TC ids.

    python tools/qmetry_sync.py cases   --slug S                         # dry run (reads QMetry if it can)
    python tools/qmetry_sync.py cases   --slug S --apply --confirm-host qtmcloud.qmetry.com
    python tools/qmetry_sync.py results --slug S --junit <junit.xml> --run <run id> [--apply --confirm-host ...]
    [--offline]  dry run without any network call

Matching (idempotent): a case is the QTM4J test case whose summary is exactly "<TC id> <title>" (the
same TC id as the QMetry Excel) in the Jira project, labelled `gene2`; a cycle is the one whose
summary is "gene2 <slug> <run id>". A second run changes nothing that is already right.
Each case is linked to the Jira stories of its requirement (requirements-map.json), so the story's
QMetry panel lists its tests and their latest results; the TC id -> QMetry key map is saved to
consolidated/<slug>/qmetry-cases.json for bugs and story comments. Every failed test with an OPEN
bug in the suite's ledger (bugs.json, filed by jira_bug.py) gets that bug attached to its execution
as a QMetry defect (idempotent: checked before every attempt, never linked twice). Cases and cycles
carry the label `gene2-live`, which is what `gene2 clean --qmetry` removes (never by key number).
Safety: dry run by default; --apply needs --confirm-host equal to the host of QMETRY_BASE_URL
(default https://qtmcloud.qmetry.com; Australia: https://syd-qtmcloud.qmetry.com); nothing is deleted.
Credentials: QMETRY_API_KEY (and QMETRY_BASE_URL, JIRA_PROJECT_KEY) through tools/_secrets.py only.
Save the key from the clipboard (not the interactive prompt, which cuts input at 128 characters):
    security add-generic-password -U -s gene2 -a QMETRY_API_KEY -w "$(pbpaste)"
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
DEFAULT_BASE = "https://qtmcloud.qmetry.com"
API = "/rest/api/latest"
LABEL = "gene2"
LIVE = "gene2-live"
RESULT_NAMES = {"passed": "Pass", "failed": "Fail", "skipped": "Not Executed"}


def host_of(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def check_host(base: str, confirm: str | None) -> str | None:
    if not confirm:
        return f"--apply needs --confirm-host {host_of(base)} (the configured QMetry host)"
    if confirm.strip().lower() != host_of(base):
        return f"--confirm-host {confirm!r} does not match the configured QMetry host {host_of(base)!r}"
    return None


class Client:
    """One method per QTM4J call used; every call is in the Open API spec."""

    def __init__(self, base: str, api_key: str):
        import requests
        self.base = base.rstrip("/") + API
        self.s = requests.Session()
        self.s.headers.update({"apiKey": api_key, "Content-Type": "application/json", "Accept": "application/json"})

    def _req(self, method, path, **kw):
        r = self.s.request(method, self.base + path, timeout=30, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.text.strip() else {}

    def project_id(self, key):
        data = self._req("POST", "/projects", json={"search": key, "qmetryEnabled": True}).get("data", [])
        hit = next((p for p in data if p.get("key") == key), None)
        return hit and hit["id"]

    def labels(self, pid):
        d = self._req("GET", f"/projects/{pid}/labels")
        return {l["name"]: l["id"] for l in (d if isinstance(d, list) else d.get("data", []))}

    def add_label(self, pid, name):
        return self._req("POST", f"/projects/{pid}/labels", json={"name": name}).get("id")

    def search_cases(self, pid, summary):
        return self._req("POST", "/testcases/search?maxResults=100&fields=summary,description,labels,version",
                         json={"filter": {"projectId": pid, "summary": summary}}).get("data", [])

    def create_case(self, body):
        return self._req("POST", "/testcases", json=body)

    def update_case(self, cid, version_no, body):
        self._req("PUT", f"/testcases/{cid}/versions/{version_no}", json=body)

    def search_cycles(self, pid, summary):
        # fields must be requested explicitly - without it the API omits summary entirely, which
        # made the "does this cycle already exist" check always false: found live (29 Sep) after
        # one suite's repeated CI runs had quietly created NINE duplicate cycles under the same
        # name, none of them ever reused. description is requested too: a rerun of the same run id
        # reads the env/version back out of it (see Sync.results), so without it here the same
        # field-omission bug would silently re-pick a new version on every rerun.
        return self._req("POST", "/testcycles/search?maxResults=50&fields=summary,description",
                         json={"filter": {"projectId": pid, "summary": summary}}).get("data", [])

    def create_cycle(self, body):
        return self._req("POST", "/testcycles", json=body)

    def link_cases(self, cycle_id, cases, environment_id=None, build_id=None):
        body = {"testCases": cases}
        if environment_id is not None:
            body["environmentId"] = environment_id
        if build_id is not None:
            body["buildId"] = build_id
        self._req("POST", f"/testcycles/{cycle_id}/testcases", json=body)

    def cycle_cases(self, cycle_id):
        # fields must be requested explicitly - without it the API omits summary AND
        # executionResult, which silently broke every result update (found live 29 Sep: 39
        # executions created and linked, all left "Not Executed" - the by-summary lookup in
        # Sync.results() matched nothing, so set_result was never actually called, even though
        # the run printed "result TCxxx -> Pass/Fail" as if it had been).
        return self._req("POST", f"/testcycles/{cycle_id}/testcases/search?maxResults=500&fields=summary,executionResult",
                         json={"filter": {}}).get("data", [])

    def case_requirements(self, cid, version_no=1):
        d = self._req("GET", f"/testcases/{cid}/requirements?tcVersionNo={version_no}&maxResults=100")
        return d if isinstance(d, list) else d.get("data", [])

    def link_requirements(self, cid, version_no, requirement_ids):
        # the spec's path uses "version" (singular) for this one call
        self._req("POST", f"/testcases/{cid}/version/{version_no}/requirements/link", json={"requirementIds": requirement_ids})

    def cases_with_label(self, pid, label):
        return self._req("POST", "/testcases/search?maxResults=500&fields=summary,labels,key",
                         json={"filter": {"projectId": pid, "labels": [label]}}).get("data", [])

    def delete_case(self, cid):
        self._req("DELETE", f"/testcases/{cid}")

    def delete_cycle(self, cycle_id):
        self._req("DELETE", f"/testcycles/{cycle_id}")

    def result_ids(self, pid):
        d = self._req("GET", f"/projects/{pid}/execution-results")
        return {r["name"]: r["id"] for r in (d if isinstance(d, list) else d.get("data", []))}

    def set_result(self, cycle_id, execution_id, result_id):
        self._req("PUT", f"/testcycles/{cycle_id}/testcase-executions/{execution_id}", json={"executionResultId": result_id})

    def environments(self, pid):
        d = self._req("GET", f"/projects/{pid}/environments")
        return {e["name"]: e["id"] for e in (d if isinstance(d, list) else d.get("data", []))}

    def add_environment(self, pid, name):
        return self._req("POST", f"/projects/{pid}/environments", json={"name": name}).get("id")

    def builds(self, pid):
        d = self._req("GET", f"/projects/{pid}/builds")
        return {b["name"]: b["id"] for b in (d if isinstance(d, list) else d.get("data", []))}

    def add_build(self, pid, name):
        return self._req("POST", f"/projects/{pid}/builds", json={"name": name}).get("id")

    def case_defects(self, cycle_id, execution_id):
        d = self._req("POST", f"/testcycles/{cycle_id}/testcase-executions/{execution_id}/defects", json={"filter": {}})
        return d if isinstance(d, list) else d.get("data", [])

    def link_defect(self, cycle_id, execution_id, defect_ids):
        self._req("PUT", f"/testcycles/{cycle_id}/testcase-executions/{execution_id}/defects", json={"defectIDs": defect_ids})


def manifest_cases(slug: str, root: pathlib.Path) -> list[dict]:
    suite = root / "consolidated" / slug
    m = json.loads((suite / "suite-manifest.json").read_text())["scenarios"]
    req = json.loads((suite / "requirements-map.json").read_text()) if (suite / "requirements-map.json").exists() else {}
    out = []
    for s in m:
        if s.get("orphan"):
            continue
        desc = (f"Automated by Gen-e2. Scenario key {s['key']}. Module {s['module']}. "
                f"{s.get('provenance', '')}. Test {s['test_file']}::{s['test_name']}."
                + (f" Requirements: {', '.join(req[s['key']])}." if req.get(s["key"]) else ""))
        out.append({"tc_id": s["tc_id"], "summary": f"{s['tc_id']} {s['title']}", "description": desc,
                    "test_name": s["test_name"], "slug_label": slug, "stories": req.get(s["key"], [])})
    return out


def junit_outcomes(path: pathlib.Path) -> dict[str, str]:
    out = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        name = re.sub(r"\[.*\]$", "", tc.get("name", ""))
        failed = any(c.tag in ("failure", "error") for c in tc)
        skipped = any(c.tag == "skipped" for c in tc)
        out[name] = "failed" if failed else ("skipped" if skipped else "passed")  # last attempt wins
    return out


class Sync:
    def __init__(self, client, project_key: str, apply: bool = False, out=print, story_ids=None, defect_ids=None):
        self.c, self.key, self.apply, self.out = client, project_key, apply, out
        self.story_ids = story_ids  # callable: [story keys] -> {key: Jira issue id}; None = no linking
        self.defect_ids = defect_ids  # callable: [jira keys] -> {key: Jira issue id}; None = no defect linking
        self.tc_keys: dict[str, str] = {}
        self.counts = collections.Counter()
        self.pid = client.project_id(project_key) if client else None
        if client and not self.pid:
            raise SystemExit(f"Jira project {project_key} is not QMetry-enabled (or not visible to this key)")

    def act(self, verb, what):
        self.counts[verb] += 1
        self.out(f"{'' if self.apply or verb == 'unchanged' else 'would '}{verb:<10} {what}")

    def _label_ids(self, names):
        have = self.c.labels(self.pid) if self.c else {}
        ids = []
        for n in names:
            if n not in have:
                self.act("create", f"label {n}")
                have[n] = self.c.add_label(self.pid, n) if self.apply else None
            ids.append(have[n])
        return ids

    def cases(self, cases: list[dict]) -> dict[str, dict]:
        """Create or update one QTM4J case per manifest scenario. Returns tc_id -> {id, versionNo}."""
        found = {}
        label_ids = self._label_ids([LABEL, LIVE, cases[0]["slug_label"]]) if cases else []
        for case in cases:
            hits = [h for h in (self.c.search_cases(self.pid, case["tc_id"]) if self.c else [])
                    if h.get("summary") == case["summary"]]
            if hits:
                h = hits[0]
                ver = (h.get("version") or {}).get("versionNo", 1)
                found[case["tc_id"]] = {"id": h["id"], "versionNo": ver}
                self.tc_keys[case["tc_id"]] = h.get("key", "")
                if (h.get("description") or "").strip() == case["description"]:
                    self.act("unchanged", f"{h.get('key')} {case['summary']}")
                else:
                    self.act("update", f"{h.get('key')} {case['summary']}")
                    if self.apply:
                        self.c.update_case(h["id"], ver, {"description": case["description"], "isAutomated": True})
            else:
                self.act("create", f"test case {case['summary']}")
                if self.apply:
                    r = self.c.create_case({"projectId": self.pid, "summary": case["summary"], "description": case["description"],
                                            "isAutomated": True, "labels": [i for i in label_ids if i is not None],
                                            "steps": [{"stepDetails": f"Run {case['test_name']}", "expectedResult": "The test passes."}]})
                    found[case["tc_id"]] = {"id": r.get("id"), "versionNo": r.get("versionNo", 1)}
                    self.tc_keys[case["tc_id"]] = r.get("key", "")
        self.link_stories(cases, found)
        return found

    def link_stories(self, cases: list[dict], found: dict) -> None:
        """Link each case to the Jira stories of its requirement (idempotent: only missing links)."""
        wanted = sorted({st for c in cases for st in c.get("stories", [])})
        if not wanted:
            return
        ids = self.story_ids(wanted) if (self.story_ids and self.c) else {}
        for case in cases:
            if not case.get("stories"):
                continue
            hit = found.get(case["tc_id"])
            have = set()
            if hit and hit.get("id") and self.c:
                have = {r.get("key") for r in self.c.case_requirements(hit["id"], hit.get("versionNo", 1))}
            missing = [st for st in case["stories"] if st not in have]
            if not missing:
                self.act("unchanged", f"{case['tc_id']} linked to {', '.join(case['stories'])}")
                continue
            self.act("link", f"{case['tc_id']} -> {', '.join(missing)}")
            if self.apply and hit and hit.get("id"):
                req_ids = [int(ids[st]) for st in missing if st in ids]
                if req_ids:
                    self.c.link_requirements(hit["id"], hit["versionNo"], req_ids)

    def results(self, slug: str, run_id: str, cases: list[dict], outcomes: dict[str, str],
                bugs_by_test: dict[str, str] | None = None, env: str = "test",
                version: str | None = None) -> str:
        """One cycle per run; link every case with a result under a QMetry Environment and Build
        (find-or-created by name; version defaults to one past the highest Build already in the
        project - read from QMetry itself via pick_next_build_version, not a local file, so it is
        correct even in CI where every run is a fresh checkout with no state of its own). A rerun
        of the SAME run id reuses the cycle's own env/version instead of advancing again, so it
        stays a true no-op. Sets each execution's result; attaches each failed test's open Jira
        bug to its execution as a QMetry defect, so the cycle and the bug point at each other
        (bugs_by_test: test_name -> Jira key, from the bug ledger)."""
        ids = self.cases(cases)
        summary = f"gene2 {slug} {run_id}"
        cycles = [c for c in (self.c.search_cycles(self.pid, summary) if self.c else []) if c.get("summary") == summary]
        with_result = [c for c in cases if c["test_name"] in outcomes]
        env_id = build_id = None
        if cycles:
            # this run's cycle already exists (a rerun of the same run id): reuse the env/version
            # it was created with instead of picking a new one, so a rerun stays a true no-op.
            cyc = cycles[0]
            self.act("unchanged", f"cycle {cyc.get('key')} {summary}")
            m = re.search(r"Environment: (.+)\nVersion: (.+)", cyc.get("description") or "")
            if m:
                env, version = m.group(1), m.group(2)
            if self.c and self.apply:
                env_id = self.c.environments(self.pid).get(env)
                build_id = self.c.builds(self.pid).get(version)
        else:
            if self.c:
                have_build = self.c.builds(self.pid)
                if not version:
                    version = pick_next_build_version(list(have_build.keys()))
                if self.apply:
                    have_env = self.c.environments(self.pid)
                    env_id = have_env.get(env) or self.c.add_environment(self.pid, env)
                    build_id = have_build.get(version) or self.c.add_build(self.pid, version)
            elif not version:
                version = "1.0"
            self.act("create", f"test cycle {summary!r} with {len(with_result)} cases (env {env}, version {version})")
            live_label = self._label_ids([LIVE])
            cyc = (self.c.create_cycle({"projectId": self.pid, "summary": summary, "labels": [i for i in live_label if i is not None],
                                        "description": f"Gen-e2 automated run {run_id}\nEnvironment: {env}\nVersion: {version}"})
                   if self.apply else {"id": None})
        linked = {x.get("summary"): x for x in (self.c.cycle_cases(cyc["id"]) if self.c and cyc.get("id") else [])}
        missing = [c for c in with_result if c["summary"] not in linked]
        if missing:
            self.act("link", f"{len(missing)} case(s) to the cycle")
            if self.apply:
                self.c.link_cases(cyc["id"], [{"id": ids[c["tc_id"]]["id"], "versionNo": ids[c["tc_id"]]["versionNo"]}
                                              for c in missing if c["tc_id"] in ids], env_id, build_id)
                linked = {x.get("summary"): x for x in self.c.cycle_cases(cyc["id"])}
        result_ids = self.c.result_ids(self.pid) if self.c else {}
        for c in with_result:
            want = RESULT_NAMES[outcomes[c["test_name"]]]
            ex = linked.get(c["summary"])
            now = ((ex or {}).get("executionResult") or {}).get("name")
            if ex and now == want:
                self.act("unchanged", f"{c['tc_id']} {want}")
                continue
            self.act("result", f"{c['tc_id']} -> {want}")
            if self.apply and ex:
                self.c.set_result(cyc["id"], ex["testCaseExecutionId"], result_ids[want])
        self._attach_defects(cyc, with_result, linked, outcomes, bugs_by_test or {})
        return version

    def _attach_defects(self, cyc, with_result, linked, outcomes, bugs_by_test: dict[str, str]) -> None:
        """Link the open Jira bug of every failed test to its QMetry execution (idempotent: only
        when it is not already linked)."""
        failed = [c for c in with_result if outcomes.get(c["test_name"]) == "failed" and c["test_name"] in bugs_by_test]
        if not failed or not cyc.get("id"):
            return
        keys = sorted({bugs_by_test[c["test_name"]] for c in failed})
        ids = self.defect_ids(keys) if (self.defect_ids and self.c) else {}
        for c in failed:
            key = bugs_by_test[c["test_name"]]
            ex = linked.get(c["summary"])
            if not ex:
                continue
            have = ({d.get("key") for d in self.c.case_defects(cyc["id"], ex["testCaseExecutionId"])}
                    if self.c else set())
            if key in have:
                self.act("unchanged", f"{c['tc_id']} defect {key} already attached")
                continue
            self.act("defect", f"{c['tc_id']} -> {key}")
            if self.apply and key in ids:
                self.c.link_defect(cyc["id"], ex["testCaseExecutionId"], [int(ids[key])])


def jira_issue_ids(keys: list[str]) -> dict[str, str]:
    """Jira issue ids for a list of keys (QTM4J links requirements and defects by issue id, never
    by key). Used both for story links (on cases) and defect links (on failed executions).

    Degrades to {} (never raises) when Atlassian credentials are not configured: linking a case to
    its story, or a bug to its execution, is a nice-to-have on top of the cases/results sync, never
    a reason to fail the whole sync - found live (29 Sep): a run with QMetry configured but no
    ATLASSIAN_EMAIL/ATLASSIAN_API_TOKEN set crashed the entire `results` step on this call, even
    though every case and every pass/fail result had already synced correctly."""
    import jira_live
    try:
        client = jira_live.JiraClient()
    except SystemExit as e:
        print(f"warning: story/defect links skipped - {e}", file=sys.stderr)
        return {}
    jql = f"key in ({', '.join(keys)})"
    return {i["key"]: i["id"] for i in client.search(jql, fields="summary")}


def pick_next_build_version(existing_names: list[str]) -> str:
    """1.0 the first time; otherwise one past the highest N.M name already in QMetry. Reading this
    from QMetry's own Builds, not a local file, is what makes it correct in CI: every run is a
    fresh checkout with no state of its own, but the project's builds persist between runs."""
    best = (0, -1)
    for name in existing_names:
        major, _, minor = str(name).partition(".")
        try:
            pair = (int(major), int(minor or 0))
        except ValueError:
            continue
        best = max(best, pair)
    return f"{best[0]}.{best[1] + 1}" if best != (0, -1) else "1.0"


def next_version(slug: str, root: pathlib.Path, explicit: str | None = None) -> str:
    """The version to record on this run's cycle: given explicitly, or the next one after the
    last auto-picked version for this slug (1.0 the first time, then 1.1, 1.2, ... never reused,
    tracked in consolidated/<slug>/qmetry-version.json so a rerun does not repeat "1.0")."""
    state = root / "consolidated" / slug / "qmetry-version.json"
    if explicit:
        if state.exists():
            d = json.loads(state.read_text())
        else:
            d = {}
        d["version"] = explicit
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps(d, indent=2) + "\n")
        return explicit
    if not state.exists():
        version = "1.0"
    else:
        last = json.loads(state.read_text()).get("version", "1.0")
        major, _, minor = last.partition(".")
        try:
            version = f"{major}.{int(minor or 0) + 1}"
        except ValueError:
            version = "1.0"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"version": version}, indent=2) + "\n")
    return version


def find_allure_results(slug: str, junit: str | None, root: pathlib.Path) -> pathlib.Path:
    """Where allure-results actually is differs by how the run was started (a local run.sh puts it
    under the suite's own reports/, a CI run points --alluredir at the repo root) - try the real
    candidates rather than guessing one path from --junit's location."""
    candidates = [root / "allure-results", root / "consolidated" / slug / "reports" / "allure-results"]
    if junit:
        j = pathlib.Path(junit).resolve()
        candidates = [j.parent / "allure-results", j.parent.parent / "allure-results"] + candidates
    return next((c for c in candidates if c.exists()), candidates[0])


def write_allure_environment(results_dir: pathlib.Path, env: str, version: str, run_id: str) -> None:
    """Allure shows a properties file at the root of allure-results as an "Environment" panel on
    the report - this is the one place Allure natively supports this, so nothing custom needed on
    the report-generation side."""
    if not results_dir.exists():
        return
    (results_dir / "environment.properties").write_text(
        f"Environment={env}\nVersion={version}\nRun={run_id}\n")


def bugs_by_test(slug: str, root: pathlib.Path) -> dict[str, str]:
    """test_name -> Jira key, for every OPEN bug in the suite's ledger (bugs.json)."""
    import bug_ledger
    ledger = bug_ledger.load(slug, root=str(root / "consolidated"))
    out = {}
    for b in ledger.get("bugs", []):
        if b.get("status") == "open" and b.get("test") and b.get("jira"):
            out[b["test"].split("::")[-1]] = b["jira"]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["cases", "results"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--junit")
    ap.add_argument("--run", help="run id for the cycle summary (default: the junit file's parent run)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-host")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--env", default="test", help="QMetry Environment name (default: test)")
    ap.add_argument("--version", help="QMetry Build name; default: auto-increment 1.0, 1.1, 1.2, ... (never repeated)")
    a = ap.parse_args(argv)
    root = pathlib.Path.cwd()  # the project, like every other tool
    cases = manifest_cases(a.slug, root)
    outcomes = junit_outcomes(pathlib.Path(a.junit)) if a.cmd == "results" else {}
    if a.cmd == "results" and not a.junit:
        sys.exit("results needs --junit")
    run_id = a.run or (pathlib.Path(a.junit).resolve().parents[1].name if a.junit else "")
    # --offline has no QMetry to read existing Builds from, so it keeps the local-file auto-increment;
    # otherwise results() itself picks the next version from QMetry's own Builds (see pick_next_build_version).
    version = next_version(a.slug, root, a.version) if (a.cmd == "results" and a.offline) else a.version
    import _secrets
    project = _secrets.get("JIRA_PROJECT_KEY") or "PROJECT"
    if a.offline:
        if a.apply:
            sys.exit("--apply cannot be --offline")
        print(f"DRY RUN (offline): {len(cases)} cases for Jira project {project}; nothing is read or written")
        s = Sync(None, project)
    else:
        base = (_secrets.get("QMETRY_BASE_URL") or DEFAULT_BASE).rstrip("/")
        if a.apply and (reason := check_host(base, a.confirm_host)):
            print(f"refused: {reason}. Nothing was called.", file=sys.stderr)
            return 2
        key = _secrets.get("QMETRY_API_KEY")
        if not key:
            print("missing QMETRY_API_KEY. Save it from the clipboard:\n"
                  "  security add-generic-password -U -s gene2 -a QMETRY_API_KEY -w \"$(pbpaste)\"", file=sys.stderr)
            return 2
        print(f"QMetry host: {host_of(base)}   project: {project}   {'APPLY' if a.apply else 'DRY RUN: reading only'}")
        s = Sync(Client(base, key), project, apply=a.apply, story_ids=jira_issue_ids, defect_ids=jira_issue_ids)
    if a.cmd == "cases":
        s.cases(cases)
    else:
        version = s.results(a.slug, run_id, cases, outcomes, bugs_by_test(a.slug, root), a.env, version)
        write_allure_environment(find_allure_results(a.slug, a.junit, root), a.env, version, run_id)
    if a.apply and s.tc_keys:
        out = root / "consolidated" / a.slug / "qmetry-cases.json"
        out.write_text(json.dumps(dict(sorted(s.tc_keys.items())), indent=2) + "\n")
        print(f"TC id -> QMetry key map: {out}")
    print(f"\nsummary: {dict(s.counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
