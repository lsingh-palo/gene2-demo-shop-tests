---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/66171
title: Requirements: Orders and admin
last_verified: 2026-09-24
review_by: 2026-12-23
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product. Status: Approved. Epic: Orders and admin.
REQ-ORDER-02 - Order history
The Orders page lists the signed-in customer's own orders, newest first, with order number,
date, number of items, total and status. A new order has the status "Placed". With no orders the
page shows "No orders yet."
REQ-ADMIN-01 - Stock management
The admin can set each product's stock to a whole number from 0 to 99. Anything else shows
"Stock must be a whole number from 0 to 99." and is not saved. The catalogue reflects a change at
once.
REQ-ADMIN-02 - Promo code switch
The admin can enable or disable each promo code. A disabled code behaves exactly like an
unknown code (REQ-PROMO-01).


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
