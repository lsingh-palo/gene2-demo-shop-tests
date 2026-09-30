---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/458754
title: Non-functional requirements
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Engineering. Status: Approved. Last change: 1 July 2026.
How well the shop must work, beyond what it does. Each rule names how it is checked.
REQ-NFR-01 - Performance
Every shop page is ready to use within 2 seconds of navigation on the test environment.
Checked by the automated suite's own timings; a page that takes longer is a defect.
REQ-NFR-02 - Accessibility baseline
Every form control has an accessible name: a visible label or an aria-label. Error and
empty-state messages are text, never colour alone.
REQ-NFR-03 - Browser support
The latest two versions of Chrome, Edge, Firefox and Safari.
1 July 2026: Internet Explorer 11 support ended. Automated checks run on
Chromium, Firefox and WebKit.
REQ-NFR-04 - Data kept in the browser
Carts, orders, reviews and admin changes are kept in the browser. A new browser profile starts
an empty shop; this is by design for the test environments and is not a defect.


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~Internet Explorer 11 is supported with a reduced layout.~~
