# gene2-demo-shop-tests

The Playwright + pytest suite that Gen-e2 built for the demo shop, standalone.

    consolidated/gene2-demo-shop/run.sh          # headed, one worker, slowed so it can be watched
    consolidated/gene2-demo-shop/run.sh --ci     # parallel, JUnit + HTML + Allure (browser visible; GENE2_HEADLESS=1 or a CI runner hides it)

`demo-app/` is the demo shop itself (v1 = current release, v2 = release candidate). GitHub Actions
(`.github/workflows/gene2-tests.yml`) starts it inside the job through `GENE2_APP_START` and runs
the suite with the same command. `tools/` holds what this suite needs to run standalone: the
optional QMetry sync and Jira story status, the stakeholder PDF, failure triage and real-time bug
filing, and the clean-slate reset for QMetry/Jira. See `DEMO-REHEARSAL.md` for the full rehearsal
procedure: smoke -> functional -> extended -> exploratory, locally and in CI, with QMetry
executions and a live Allure report on every push.

## Results

| What | Where |
|---|---|
| Live Allure report (the latest run on main) | https://lsingh-palo.github.io/gene2-demo-shop-tests/ |
| Stakeholder PDF of that run | https://lsingh-palo.github.io/gene2-demo-shop-tests/test-report.pdf |
| Run report of that run (failures, reasons, bugs) | https://lsingh-palo.github.io/gene2-demo-shop-tests/run-report.md |
| Pipeline runs | https://github.com/lsingh-palo/gene2-demo-shop-tests/actions |
| Bugs filed by the runs | https://gene2-demo.atlassian.net/issues/?jql=labels%20%3D%20%22gene2-suite-gene2-demo-shop%22 |
| QMetry test cycles | Jira project SHOP -> Apps -> QMetry -> Test Cycles |

Each run's page on GitHub starts with "Open the Allure report for this run". A run started by a pull
request does not publish a live report; its zipped Allure report is under Artifacts on that page.
