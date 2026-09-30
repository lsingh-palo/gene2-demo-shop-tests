---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/131250
title: Business rules: tax, shipping and promotions
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Finance and Marketing. Status: Approved. Last change: 3 September 2026
(pricing review).
This page is the single source for pricing rules. Where a Jira story and this page disagree,
this page wins (see Test strategy). Corrections are made in place: struck text is
the old rule and is kept for history only.
Order of calculation
Subtotal = the sum of price x quantity for every cart line.
Discount from the promo code (at most one discount code, REQ-PROMO-02).
Tax on the discounted subtotal (REQ-TAX, REQ-TAX-02).
Shipping for the delivery region (REQ-SHIP to REQ-SHIP-04).
Total = subtotal - discount + tax + shipping.
REQ-TAX - Sales tax
Tax is charged at 8%. 22 June 2026:
rate confirmed at 8% by Finance. Tax is rounded to the nearest cent.
REQ-TAX-02 - Tax after discounts
Tax is charged on the subtotal after discounts. Shipping is not taxed.
REQ-SHIP - Metro shipping
Metro shipping is a flat $6.50. Orders over
$75 ship free.
REQ-SHIP-02 - Regional surcharge
The Regional delivery region adds a $5.00 surcharge to the Metro fee. The free-shipping
threshold applies to the $6.50 base fee only, so a Regional order over $75 pays $5.00.
REQ-SHIP-03 - Remote shipping
The Remote delivery region never ships free: it is a flat $14.00, and FREESHIP does not
apply.
REQ-SHIP-04 - Threshold after discounts
The $75 free-shipping threshold is measured on the subtotal after discounts.
Promo codes
Code
Type
Effect
SAVE10
Discount
10% off the subtotal
WELCOME5
Discount
$5.00 off (minimum order in REQ-PROMO-03)
FREESHIP
Shipping
Free Metro or Regional base shipping
REQ-PROMO-01 - Invalid codes
An unknown or disabled code shows "This code is not valid." and changes nothing. Codes are not
case sensitive.
REQ-PROMO-02 - One discount code per order
One discount code per order. FREESHIP is not a discount code and may be combined with one of
them. A second discount code shows "Only one discount code can be used per order."
3 September 2026: changed in the pricing review; stacking is no longer allowed.
REQ-PROMO-03 - WELCOME5 minimum order
WELCOME5 needs a subtotal of $30 or more. Below that it is refused with "WELCOME5 needs a
subtotal of $30 or more."


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~10%~~
2. ~~$50~~
3. ~~Up to two discount codes may be combined;~~
4. ~~WELCOME5 applies after the percentage discount.~~
