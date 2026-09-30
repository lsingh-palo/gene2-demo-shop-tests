---
source: jira 32 issue(s)
title: Jira requirements digest
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


## SHOP-7 - Log in with a customer account and refuse locked accounts  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-7>  updated 2026-09-30T10:14:54.291+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to log in with my username and password, so that I can shop with my own cart and order history.
Acceptance criteria
- Given a registered customer, when they log in with the right password, then they land on the Featured catalogue.
- Given a wrong password, when they submit, then they see "Username and password do not match." and stay on the login page.
- Given a locked account, when it logs in with the right password, then it sees "This account is locked. Contact support." and cannot reach any shop page.
Notes
Demo accounts: standard_user (customer), locked_user (locked), admin_user (admin).

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:11.953+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-7 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC003 a locked account is refused with the lockout message: passed (QMetry SHOP-TC-9)
- TC005 a locked account cannot reach the catalog: passed (QMetry SHOP-TC-18)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-8 - Redirect to login when there is no session  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-8>  updated 2026-09-24T01:51:04.455+0800

Description (may be stale - the comment thread wins):
> As the shop owner, I want every shop page to need a session, so that carts and orders are never shown to a visitor who has not logged in.
Acceptance criteria
- Given no session, when a visitor opens any page other than login, then they are sent to the login page with the message "You must log in to view that page."
- Given a session, when the customer logs out, then the cart is cleared and the next shop page needs a new login.


## SHOP-9 - Restrict the admin page to admins  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-9>  updated 2026-09-30T10:14:55.220+0800

Description (may be stale - the comment thread wins):
> As the shop owner, I want only admins to use the admin page, so that customers cannot change stock or promotions.
Acceptance criteria
- Given admin_user, when they open Admin, then they see the stock and promo controls.
- Given a customer, when they open admin.html directly, then they see "Admins only." and no controls.
- Given a customer, then the Admin link is not shown in the header.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:12.861+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-9 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 1 test(s), 1 passed, 0 failed.
- TC006 a customer cannot use the admin page: passed (QMetry SHOP-TC-21)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-10 - Search products by name  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-10>  updated 2026-09-30T10:14:40.098+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to search products by name, so that I can find an item without paging through the whole range.
Acceptance criteria
- Given All products, when I type part of a name, then only products whose name contains that text are listed.
- The match ignores case: "lamp", "LAMP" and "Lamp" all find Desk Lamp.
- Given a search with no matches (for example "zebra"), then I see "No products match." and no pager.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:48:56.309+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-10 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC040 search matches product names regardless of case: passed (QMetry SHOP-TC-34)
- TC041 a search with no matches shows the empty message: passed (QMetry SHOP-TC-35)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-11 - Filter products by category and stock  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-11>  updated 2026-09-30T10:14:41.204+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to filter by category and hide items that are out of stock, so that I only see what I can buy.
Acceptance criteria
- Given the category Kitchen, then only Kitchen products are listed.
- Given "In stock only", then products with 0 stock are hidden.
- Filters and search combine: every condition must hold (AND).
- Kitchen with In stock only returns exactly 8 products on one page.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:48:57.499+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-11 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 1 test(s), 1 passed, 0 failed.
- TC042 kitchen with in stock only lists exactly eight products on one page: passed (QMetry SHOP-TC-33)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-12 - Page through All products  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-12>  updated 2026-09-30T10:14:42.663+0800

Description (may be stale - the comment thread wins):
> As a customer, I want the full range split into pages of 8, so that the page stays quick to scan.
Acceptance criteria
- 8 products per page; the page count is the number of matches divided by 8, rounded up.
- All 18 products unfiltered = 3 pages; "Page 1 of 3" is shown.
- Paging through every page shows every matching product exactly once.
- There is no Next button on the last page and no Previous button on the first.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:48:58.539+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-12 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 1 test(s), 1 passed, 0 failed.
- TC043 every matching product appears exactly once across pages: passed (QMetry SHOP-TC-32)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-13 - Product detail page  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-13>  updated 2026-09-30T10:14:43.696+0800

Description (may be stale - the comment thread wins):
> As a customer, I want a page per product with its price, stock, description and reviews, so that I can decide before adding it to my cart.
Acceptance criteria
- The page shows name, price, category, stock status and description.
- The average rating is the mean of the review ratings, shown to one decimal ("4.7 out of 5 (3 reviews)").
- A product without reviews shows "No reviews yet".
- A quantity of 1-5 can be chosen before Add to cart.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:48:59.659+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-13 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 1 test(s), 1 passed, 0 failed.
- TC050 the average rating is shown to one decimal: passed (QMetry SHOP-TC-23)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-14 - Write a product review  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-14>  updated 2026-09-30T10:14:44.699+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to rate and review a product, so that other customers can learn from my experience.
Acceptance criteria
- A review needs a rating of 1 to 5 stars; without one I see "Choose a rating from 1 to 5 stars."
- The review text must be 10 to 500 characters; otherwise I see "Review text must be 10 to 500 characters."
- A rejected review is not saved.
- A saved review appears in the list at once and the average rating updates.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:00.784+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-14 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC060 a review without a rating is rejected: passed (QMetry SHOP-TC-31)
- TC061 review text must be 10 to 500 characters: passed (QMetry SHOP-TC-30)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-15 - Allow one review per customer per product  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-15>  updated 2026-09-30T10:14:45.616+0800

Description (may be stale - the comment thread wins):
> As the shop owner, I want each customer to review a product only once, so that ratings cannot be inflated.
Acceptance criteria
- Given I already reviewed a product, when I submit another review for it, then I see "You have already reviewed this product." and nothing is saved.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:01.806+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-15 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 1 test(s), 1 passed, 0 failed.
- TC062 a customer can review a product only once: passed (QMetry SHOP-TC-29)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-16 - Change quantities in the cart  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-16>  updated 2026-09-30T10:14:46.616+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to change the quantity of each cart line, so that I can buy more than one of an item.
Acceptance criteria
- Each line has a quantity from 1 to 5; changing it updates the line total at once.
- A line can be removed.
- The cart badge shows the total number of items (the sum of quantities) and updates immediately.
- The badge is hidden whenever the cart is empty.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:02.926+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-16 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 4 test(s), 4 passed, 0 failed.
- TC020 adding items increments the badge: passed (QMetry SHOP-TC-3)
- TC021 removing an item decrements the badge: passed (QMetry SHOP-TC-1)
- TC022 the badge is hidden when the cart is empty: passed (QMetry SHOP-TC-2)
- TC023 the badge counts quantities: passed (QMetry SHOP-TC-19)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-17 - Block out-of-stock products from the cart  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-17>  updated 2026-09-30T10:14:47.554+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to know when an item is sold out or nearly gone, so that I do not order something the shop cannot send.
Acceptance criteria
- A product with 0 stock shows "Out of stock" and its Add button is disabled, on every page that lists it and on its product page.
- A product with 1 to 3 left shows "Only N left".
- When an admin sets a product's stock to 0, the catalogue reflects it at once.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:04.381+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-17 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC070 an out-of-stock product cannot be added to the cart: passed (QMetry SHOP-TC-41)
- TC072 a product with 1 to 3 left shows only n left: passed (QMetry SHOP-TC-40)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-18 - Apply promo codes at checkout  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-18>  updated 2026-09-30T10:14:48.580+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to enter a promo code at checkout, so that I get the advertised discount.
Acceptance criteria
- SAVE10 takes 10% off the subtotal.
- WELCOME5 takes $5.00 off orders of $25.00 or more.
- FREESHIP makes shipping free (not for Remote deliveries).
- An unknown or disabled code shows "This code is not valid." and changes nothing.
- Codes are not case sensitive.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:36.078+0800 Lalit Singh: Marketing confirmed the launch codes. Discount rules and thresholds are owned by the Business rules page in Confluence (SHOP space); please check it before writing tests.
- 2026-09-29T09:49:05.391+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-18 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC082 welcome5 needs a subtotal of 30 dollars: passed (QMetry SHOP-TC-28)
- TC083 an unknown code is not valid: passed (QMetry SHOP-TC-27)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-19 - Allow only one discount code per order  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-19>  updated 2026-09-30T10:14:49.542+0800

Description (may be stale - the comment thread wins):
> As Finance, I want customers to use at most one discount code per order, so that margins stay predictable.
Acceptance criteria
- Given SAVE10 is applied, when WELCOME5 is entered, then "Only one discount code can be used per order." is shown and the discount does not change.
- FREESHIP is not a discount code: it can be combined with SAVE10 or WELCOME5.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:37.140+0800 Lalit Singh: Rule changed after the pricing review: stacking two discount codes is no longer allowed. The old rule is struck through on the Business rules page and must not be implemented.
- 2026-09-29T09:49:06.425+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-19 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC080 only one discount code applies per order: passed (QMetry SHOP-TC-26)
- TC081 freeship combines with a discount code: passed (QMetry SHOP-TC-25)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-20 - Charge tax on the discounted subtotal  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-20>  updated 2026-09-30T10:14:50.580+0800

Description (may be stale - the comment thread wins):
> As Finance, I want tax charged on what the customer actually pays for goods, so that we do not over-collect tax on discounted orders.
Acceptance criteria
- Tax is 8% of the subtotal after discounts, rounded to the nearest cent.
- Shipping is not taxed.
- Total = subtotal - discount + tax + shipping.
- Example: Desk Lamp ($42.50) with WELCOME5 = $37.50 taxable, tax $3.00.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:38.652+0800 Lalit Singh: Finance sign-off: 8% on the discounted subtotal, rounding half up to the cent. No tax on shipping.
- 2026-09-29T09:49:07.912+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-20 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 3 test(s), 3 passed, 0 failed.
- TC030 tax is 8% of the subtotal: passed (QMetry SHOP-TC-7)
- TC034 tax is rounded to the nearest cent: passed (QMetry SHOP-TC-17)
- TC037 tax is charged on the discounted subtotal: passed (QMetry SHOP-TC-20)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-21 - Choose a delivery region at checkout  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-21>  updated 2026-09-30T10:14:51.482+0800

Description (may be stale - the comment thread wins):
> As a customer outside the metro area, I want to choose my delivery region, so that I pay the right shipping for where I live.
Acceptance criteria
- Metro (the default): flat $6.50, free when the subtotal after discounts is over $75.00.
- Regional: the Metro fee plus a $5.00 surcharge; over $75.00 the customer pays the $5.00 surcharge only.
- Remote: always $14.00; FREESHIP does not apply.
- Full name is 2-60 characters and the address line is required.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:08.996+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-21 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 5 test(s), 5 passed, 0 failed.
- TC035 orders over $75 ship free: passed (QMetry SHOP-TC-16)
- TC036 orders of $75 or less pay flat shipping: passed (QMetry SHOP-TC-15)
- TC090 the regional surcharge is added to shipping: passed (QMetry SHOP-TC-37)
- TC091 remote shipping is always 14 dollars: passed (QMetry SHOP-TC-38)
- TC092 the free shipping threshold is measured after discounts: passed (QMetry SHOP-TC-36)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-22 - See my order history  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-22>  updated 2026-09-30T10:14:52.445+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to see my past orders, so that I can check what I bought and what I paid.
Acceptance criteria
- The Orders page lists my orders, newest first, with order number, date, item count, total and status "Placed".
- I only see my own orders.
- Submitting checkout more than once records one order.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:10.010+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-22 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 1 passed, 0 failed, 1 not in this run.
- TC033 double-submitting checkout records one order: not in this run (QMetry SHOP-TC-5)
- TC100 order history lists the customer's orders newest first: passed (QMetry SHOP-TC-22)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-23 - Manage stock and promo codes as admin  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-23>  updated 2026-09-30T10:14:53.335+0800

Description (may be stale - the comment thread wins):
> As the shop admin, I want to set stock levels and switch promo codes on and off, so that I can react to sell-outs and campaigns without a deployment.
Acceptance criteria
- Stock can be set from 0 to 99 per product; anything else shows "Stock must be a whole number from 0 to 99." and is not saved.
- A stock change shows in the catalogue at once.
- A disabled promo code behaves exactly like an unknown code.

Comment thread (oldest first, newest wins):
- 2026-09-29T09:49:11.046+0800 Lalit Singh: [gene2-live gene2-demo-shop story-status]
Gen-e2 automated tests for SHOP-23 (suite gene2-demo-shop). This comment is updated in place by each run.
Latest run gh-36658825518-functional on http://127.0.0.1:8801: 2 test(s), 2 passed, 0 failed.
- TC071 stock set to zero by the admin blocks adding in the catalogue: passed (QMetry SHOP-TC-39)
- TC084 a code disabled by the admin is not valid: passed (QMetry SHOP-TC-24)
QMetry cycle: gene2 gene2-demo-shop gh-36658825518-functional

## SHOP-37 - Checkout accepts an order without a postcode  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-37>  updated 2026-09-24T02:47:24.058+0800

Description (may be stale - the comment thread wins):
> Severity: Medium   Environment: Production (v1.0)
A customer can place an order with the postcode field empty. The requirement says a 6-digit postcode is required and an order must not be placed without one. Found by Customer Service: two parcels came back this week with no postcode on the label.
Steps to reproduce
- Log in as standard_user.
- Add Desk Lamp to the cart and go to Checkout.
- Enter a full name, leave Postcode empty, keep the saved address.
- Click Place order.
Expected
The order is refused with an error asking for a 6-digit postcode.
Actual
The order is placed and the confirmation page is shown.

Comment thread (oldest first, newest wins):
- 2026-09-24T02:47:24.058+0800 Lalit Singh: Gen-e2: this bug reproduced again on the latest run (Medium). Still failing. No duplicate created.

## SHOP-38 - Double-clicking Place order records two orders  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-38>  updated 2026-09-29T17:23:02.040+0800

Description (may be stale - the comment thread wins):
> Severity: High   Environment: Production (v1.0)
A quick double click on Place order creates two orders for the same cart. Finance found duplicate charges on three customer statements.
Steps to reproduce
- Log in as standard_user.
- Add Desk Lamp to the cart and go to Checkout.
- Enter a full name and the postcode 123456.
- Double-click Place order.
Expected
One order is recorded ("Orders on this account: 1").
Actual
Two orders are recorded ("Orders on this account: 2").

Comment thread (oldest first, newest wins):
- 2026-09-24T02:47:25.374+0800 Lalit Singh: Gen-e2: this bug reproduced again on the latest run (High). Still failing. No duplicate created.

## SHOP-39 - Cart badge shows an empty pill after the last item is removed  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-39>  updated 2026-09-24T01:51:40.621+0800

Description (may be stale - the comment thread wins):
> Severity: Low   Environment: Production (v1.0)
After removing the last item, the cart badge stayed on screen as an empty orange pill until the page was reloaded. Fixed in v1.0: the badge is now hidden whenever the cart is empty.
Steps to reproduce
- Add one product, then remove it from the catalogue.
Expected
The badge disappears.
Actual
An empty badge stays visible.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:55.525+0800 Lalit Singh: Verified on v1.0: the badge hides as soon as the cart is empty. Closing.

## SHOP-40 - Tax is truncated instead of rounded to the cent  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-40>  updated 2026-09-24T01:51:41.446+0800

Description (may be stale - the comment thread wins):
> Severity: Medium   Environment: Production (v1.0)
A $9.99 order showed tax of $0.79. 8% of $9.99 is $0.7992, which rounds to $0.80. The calculation cut off the extra digits instead of rounding.
Steps to reproduce
- Add Espresso Cups ($9.99) and go to Checkout.
Expected
Tax $0.80.
Actual
Tax $0.79.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:56.576+0800 Lalit Singh: Fixed and verified: tax now rounds to the nearest cent. Closing.

## SHOP-41 - Two discount codes can be applied to one order  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-41>  updated 2026-09-24T02:47:26.592+0800

Description (may be stale - the comment thread wins):
> Severity: High   Environment: Staging (v2.0 RC1)
On the v2.0 release candidate, SAVE10 and WELCOME5 can both be applied to the same order, so the customer gets 10% plus $5.00 off. Only one discount code is allowed per order.
Steps to reproduce
- Log in as standard_user.
- Add Wool Throw ($120.00) and go to Checkout.
- Apply SAVE10, then apply WELCOME5.
Expected
WELCOME5 is refused with "Only one discount code can be used per order."; discount stays $12.00.
Actual
Both codes are applied and the discount is $17.00.

Comment thread (oldest first, newest wins):
- 2026-09-24T02:47:26.592+0800 Lalit Singh: Gen-e2: this bug reproduced again on the latest run (High). Still failing. No duplicate created.

## SHOP-42 - Regional deliveries are charged the Metro shipping fee  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-42>  updated 2026-09-24T02:47:27.763+0800

Description (may be stale - the comment thread wins):
> Severity: Medium   Environment: Staging (v2.0 RC1)
On the v2.0 release candidate, choosing the Regional delivery region does not add the $5.00 surcharge.
Steps to reproduce
- Log in as standard_user.
- Add Desk Lamp ($42.50) and go to Checkout.
- Choose the delivery region Regional.
Expected
Shipping $11.50 ($6.50 + $5.00 Regional surcharge).
Actual
Shipping $6.50.

Comment thread (oldest first, newest wins):
- 2026-09-24T02:47:27.763+0800 Lalit Singh: Gen-e2: this bug reproduced again on the latest run (Medium). Still failing. No duplicate created.

## SHOP-43 - [gene2-demo-shop] search: search matches product names regardless of case  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-43>  updated 2026-09-24T02:47:29.134+0800

Description (may be stale - the comment thread wins):
> Reported by Gen-e2 test harness.
Target: gene2-demo-shop   Module: search   Severity: High
Fingerprint: gene2:gene2-demo-shop:f5d6071b32

Steps to reproduce:
1. Log in as standard_user on the v2 release candidate.
2. Open All products and search for "lamp".


Expected: Desk Lamp is listed (case-insensitive search, REQ-SEARCH-01).
Actual: v2: No products match. 'Lamp' finds it; 'lamp' and 'LAMP' do not.

Reproduction test: consolidated/gene2-demo-shop/tests/test_search.py::test_search_ignores_case (fails until fixed).


## SHOP-44 - [gene2-demo-shop] search: every matching product appears exactly once across pages  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-44>  updated 2026-09-24T02:47:30.826+0800

Description (may be stale - the comment thread wins):
> Reported by Gen-e2 test harness.
Target: gene2-demo-shop   Module: search   Severity: Medium
Fingerprint: gene2:gene2-demo-shop:1e18f5de3b

Steps to reproduce:
1. Log in as standard_user on the v2 release candidate.
2. Open All products (no filters) and walk Next through pages 1 to 3, noting every product.


Expected: 18 products across 3 pages, each exactly once (REQ-SEARCH-03).
Actual: v2: 19 cards for 18 products; page 2 repeats the last product of page 1.

Reproduction test: consolidated/gene2-demo-shop/tests/test_search.py::test_every_product_appears_once_across_pages (fails until fixed).


## SHOP-45 - [gene2-demo-shop] stock: an out-of-stock product cannot be added to the cart  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-45>  updated 2026-09-24T02:47:32.274+0800

Description (may be stale - the comment thread wins):
> Reported by Gen-e2 test harness.
Target: gene2-demo-shop   Module: stock   Severity: High
Fingerprint: gene2:gene2-demo-shop:8957b8eb87

Steps to reproduce:
1. Log in as standard_user on the v2 release candidate.
2. Open All products, search "Wall Clock" (0 in stock).
3. Open its product page.


Expected: The button is disabled and reads "Out of stock" on every list and on the product page (REQ-STOCK-01).
Actual: v2: the button reads "Add to cart" and is enabled; the product can be added with 0 stock.

Reproduction test: consolidated/gene2-demo-shop/tests/test_stock.py::test_out_of_stock_product_cannot_be_added (fails until fixed).


## SHOP-46 - [gene2-demo-shop] catalog: sorting by price low to high is numeric  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-46>  updated 2026-09-24T03:03:56.219+0800

Description (may be stale - the comment thread wins):
> Reported by Gen-e2 test harness.
Target: gene2-demo-shop   Module: catalog   Severity: Medium
Fingerprint: gene2:gene2-demo-shop:135fb86528

Steps to reproduce:
1. Log in as standard_user on the v2 release candidate.
2. On Featured, sort by Price (low to high).


Expected: Prices in numeric order: $7.50, $9.99, $18.00, $24.00, $42.50, $120.00 (REQ-SORT).
Actual: v2: sorted as text, so $120.00 comes before $18.00.

Reproduction test: consolidated/gene2-demo-shop/tests/test_catalog.py::test_price_sort_is_numeric (fails until fixed).


## SHOP-47 - [gene2-demo-shop] cart: removing an item decrements the badge  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-47>  updated 2026-09-24T03:03:57.967+0800

Description (may be stale - the comment thread wins):
> Reported by Gen-e2 test harness.
Target: gene2-demo-shop   Module: cart   Severity: Medium
Fingerprint: gene2:gene2-demo-shop:a32beacd8f

Steps to reproduce:
1. Log in as standard_user on the v2 release candidate.
2. Add Desk Lamp and Wool Throw (badge 2).
3. Remove Wool Throw.


Expected: The badge shows 1 after the remove (REQ-CART).
Actual: v2: the badge stays at 2; it also ignores a quantity lowered in the cart.

Reproduction test: consolidated/gene2-demo-shop/tests/test_cart.py::test_badge_decrements_on_remove (fails until fixed).


## SHOP-48 - [gene2-demo-shop] checkout: tax is 8% of the subtotal  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-48>  updated 2026-09-24T03:03:59.575+0800

Description (may be stale - the comment thread wins):
> Reported by Gen-e2 test harness.
Target: gene2-demo-shop   Module: checkout   Severity: High
Fingerprint: gene2:gene2-demo-shop:7422b6f65e

Steps to reproduce:
1. Log in as standard_user on the v2 release candidate.
2. Add Desk Lamp ($42.50) and open Checkout.


Expected: Tax $3.40 (8%, REQ-TAX).
Actual: v2: tax $4.25 (10%, the struck rate).

Reproduction test: consolidated/gene2-demo-shop/tests/test_checkout.py::test_tax_is_eight_percent_of_subtotal (fails until fixed).


## SHOP-49 - Show every message in the agreed wording  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-49>  updated 2026-09-25T03:55:45.737+0800

Description (may be stale - the comment thread wins):
> As a customer, I want every error message to say exactly what went wrong in plain words, so that I can fix it without calling support.
Acceptance criteria
- Every message matches the wording in the Error message catalogue (Confluence), word for word.
- A message appears next to the form that caused it, and the form keeps what I typed.
- Only one message is shown at a time; checkout checks the full name first.


## SHOP-50 - Place an order and pay on delivery  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-50>  updated 2026-09-25T03:55:47.149+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to place my order without entering card details and pay when it arrives, so that checkout is quick.
Acceptance criteria
- The checkout has no payment step and asks for no card or bank details.
- Placing an order shows "Thank you, your order is placed." with an order number like SO-1001.
- After the order the cart is empty and the promo codes are cleared.
Notes
Card payments are planned for v3.0 (REQ-PAY-02) and are not part of this story.


## SHOP-51 - Meet the accessibility baseline on every form  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-51>  updated 2026-09-25T03:55:44.270+0800

Description (may be stale - the comment thread wins):
> As a customer who uses a screen reader, I want every field to be announced by name, so that I can log in, check out and write a review without help.
Acceptance criteria
- Every form control on the login, checkout, review and admin forms has an accessible name.
- Error messages are text, not colour alone.

