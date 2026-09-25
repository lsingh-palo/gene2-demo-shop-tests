---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/98349
title: Requirements: Cart, stock and promotions
last_verified: 2026-09-24
review_by: 2026-12-23
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product. Status: Approved. Epic: Cart and promotions.
REQ-CART - Cart badge
The cart badge shows the number of items in the cart (the sum of the quantities) and updates
immediately on add, remove and quantity change. The badge is hidden whenever the cart is empty.
(Corrected 11 August 2026, see the v1.0 release notes.)
REQ-CART-02 - Quantities
Each cart line has a quantity from 1 to 5. The cart page can change the quantity or remove the
line.
REQ-STOCK-01 - Stock limits
A product with no stock cannot be added to the cart: its button is disabled and reads "Out of
stock", on every list and on its product page. A product with 1 to 3 left shows "Only N left".
Promotions
Promo codes, discount limits and thresholds are defined on
Business rules: tax, shipping and promotions (REQ-PROMO-01 to REQ-PROMO-03).


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~The badge is hidden until the first add.~~
