# gene2-demo-shop-tests

The Playwright + pytest suite that Gen-e2 built for the demo shop, standalone.

    consolidated/gene2-demo-shop/run.sh          # headed, one worker
    consolidated/gene2-demo-shop/run.sh --ci     # headless, parallel, JUnit + HTML + Allure

`demo-app/` is the demo shop itself (v1 = current release, v2 = release candidate). GitHub Actions
(`.github/workflows/gene2-tests.yml`) starts it inside the job through `GENE2_APP_START` and runs
the suite with the same command. `tools/` holds only what the pipeline needs for the optional
QMetry sync, the Jira story status and the stakeholder PDF.
