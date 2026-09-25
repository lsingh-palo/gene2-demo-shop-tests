---
source: local evals/demo-app/requirements/shop-rules.html
title: Demo Shop - Checkout and catalogue rules
last_verified: 2026-09-24
review_by: 2026-12-23
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Demo Shop - Checkout and catalogue rules
Owner: Product. Status: Approved. This page is written the way a real Confluence
requirements page ends up after a few rounds of edits: corrections are made in place with
strikethrough, and the dated note after each one is the current rule.
REQ-TAX - Sales tax
Tax is charged on the subtotal at 8%. 22/9/26 update: rate
confirmed at 8% by Finance. Tax is rounded to the nearest cent.
REQ-SHIP - Shipping
Shipping is a flat $6.50. Orders over $75
ship free.
REQ-POSTCODE - Postcode
A 6-digit postcode is required at checkout. An order must not be placed without one.
REQ-SORT - Catalogue sorting
The catalogue can be sorted by name (A to Z, Z to A) and by price (low to high, high to low).
Price sorting is numeric.
REQ-CART - Cart badge
The cart badge shows the number of items in the cart and updates immediately on add and on remove.
The badge is hidden whenever the cart is empty.
REQ-LOCK - Locked accounts
A locked account cannot log in and sees: "This account is locked. Contact support."
REQ-ORDER - Order placement
Placing an order is idempotent: submitting the checkout form more than once records one order.


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~10%~~
2. ~~$50~~
3. ~~The badge is hidden until the first add.~~
