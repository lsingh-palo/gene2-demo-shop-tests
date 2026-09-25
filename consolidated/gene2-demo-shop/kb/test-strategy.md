---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/98369
title: Test strategy
last_verified: 2026-09-24
review_by: 2026-12-23
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: QA. Status: Approved. Applies to release v2.0.
Scope
All six modules of the Demo Shop web application (see Demo Shop product requirements). Out of
scope: payment providers, email, performance and load.
Sources of truth
Confluence requirement pages are the source of truth for rules. The Business rules page
takes precedence over Jira story acceptance criteria when they disagree; the story is then
corrected.
Struck-through text on any page is history, never a requirement.
Every test cites the requirement id it checks.
Test levels
UI functional tests (Playwright, pytest) per module, generated from a reviewed test plan.
Bug reproduction tests: one per confirmed bug; they fail until the bug is fixed.
Exploratory sessions, time-boxed, for flows the rules do not cover (for example double
submits).
Environments
Build
Role
v1 (reference)
The signed-off behaviour. The oracle for parity.
v2 (release candidate)
The re-platformed build under test.
Parity approach (v1 vs v2)
The same suite runs against both builds. A test that passes on v1 and fails on v2 is a
regression; a test that fails on both is a shared failure (a known
production bug); a test that passes on both is parity.
Entry criteria
Stories are In QA with their requirement ids labelled.
The release candidate is deployed and the smoke tests pass.
Exit criteria
No open High or Critical regression against v1.
Every requirement id in scope has at least one passing test, or a linked open bug.
The suite runs headless in CI with JUnit and HTML reports.
Defects
Bugs are raised in Jira project SHOP with steps, expected and actual results, severity and
environment, and linked to their story. Automated runs do not raise duplicates: a bug that is
already open gets a comment instead.


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
