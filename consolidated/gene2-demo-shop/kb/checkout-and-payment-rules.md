---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/557058
title: Checkout and payment rules
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product and Finance. Status: Approved. Epic: Checkout, tax and
shipping. Last change: 15 September 2026.
What happens when an order is placed, and how it is paid. The checkout form fields are on
Requirements: Checkout, tax and shipping (REQ-POSTCODE, REQ-ADDR-01, REQ-ORDER); prices, tax
and shipping are on Business rules: tax, shipping and promotions.
REQ-PAY-01 - Pay on delivery
Payment is collected on delivery. The checkout asks for no card or bank details and has no
payment step: Place order places the order. 15 September 2026: card payments moved to
v3.0 (REQ-PAY-02).
REQ-PAY-02 - Card payments (planned for v3.0, not built)
Status: planned. Card payments through a payment provider, with 3-D Secure.
Not part of v1.0 or v2.0 and out of scope for testing until v3.0 is planned.
REQ-CHK-01 - Order number
Each order gets a number of the form SO-1001, SO-1002 and so on, one higher for each order
placed. The confirmation page shows the number of the order just placed.
REQ-CHK-02 - After the order is placed
The customer lands on the confirmation page, which says "Thank you, your order is placed."
The cart is empty, the cart badge is hidden and any applied promo codes are cleared, so the next
order starts fresh.
REQ-CHK-03 - The order in the history
The new order appears in the customer's order history with its number, the date
(YYYY-MM-DD), the number of items (the sum of the quantities), the total including tax and
shipping, and the status "Placed".


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~Card payment is taken at checkout.~~
