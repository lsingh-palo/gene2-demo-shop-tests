# gene2-demo-shop-tests

The Playwright + pytest suite that Gen-e2 built for the demo shop, standalone.

    consolidated/gene2-demo-shop/run.sh          # headed, one worker
    consolidated/gene2-demo-shop/run.sh --ci     # parallel, JUnit + HTML + Allure (browser visible; GENE2_HEADLESS=1 or a CI runner hides it)

`demo-app/` is the demo shop itself (v1 = current release, v2 = release candidate). GitHub Actions
(`.github/workflows/gene2-tests.yml`) starts it inside the job through `GENE2_APP_START` and runs
the suite with the same command. `tools/` holds what this suite needs to run standalone: the
optional QMetry sync and Jira story status, the stakeholder PDF, failure triage and real-time bug
filing, and the clean-slate reset for QMetry/Jira. See `DEMO-REHEARSAL.md` for the full rehearsal
procedure: smoke -> functional -> extended -> exploratory, locally and in CI, with QMetry
executions and a live Allure report on every push.
