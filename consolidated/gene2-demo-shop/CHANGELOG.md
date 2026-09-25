# CHANGELOG - gene2-demo-shop

Append-only. Newest entry directly under this header. Never edit or remove a past entry. Written by tools/changelog.py.

## 2026-09-24T02:48:44+08:00  (functional, interactive)

- Standalone run: test_runs/gene2-demo-shop-functional-20260924-015812/
- Mode: interactive | Browsers: chromium | Workers: 1
- Audit: covered 18, repaired 0, added 23, orphan 0
- Plan: specs/plan-20260924-015812.md (approved before generation, Rule 21)
- Admission funnel: proposed 23 -> collected 23 -> stable 23 -> mutation killed 23 -> new key 23 -> reviewer accepted 23
- Added:
    login: test_customer_cannot_use_admin_page (TC006)
    cart: test_badge_counts_quantities (TC023)
    checkout: test_tax_on_discounted_subtotal (TC037)
    search: test_search_ignores_case (TC040)
    search: test_search_without_matches_shows_empty_message (TC041)
    search: test_kitchen_in_stock_fits_one_page (TC042)
    search: test_every_product_appears_once_across_pages (TC043)
    product: test_average_rating_to_one_decimal (TC050)
    review: test_review_without_rating_is_rejected (TC060)
    review: test_review_text_length_limits (TC061)
    review: test_one_review_per_customer (TC062)
    stock: test_out_of_stock_product_cannot_be_added (TC070)
    stock: test_admin_zero_stock_blocks_adding (TC071)
    stock: test_low_stock_shows_only_n_left (TC072)
    promo: test_only_one_discount_code_per_order (TC080)
    promo: test_freeship_combines_with_a_discount_code (TC081)
    promo: test_welcome5_needs_thirty_dollars (TC082)
    promo: test_unknown_code_is_not_valid (TC083)
    promo: test_code_disabled_by_admin_is_not_valid (TC084)
    shipping: test_regional_surcharge_is_added (TC090)
    shipping: test_remote_shipping_is_always_fourteen (TC091)
    shipping: test_free_shipping_threshold_after_discounts (TC092)
    orders: test_order_history_newest_first (TC100)
- Repaired: none
- Result: 39 passed, 2 failed, 2 reran  (pass rate 95%)
- Harness KPIs: acceptance rate 100%; heal success rate n/a; reruns 0; review minutes 20.2; bug true-positive rate n/a
- Bugs: SHOP-37 (Medium) an order cannot be placed without a postcode (known, commented), SHOP-38 (High) double-submitting checkout records one order (known, commented), SHOP-41 (High) only one discount code applies per order (known, commented), SHOP-42 (Medium) the regional surcharge is added to shipping (known, commented), SHOP-43 (High) search matches product names regardless of case (new), SHOP-44 (Medium) every matching product appears exactly once across pages (new), SHOP-45 (High) an out-of-stock product cannot be added to the cart (new)
- Requirements from Jira project SHOP (17 stories, 6 bugs) and Confluence space SHOP (12 pages) on the demo site; 4 struck segments dropped on the business rules page, 0 parse warnings; 14 KB files promoted after review.
- Source conflict found by reading both sources: story SHOP-18 says WELCOME5 needs $25, the Business rules page says $30; the Test strategy page gives Confluence precedence. P-037 tests $27.99 and $30.00.
- Result is on v1 (the full consolidated suite, 41 tests). The 2 failures are the existing bug reproductions (TC032, TC033).
- Reviewer (separate read-only agent run): 9 accepted, 14 accepted with note, 0 rejected. The notes are strength gaps for a follow-up run (single-line badge sum, one boundary per rule, first-poll assertions).
- Parity vs v2: REGRESSION 15 (8 defects: DB-01 x2, DB-02 x3, DB-03 x4, DB-06, DB-07, DB-08, DB-09, DB-10 x2), DIVERGENCE 0, SHARED FAILURE 2, PARITY 24.
- Bugs filed with fingerprint dedupe (jira_bug.py, label gene2-demo): 4 known issues commented, 3 new issues filed. DB-01 to DB-03 are reported by parity only.
- CI mode: GENE2_MODE=ci, 3 workers, headless: 39 passed, 2 failed, 26 s; junit + html written.
- Re-run this suite:
    (python evals/demo-app/serve.py --variant v1 --port 8801 &) ; cd consolidated/gene2-demo-shop && source ../../.global_venv/bin/activate && pytest -v --base-url http://127.0.0.1:8801

## 2026-09-23T23:12:24+08:00  (functional, interactive)

- Standalone run: test_runs/gene2-demo-shop-functional-20260923-225724/
- Mode: interactive | Browsers: chromium | Workers: 1
- Audit: covered 11, repaired 0, added 7, orphan 0
- Plan: specs/plan-20260923-225724.md (approved before generation, Rule 21)
- Admission funnel: proposed 8 -> collected 8 -> stable 8 -> mutation killed 8 -> new key 8 -> reviewer accepted 7
- Added:
    login: test_locked_account_cannot_reach_catalog (TC005)
    catalog: test_name_sort_a_to_z (TC011)
    catalog: test_name_sort_z_to_a (TC012)
    catalog: test_price_sort_high_to_low (TC013)
    checkout: test_tax_rounds_to_nearest_cent (TC034)
    checkout: test_orders_over_75_ship_free (TC035)
    checkout: test_orders_of_75_or_less_pay_flat_shipping (TC036)
- Repaired: none
- Result: 16 passed, 2 failed, 2 reran  (pass rate 89%)
- Harness KPIs: acceptance rate 88%; heal success rate n/a; reruns 0; review minutes 6.1; bug true-positive rate n/a
- Bugs: none
- Extend run: the reviewer notes from entry 1 turned into plan steps P-015..P-022 (approved as written). Covered tests untouched.
- Result is on v1. The 2 failures are the existing bug reproductions (TC032, TC033); no existing test regressed.
- Reviewer: 3 accepted, 4 accepted with note (shipping boundary unreachable at exactly $75.00 with this catalogue, twice; locked-login barrier accepts any error; name A to Z is the default sort), 1 rejected: the non-6-digit postcode repro (P-019) reuses one page, so a leftover checkout-error would let a digits-only fix pass. P-019 has no test yet.
- Parity vs v2: REGRESSION 6 (still 3 defects: DB-01 x2, DB-02 x2, DB-03 x2), DIVERGENCE 0, SHARED FAILURE 2, PARITY 10.
- Promo banner decided by the person at the plan gate: intended behaviour, no test.
- Bug a281e57eb3 (postcode) note extended: '12a' is also accepted. No new bug filed.
- Re-run this suite:
    (python evals/demo-app/serve.py --variant v1 --port 8801 &) ; cd consolidated/gene2-demo-shop && source ../../.global_venv/bin/activate && pytest -v --base-url http://127.0.0.1:8801

## 2026-09-23T18:40:17+08:00  (functional, interactive)

- Standalone run: test_runs/gene2-demo-shop-functional-20260923-184017/
- Mode: interactive | Browsers: chromium | Workers: 1
- Audit: covered 0, repaired 0, added 11, orphan 0
- Plan: specs/plan-20260923-184017.md (approved before generation, Rule 21)
- Admission funnel: proposed 17 -> collected 16 -> stable 15 -> mutation killed 14 -> new key 13 -> reviewer accepted 11
- Added:
    login: test_login_lands_on_catalog (TC001)
    login: test_login_wrong_password_shows_mismatch_error (TC002)
    login: test_locked_account_is_refused (TC003)
    login: test_catalog_requires_login (TC004)
    catalog: test_price_sort_is_numeric (TC010)
    cart: test_badge_increments_on_add (TC020)
    cart: test_badge_decrements_on_remove (TC021)
    cart: test_badge_hidden_when_cart_empty (TC022)
    checkout: test_tax_is_eight_percent_of_subtotal (TC030)
    checkout: test_postcode_is_required (TC032)
    checkout: test_double_submit_records_one_order (TC033)
- Repaired: none
- Result: 9 passed, 2 failed, 2 reran  (pass rate 82%)
- Harness KPIs: acceptance rate 65%; heal success rate n/a; reruns 0; review minutes 2.5; bug true-positive rate n/a
- Bugs: a281e57eb3 (Medium) checkout: an order cannot be placed without a postcode (REQ-POSTCODE), 72e06e2f07 (High) checkout: double-submitting checkout records two orders (REQ-ORDER)
- First build of this suite through the full v3.1 pipeline: plan gate, admission, fresh-context review, merge, parity.
- Result is on v1 (the oracle app). The 2 failures are the bug reproductions (@pytest.mark.bug); each was rerun once and failed again, so reruns_per_run is 0.
- Reviewer: 9 accepted, 2 accepted with note (TC030 rounding case missing; TC003 does not assert the login was refused), 2 rejected (observed tax duplicate; half-strength free-shipping test). P-012 has no test yet.
- Parity vs v2 (planted regressions): REGRESSION 4 (3 defects: DB-01, DB-02 x2, DB-03), DIVERGENCE 0, SHARED FAILURE 2 (the bugs), PARITY 5. See parity/parity-report.md.
- Bugs not filed in Jira (offline demo app): jira_bug.py --dry-run only, ledger in bugs.json.
- Open for a person: the promo banner alternates on every load; no requirement covers it (reviewer).
- Re-run this suite:
    (python evals/demo-app/serve.py --variant v1 --port 8801 &) ; cd consolidated/gene2-demo-shop && source ../../.global_venv/bin/activate && pytest -v --base-url http://127.0.0.1:8801
