---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/66130
title: Requirements: Catalogue and search
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: Product. Status: Approved. Epic: Catalogue and search.
The shop has two lists: Featured (6 hand-picked products, the landing page after
login) and All products (the full range of 18 products in three categories: Home,
Kitchen, Outdoor).
REQ-SORT - Sorting
Both lists can be sorted by name (A to Z, Z to A) and by price (low to high, high to low). Price
sorting is numeric: $7.50 comes before $18.00, which comes before $120.00.
REQ-SEARCH-01 - Search by name
Search matches product names. The match is a substring match and ignores case: "lamp", "LAMP"
and "Lamp" all find Desk Lamp.
REQ-SEARCH-02 - Filters
All products can be filtered by category and by "In stock only". Filters combine with the search
and with each other: a product is listed only when every condition holds.
REQ-SEARCH-03 - Pagination
All products shows 8 products per page. The number of pages is the number of matching products
divided by 8, rounded up. Paging through every page shows every matching product exactly once.
There is no Previous button on the first page and no Next button on the last.
Empty results
When nothing matches, the list shows "No products match." and no pager.


## Struck-through / obsolete (do NOT treat as requirements)

_None found on this page._
