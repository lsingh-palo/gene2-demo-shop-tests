# Observations - gene2-demo-shop

Append-only. One dated block per run: what the harness learned about this app. Observations,
not requirements: the requirements are in `demo-shop-checkout-and-catalogue-rules.md`. See
`.github/harness/knowledge/evolving-knowledge.md`.

## 2026-09-23T18:40:17+08:00  (functional run gene2-demo-shop-functional-20260923-184017)

- **Stable locators:** every interactive element carries a `data-test` attribute. Prefer it.
  `[data-test='add-<pid>']` / `[data-test='remove-<pid>']` (product ids `p1`..`p6`),
  `[data-test='cart-badge']`, `[data-test='sort']` (option `price-asc`),
  `[data-test='product-price']`, `[data-test='product-list']`, `[data-test='full-name']`,
  `[data-test='postcode']`, `[data-test='place-order']`, `[data-test='checkout-error']`,
  `[data-test='tax']`, `[data-test='order-count']`, `[data-test='error']` (login page).
- **Error-state text:** locked user -> "This account is locked. Contact support."; bad password ->
  "Username and password do not match."; catalog without login -> redirect to
  `index.html?error=login-required` with "You must log in to view that page."; checkout with no
  full name -> `checkout-error` "Full name is required." (so the locator is real even though the
  postcode check is missing).
- **Order count is per session:** `order-count` on the confirmation page counts orders in this
  browser session, so "1" is the right oracle in a fresh context. A single click records 1; a
  double-click records 2 (bug, REQ-ORDER).
- **Postcode is not validated at all:** empty and non-6-digit values ("12a", seen live by the
  reviewer) are both accepted (bug, REQ-POSTCODE). The current repro covers only the empty case.
- **Promo banner alternates:** `/promo.json` returns true / false on alternate requests, so the
  catalog banner shows on about half of fresh loads (3 of 6 in the review). It is not an
  environment flake and no requirement covers it; a person should decide whether it is a product
  issue. Do not write a test that asserts the banner until that is decided.
- **Only one checkout subtotal was exercised ($42.50, Desk Lamp `p2`):** 8% of it is exactly
  $3.40, so tax rounding is untested. $9.99 -> $0.80 is a rounding case.
- **Requirements page:** served at `/requirements.html`; it contains struck rules (10% tax, $50
  free shipping, "hidden until the first add") that are NOT current.
- **Test users:** `standard_user`, `locked_user`, both password `demo_pass` (local demo app only).

## 2026-09-23T23:12:24+08:00  (functional extend run gene2-demo-shop-functional-20260923-225724)

- **Promo banner: decided.** The person ruled at the plan gate that the alternating banner is
  intended behaviour. No test asserts it; the open question above is closed.
- **Default sort is name A to Z.** The grid renders A to Z before any selection, so a test that
  selects `name-asc` passes on its first poll whether or not selecting works. To prove the action,
  select another sort first (reviewer, TC011).
- **`checkout-error` is never cleared on resubmit**, and a placed order navigates to confirmation
  about 150 ms after the click. A test that submits twice on one page can pass on a leftover error
  and on a URL check made before the navigation. Use a fresh checkout per case and assert the error
  is hidden before submitting (reviewer, rejected P-019).
- **Cart state is in `localStorage`** (`demo_cart`), so it survives `page.goto` between catalog and
  checkout within one test; each test gets a fresh browser context.
- **Each product can be added once**, so no cart totals exactly $75.00. The closest totals are
  $74.00 (Lamp + Planter + Notebook) and $76.49 (Lamp + Planter + Cups): the REQ-SHIP boundary
  itself is not reachable with this catalogue.
