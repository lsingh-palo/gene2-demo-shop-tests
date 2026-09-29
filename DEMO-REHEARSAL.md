# Demo rehearsal procedure

Everything below runs from the root of this repo (`gene2-demo-shop-tests`), on your own laptop and
in this repo's GitHub Actions. No harness, no `gene2` CLI: this suite carries the 8 scripts it
needs under `tools/` and is meant to run on its own.

Storyline: **smoke -> functional -> extended -> exploratory**, in both CI and QMetry, with real
bugs filed as they are found (never old ones), then a full clean-slate reset including QMetry
executions.

---

## 0. One-time setup (skip if already done)

- GitHub repo secrets: `QMETRY_API_KEY`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN` (Settings ->
  Secrets and variables -> Actions -> Secrets).
- GitHub repo variables: `GENE2_TARGET_SLUG=gene2-demo-shop`, `GENE2_BASE_URL=http://127.0.0.1:8801`,
  `GENE2_APP_START=python3 demo-app/serve.py --port 8801`, `GENE2_BROWSERS=chromium`,
  `GENE2_WORKERS=3`, `QMETRY_BASE_URL=https://qtmcloud.qmetry.com`, `JIRA_PROJECT_KEY=SHOP`,
  `ATLASSIAN_BASE_URL=https://<your-site>.atlassian.net` (Settings -> Secrets and variables ->
  Actions -> Variables).
- Local machine: same credentials saved to the keychain so the scripts under `tools/` can read
  them without you pasting anything each time:

```bash
security add-generic-password -U -s gene2 -a QMETRY_API_KEY -w "<your key>"
security add-generic-password -U -s gene2 -a ATLASSIAN_API_TOKEN -w "<your token>"
```

- GitHub Pages: Settings -> Pages -> Source: "GitHub Actions" (one time; already on for this repo).
  The live Allure report for every push lands at
  `https://<your-username>.github.io/gene2-demo-shop-tests/`.

---

## 1. Clean slate

Local: delete the venv-free run state so the next run starts fresh (harmless, it reinstalls once).

```bash
rm -rf consolidated/gene2-demo-shop/.venv consolidated/gene2-demo-shop/reports \
       consolidated/gene2-demo-shop/qmetry-version.json consolidated/gene2-demo-shop/qmetry-cases.json
```

QMetry and Jira: this is the one step you must run yourself at a real terminal. `tools/clean.py` is
deliberately built so a script (or an AI assistant) cannot run it: **you type the Jira host**
before anything is deleted, and it is a dry run until you add `--apply`. It removes exactly what
earlier runs created - QMetry test cases labelled `gene2-live` + `gene2-demo-shop`, test cycles
named `gene2 gene2-demo-shop ...`, Jira issues labelled the same way, and run/story-status comments
by their marker line - never by guessing a key range or a date. Deleting a test cycle in QMetry
removes its executions with it: an execution is not a resource of its own, it only exists as a row
inside its cycle, so there is nothing left to clean up separately.

```bash
# dry run first - lists everything that would be removed, deletes nothing
python tools/clean.py --slug gene2-demo-shop --jira --qmetry
```

```bash
# the real cleanup - you will be asked to type your Jira host before it deletes anything
python tools/clean.py --slug gene2-demo-shop --jira --qmetry --apply
```

The local suite itself (`consolidated/gene2-demo-shop/`) is committed to this repo, so
`tools/clean.py` (with no `--jira`/`--qmetry`) always lists it as "kept" - it only ever removes
untracked run folders, never the suite you are demoing.

You should now have: no local `reports/`, no `qmetry-version.json` (next version will start at
whatever QMetry's remaining Builds say, or `1.0` if you also removed the Builds), no gene2-created
QMetry cycles, cases or executions, no gene2-created Jira bugs or story-status comments.

---

## 2. Smoke - the fast, must-always-pass tier

**Local, headed** (watch it run, no parallelism):

```bash
GENE2_APP_START="python3 demo-app/serve.py --port 8801" GENE2_BASE_URL="http://127.0.0.1:8801" \
  bash consolidated/gene2-demo-shop/run.sh -m smoke
```

**Local, CI-mode** (headless, parallel, produces the JUnit/Allure files the sync steps need):

```bash
GENE2_APP_START="python3 demo-app/serve.py --port 8801" GENE2_BASE_URL="http://127.0.0.1:8801" \
  bash consolidated/gene2-demo-shop/run.sh --ci -m smoke
```

**Sync this run into QMetry** (creates the cycle, links the 5 smoke cases, sets each result; env
defaults to `test`, version defaults to one past the highest Build already in the project - the
first run of the day is `1.0`, the next is `1.1`, and so on, forever, with no manual bookkeeping):

```bash
python tools/qmetry_sync.py results --slug gene2-demo-shop \
  --junit consolidated/gene2-demo-shop/reports/junit.xml --run smoke-local-$(date +%Y%m%d) \
  --apply --confirm-host qtmcloud.qmetry.com
```

**In CI** (this is the real audience-facing part): push to a `gene2/**` branch, or open a PR (a PR
always runs smoke automatically - that is the whole reason smoke exists as its own tier):

```bash
git push origin gene2/initial-suite
```

Open the repo's **Actions** tab and watch the `gene2-tests` run. When it finishes:
- the job summary shows tests/failures/errors/skipped
- **QMetry sync** and **Story status** steps run automatically (they print `if:` skipped only when
  the secret is missing)
- **Allure report**: click the run -> the live link at
  `https://<your-username>.github.io/gene2-demo-shop-tests/` (only on a push, not a PR preview -
  a PR still gets the zipped artifact)

**In QMetry**: open the Jira project's QMetry tab -> Test Cycles -> the cycle printed by the sync
command (for example `SHOP-TR-23`, summary `gene2 gene2-demo-shop gh-<run id>`). Every linked case
shows the Environment and Build column you just created.

---

## 3. Functional - the standard regression tier

Same shape, different marker. Functional includes smoke (a smoke test is also functional) plus
everything else that is not `extended`, `bug`, or unmarked-slow.

```bash
GENE2_APP_START="python3 demo-app/serve.py --port 8801" GENE2_BASE_URL="http://127.0.0.1:8801" \
  bash consolidated/gene2-demo-shop/run.sh --ci -m functional
```

Two of the 39 functional tests are `@pytest.mark.bug` - known, already-filed defects that are
*expected* to fail in `--ci` mode (they are strict expected failures: the run stays green while
they fail, and turns red the day they unexpectedly pass, meaning the bug got fixed and the test
needs promoting out of `bug`). Point this out live - it is the harness proving it already knows
about that failure, not hiding it.

```bash
python tools/qmetry_sync.py results --slug gene2-demo-shop \
  --junit consolidated/gene2-demo-shop/reports/junit.xml --run functional-local-$(date +%Y%m%d) \
  --apply --confirm-host qtmcloud.qmetry.com
```

**In CI**: trigger it on demand from the Actions tab -> `gene2-tests` -> "Run workflow" -> level
`functional` (a plain push to `main`/`develop`/`gene2/**` also defaults to `functional`).

---

## 4. Extended - edge, robustness, security

3 tests: admin-page access control, a locked account's catalog access, and the review-text
boundary length. Same commands, `-m extended`:

```bash
GENE2_APP_START="python3 demo-app/serve.py --port 8801" GENE2_BASE_URL="http://127.0.0.1:8801" \
  bash consolidated/gene2-demo-shop/run.sh --ci -m extended

python tools/qmetry_sync.py results --slug gene2-demo-shop \
  --junit consolidated/gene2-demo-shop/reports/junit.xml --run extended-local-$(date +%Y%m%d) \
  --apply --confirm-host qtmcloud.qmetry.com
```

**In CI**: Actions -> "Run workflow" -> level `extended` (the nightly `schedule` trigger also runs
this tier automatically, so a scheduled run is the natural place to show it unattended).

---

## 5. Exploratory - a real session, found live, promoted for real

This tier is never faked by relabeling an existing test. The marker literally means "promoted from
an exploratory session" - so to have a real exploratory-tier test on demo day, run a real session
before or during the demo:

1. **Explore by hand or with an agent** against the running app
   (`http://127.0.0.1:8801`, credentials in `consolidated/gene2-demo-shop/config/suite-config.json`).
   Try something the generated suite would not think to try - a weird input, a double click, a
   browser-back after checkout.
2. **The moment you find something wrong**, triage it honestly:

```bash
python tools/triage.py build --slug gene2-demo-shop \
  --junit consolidated/gene2-demo-shop/reports/junit.xml --out consolidated/gene2-demo-shop/reports

python tools/triage.py set --file consolidated/gene2-demo-shop/reports/triage.json \
  --test "<the failing test's name>" --class product_bug \
  --reason "value wrong, element found, reproduces every time" \
  --module <module> --title "<expected behaviour, one line>" --severity High
```

3. **File the real bug, right now, in Jira** (this is the "must be real-time" part - the fingerprint
   makes it idempotent, so running this twice for the same bug adds a comment, never a duplicate):

```bash
python tools/jira_bug.py --slug gene2-demo-shop \
  --from-triage consolidated/gene2-demo-shop/reports/triage.json \
  --app-url http://127.0.0.1:8801
```

4. **Write the reproduction as a real test**, mark it `@pytest.mark.exploratory`, and run it so it
   shows up green-on-the-fix or red-until-fixed like any other test. Then sync it into QMetry the
   same way as the other tiers:

```bash
python tools/qmetry_sync.py results --slug gene2-demo-shop \
  --junit consolidated/gene2-demo-shop/reports/junit.xml --run exploratory-live-$(date +%Y%m%d) \
  --apply --confirm-host qtmcloud.qmetry.com
```

The point for the audience: the bug in Jira, the test in the suite, and the execution in QMetry all
reference each other, and all three were created in front of them, not pre-staged.

---

## 6. Reading the results back

**Allure, locally** (double-clicking `index.html` gives a "failed to fetch" error - browsers block
`fetch()` on `file://`; always serve it):

```bash
cd consolidated/gene2-demo-shop/reports/allure-report && python3 -m http.server 8000
```

then open `http://localhost:8000`.

**Allure, from CI**: the live link on every push -
`https://<your-username>.github.io/gene2-demo-shop-tests/` - or download the `gene2-report-<level>`
artifact from the run page for the zipped copy (PR previews only get the artifact, by design: the
app under test in a PR preview may not be the meaningful comparison).

**QMetry, latest runs**: Jira project -> QMetry tab -> Test Cycles, sorted by created date. Cycle
summaries are always `gene2 gene2-demo-shop <run id>` - a local run id is
`<tier>-local-YYYYMMDD`, a CI run id is `gh-<the Actions run number>`, so you can match a cycle
straight back to the Actions run that produced it. Each cycle's description carries the
Environment and Version it ran under.

**Stakeholder PDF** (verdict by module and requirement, failures with evidence, known bugs,
environment):

```bash
python tools/allure_pdf.py --slug gene2-demo-shop \
  --results consolidated/gene2-demo-shop/reports/allure-results --out test-report.pdf
```

**Jira story status**: one comment per story, updated in place (never a new comment per run):

```bash
python tools/story_status.py --slug gene2-demo-shop \
  --junit consolidated/gene2-demo-shop/reports/junit.xml --run <same run id you used for qmetry> \
  --apply --confirm-host <your-site>.atlassian.net
```

---

## 7. Environment and version, explained

- `--env` defaults to `test` (pass `--env staging` etc. if you want a different QMetry
  Environment; it is created automatically the first time it is used).
- `--version` defaults to auto-increment: the sync script reads the highest `N.M` Build name
  already in the QMetry project and picks the next one - `1.0` the first time ever, `1.1` the next
  run, `1.2` after that, forever. This is read from QMetry itself, not a local file, so it is
  correct on a laptop and in a fresh CI checkout alike.
- Rerunning the exact same `--run <id>` a second time (for example retrying a flaky CI step) is a
  true no-op: it finds its own cycle already exists, reads back the Environment/Version it was
  created with, and changes nothing.
- The same Environment and Version are written into the Allure report itself
  (`allure-results/environment.properties`), so the report's own "Environment" panel shows them -
  no separate lookup needed to match an Allure report to its QMetry cycle.
- To pin a specific version on purpose (for example labelling a release candidate build), pass
  `--version 2.0-rc1` explicitly; the next run with no `--version` continues from whatever you
  just used.

---

## 8. Command quick reference

| What | Local | CI |
|---|---|---|
| Smoke | `run.sh -m smoke` (headed) / `run.sh --ci -m smoke` | PR event, or Actions -> Run workflow -> `smoke` |
| Functional | `run.sh --ci -m functional` | push to main/develop/gene2/**, or Run workflow -> `functional` |
| Extended | `run.sh --ci -m extended` | nightly schedule, or Run workflow -> `extended` |
| Exploratory | manual/agentic session, then `triage.py` + `jira_bug.py --from-triage`, then mark + run the new test | same, run locally or dispatch after the test is merged |
| Sync to QMetry | `qmetry_sync.py results --slug gene2-demo-shop --junit <path> --run <id> --apply --confirm-host qtmcloud.qmetry.com` | automatic step in the workflow, only when `QMETRY_API_KEY` is set |
| Story status | `story_status.py --slug gene2-demo-shop --junit <path> --run <id> --apply --confirm-host <site>.atlassian.net` | automatic step, only when `ATLASSIAN_API_TOKEN` is set |
| Stakeholder PDF | `allure_pdf.py --slug gene2-demo-shop --results <allure-results dir> --out test-report.pdf` | automatic step |
| View Allure | `cd reports/allure-report && python3 -m http.server 8000` | live link on every push, artifact on every run |
| Clean slate | delete local `reports/`, then the QMetry/Jira clean entry point (types the host, dry run first) | never run from CI, by design |
