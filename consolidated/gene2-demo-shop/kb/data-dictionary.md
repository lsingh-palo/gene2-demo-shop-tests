---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/491549
title: Data dictionary
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Engineering. Status: Approved. Last change: 12 September 2026.
The fields the shop shows and stores, with their formats and limits. Rules that use a field
are named in the last column.
Product
Field
Format and limits
Rules
Id
p1 to p18; p1 to p6 are the Featured products
-
Price
US dollars with two decimals, for example $42.50
REQ-SORT
Category
Home, Kitchen or Outdoor
REQ-SEARCH-02
Stock
whole number from 0 to 99, set by an admin
REQ-STOCK-01, REQ-ADMIN-01
Stock label
0: "Out of stock"; 1 to 3: "Only N left" (for example "Only 2 left"); 4 or more: "In stock"
REQ-STOCK-01
Cart line
Field
Format and limits
Rules
Quantity
1 to 5 per line
REQ-CART-02
Order
Field
Format and limits
Rules
Number
SO- followed by four digits, from SO-1001
REQ-CHK-01
Date
YYYY-MM-DD
REQ-CHK-03
Items
the sum of the line quantities
REQ-CHK-03
Delivery region
Metro (default), Regional or Remote
REQ-SHIP to REQ-SHIP-04
Status
Placed
REQ-CHK-03
Review
Field
Format and limits
Rules
Rating
1 to 5 stars
REQ-REVIEW-01
Text
10 to 500 characters
REQ-REVIEW-01
Author
the username; one review per product per account
REQ-REVIEW-02
Money on screen
Every amount shows a dollar sign and two decimals. A zero discount shows $0.00. Zero
shipping shows the word Free instead of an amount.


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
