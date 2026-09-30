---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/131228
title: Requirements: Accounts and access
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product. Status: Approved. Epic: Accounts and access.
REQ-LOCK - Locked accounts
A locked account cannot log in and sees: "This account is locked. Contact support." It cannot
reach any shop page.
REQ-AUTH-01 - Session guard
Every page other than login needs a session. Without one the visitor is sent to the login page
with the message "You must log in to view that page." Logging out clears the cart.
REQ-AUTH-02 - Admin access
Only the admin role may open the Admin page. A customer who opens it directly sees "Admins
only." and no admin controls. The Admin link in the header is shown to admins only.
Accounts in the test environments
User
Role
standard_user
Customer
locked_user
Customer, locked
admin_user
Admin


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
