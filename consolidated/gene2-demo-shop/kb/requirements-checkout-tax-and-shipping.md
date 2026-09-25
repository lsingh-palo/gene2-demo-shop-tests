---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/360451
title: Requirements: Checkout, tax and shipping
last_verified: 2026-09-24
review_by: 2026-12-23
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product. Status: Approved. Epic: Checkout, tax and shipping.
Tax, shipping fees and promotions are defined on Business rules: tax, shipping and
promotions. This page covers the checkout form and order placement.
REQ-POSTCODE - Postcode
A 6-digit postcode is required at checkout. An order must not be placed without
one.
REQ-ADDR-01 - Name and address
The full name is 2 to 60 characters. The address line is required; it starts filled from the
customer's saved address and can be changed.
REQ-ORDER - Order placement
Placing an order is idempotent: submitting the checkout form more than once records one order.
Delivery region
The customer chooses Metro (the default), Regional or Remote. The fee for each is on the
Business rules page (REQ-SHIP to REQ-SHIP-04).


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
