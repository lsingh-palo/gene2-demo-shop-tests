---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/655361
title: Requirements: Roles and permissions
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product and Security. Status: Approved. Epic: Accounts and access.
Last change: 11 September 2026.
Who may do what in the shop. Login rules are on Requirements: Accounts and access
(REQ-LOCK, REQ-AUTH-01, REQ-AUTH-02); this page adds the permission matrix and the rules that
cross roles.
Permission matrix
Capability
Visitor (no session)
Customer
Locked customer
Admin
Log in page
yes
yes
refused (REQ-LOCK)
yes
Featured catalogue, All products, product detail
sent to login (REQ-AUTH-01)
yes
no
yes
Write a review
no
one per product (REQ-REVIEW-02)
no
one per product
Cart and checkout
no
yes
no
yes (REQ-ROLE-01)
Order history
no
own orders only (REQ-ROLE-02)
no
own orders only
Admin page: stock and promo codes
no
"Admins only." (REQ-AUTH-02)
no
yes
Admin link in the header
no
hidden
no
shown
REQ-ROLE-01 - Admins can shop
The admin account can use the cart, checkout and order history exactly like a customer. Its
checkout address starts filled with its saved address, 1 Depot Lane.
REQ-ROLE-02 - Own orders only
Order history lists only the orders placed by the account that is logged in. Another
account's orders are never shown, including to the admin.
REQ-ROLE-03 - Admin changes apply to every account
A stock level or a promo code switch changed on the Admin page applies to every account
from that moment, and stays in effect after the admin logs out. A customer who logs in after an
admin disabled SAVE10 sees "This code is not valid." for SAVE10.
Roles we do not have
11 September 2026: the Support role is dropped for v2.0; support staff use the admin
account for stock and promo questions only.


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~A Support role can view any customer's orders.~~
