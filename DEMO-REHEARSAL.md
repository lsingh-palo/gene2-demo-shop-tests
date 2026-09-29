# Demo rehearsal procedure

Everything runs from the root of this repo with one short command per step: `./gene2 <command>`
(`./gene2 help` lists them). It uses the suite's own Python environment, created on first use, so
it behaves the same from a terminal or from any AI assistant. Storyline: **smoke -> functional ->
extended -> full (known bugs) -> release candidate (real failures, bugs filed live) -> exploratory
(a new test)**, locally and in GitHub Actions, with every run in QMetry and a live Allure report.

| | |
|---|---|
| Local repo | this folder |
| Remote repo | https://github.com/lsingh-palo/gene2-demo-shop-tests |
| CI runs | https://github.com/lsingh-palo/gene2-demo-shop-tests/actions |
| Live Allure report (latest non-PR CI run) | https://lsingh-palo.github.io/gene2-demo-shop-tests/ |
| Run reports on this laptop | `.gene2-local/runs/<run id>.md`, all runs in `.gene2-local/runs/INDEX.md` (never committed) |

---

## 0. One-time setup (already done for this repo)

- GitHub secrets: `QMETRY_API_KEY`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`. Variables:
  `GENE2_TARGET_SLUG=gene2-demo-shop`, `GENE2_BASE_URL=http://127.0.0.1:8801`,
  `GENE2_APP_START=python3 demo-app/serve.py --port 8801`, `QMETRY_BASE_URL`, `JIRA_PROJECT_KEY`,
  `ATLASSIAN_BASE_URL`.
- GitHub Pages: Settings -> Pages -> Source "GitHub Actions"; the `github-pages` environment allows
  `main` and `gene2/**`.
- This laptop: the same credentials in the keychain (the tools read them from there):

```bash
security add-generic-password -U -s gene2 -a QMETRY_API_KEY -w "$(pbpaste)"
```

---

## 1. Ready? Anything left over?

```bash
./gene2 preflight
```

Read-only. A table of: branch, uncommitted and unpushed work, local run leftovers, whether the demo
app is already running, credentials (names only), the bugs, harness comments, QMetry cycles
(with their executions) and cases that earlier runs left, the last CI runs, the live report. Then
the exact commands to clear each one.

## 2. Clean slate

```bash
./gene2 clean            # dry run: lists everything it would remove
./gene2 clean --apply    # asks you to TYPE the Jira host, then deletes
```

It removes what runs of this suite created, found by label and marker (never by a key range):
Jira bugs (`gene2-live` + `gene2-suite-gene2-demo-shop`, and every bug in the suite's ledger by its
fingerprint label, including ones filed before the `gene2-live` label existed), harness comments
on stories, QMetry test cycles named `gene2 gene2-demo-shop ...` (deleting a cycle deletes its
executions: an execution only exists inside its cycle) and test cases labelled `gene2-live`, and
local run leftovers. Only a person at a terminal can type the host, so no script or AI assistant
can delete on its own. It also empties `consolidated/gene2-demo-shop/bugs.json`; push that so CI
stops linking the deleted bugs:

```bash
git add consolidated/gene2-demo-shop/bugs.json && git commit -m "Reset the bug ledger" && git push
```

`./gene2 preflight` again should show zero leftovers. The next run is Version 1.0.

## 3. Run a level, locally or in CI

| Level | What | Local | CI |
|---|---|---|---|
| smoke | 5 critical-path tests (every PR runs this) | `./gene2 run smoke headed` | `./gene2 ci smoke` |
| functional | 39 standard regression tests (every push) | `./gene2 run functional` | `./gene2 ci functional` |
| extended | edge and security tests (nightly) | `./gene2 run extended` | `./gene2 ci extended` |
| exploratory | tests promoted from exploratory sessions | `./gene2 run exploratory v2` | `./gene2 ci exploratory` |
| full | every test; the 2 known-bug reproductions fail as designed and the run stays green | `./gene2 run full` | `./gene2 ci full` |

Add `v2` to run against the release candidate (`demo-app` v2, which has regressions): real
failures, to triage and file. `headed` shows the browser (one worker).

A **local run** runs the tests, syncs them into QMetry (one cycle per run, Environment `test`,
Version one past this suite's last one) and writes the run report. `./gene2 allure` opens that
run's Allure report in the browser (served over http: a report opened as a file cannot load its
data, which is the "failed to fetch" error).

A **CI run** (`./gene2 ci ...`) starts the workflow on the pushed branch, waits, and brings the run
report back into `.gene2-local/runs/`. On GitHub, the run page starts with **Open the Allure report
for this run** (the live report, with trend charts and the Environment panel showing the version)
followed by the full run report. Pull request runs are previews: they keep only the zipped report
and do not add a QMetry cycle.

Every run report has: the verdict and counts, the CI run URL, the live Allure URL, the QMetry cycle
key with Environment and Version, the Jira bugs, a link listing every bug this suite filed, the
local and remote repo, results by module, a **failed test -> TC id -> QMetry case -> Jira bug**
table where each bug is marked *filed now*, *pre-existing* or *none yet*, the **new test cases**
created in QMetry, and what is pending.

```bash
./gene2 report     # the latest run report
./gene2 status     # every run in one table
./gene2 allure ci  # open the live CI report
./gene2 open ci    # open the latest CI run page
```

## 4. Failures become bugs, live

```bash
./gene2 triage       # every failure of the latest run: evidence, expected vs actual, a proposed class
./gene2 accept       # after you agree: confirms the product-bug and known-bug rows
./gene2 bugs         # files them in Jira now, attaches each to its QMetry execution, refreshes the report
git add consolidated/gene2-demo-shop/bugs.json && git commit -m "Record bugs filed in run <id>" && git push
```

`./gene2 bugs --dry-run` prints the bugs it would file (steps, expected, actual, screenshot, build
and environment) without creating any. A bug is filed once per defect (a second run adds a comment
to the open bug instead of a duplicate). Rows proposed `needs_review` wait for a person.

## 5. Exploratory: a new test from a finding

1. Explore an area on app v2 (`python3 demo-app/serve.py --variant v2 --port 8801`), by hand or with
   an AI browser tool, looking for what the suite does not cover yet.
2. Write the reproduction test in `consolidated/gene2-demo-shop/tests/`, marked
   `@pytest.mark.exploratory` (plus `@pytest.mark.bug` while the defect is open).
3. Register it: `./gene2 promote <test name> --module <module> --title "<expected behaviour>"` (it
   gets the scenario key and the next TC id in the suite manifest).
4. `./gene2 run exploratory v2`: it runs, QMetry creates its case (listed under "New test cases").
5. `./gene2 triage`, `./gene2 accept`, `./gene2 bugs` to file the defect.
6. Commit the test and `suite-manifest.json`, push, and `./gene2 ci full v2`.

## 6. QMetry: environment and version

- Environment defaults to `test`; version defaults to one past the highest version this suite's own
  cycles used: 1.0 after a clean slate, then 1.1, 1.2, ... for local and CI runs alike (QMetry
  holds the state, so a fresh CI checkout counts correctly). Rerunning the same run id changes
  nothing. `./gene2 tool qmetry_sync results ... --env <name> --version <x>` pins them explicitly.
- The same Environment, Version and run id are written into the Allure report's Environment panel.
- Cycle names: `gene2 gene2-demo-shop <run id>`; a local run id is `local-<level>[-v2]-<time>`, a
  CI one `gh-<Actions run id>-<level>`, so a cycle leads straight back to its run.

## 7. Command reference

| Command | Does |
|---|---|
| `./gene2 preflight` | ready check and leftovers (read-only) |
| `./gene2 clean [--apply]` / `./gene2 clean local` | remove what runs created / local leftovers only |
| `./gene2 run <level> [v2] [headed]` | run here + QMetry sync + run report |
| `./gene2 ci <level> [v2]` | run in GitHub Actions, wait, fetch the run report |
| `./gene2 triage` / `accept` / `bugs [--dry-run]` | failures -> confirmed -> Jira bugs attached in QMetry |
| `./gene2 promote <test> --module M --title T` | add a new exploratory test to the manifest |
| `./gene2 report` / `status` | latest run report / all runs |
| `./gene2 allure [ci]` / `open ci\|repo\|actions` | open reports and pages in the browser |
| `./gene2 tool <script> [args]` | any script in `tools/` with the suite's Python |
