---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/66150
title: Requirements: Product detail and reviews
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product. Status: Approved. Epic: Product detail and reviews.
REQ-PDP-01 - Product detail and rating
The product page shows name, price, category, stock status, description, the average rating and
the reviews. The average rating is the mean of all review ratings, shown to one decimal place, for
example "4.7 out of 5 (3 reviews)". A product without reviews shows "No reviews yet".
REQ-REVIEW-01 - Review validation
A review needs a rating of 1 to 5 stars and a text of 10 to 500 characters. Otherwise the
customer sees an error and nothing is saved:
No rating: "Choose a rating from 1 to 5 stars."
Text too short or too long: "Review text must be 10 to 500 characters."
REQ-REVIEW-02 - One review per product
A customer may review a product only once. A second attempt shows "You have already reviewed
this product." and is not saved.


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
