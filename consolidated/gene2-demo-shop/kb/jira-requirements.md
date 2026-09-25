---
source: jira 23 issue(s)
title: Jira requirements digest
last_verified: 2026-09-24
review_by: 2026-12-23
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


## SHOP-7 - Log in with a customer account and refuse locked accounts  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-7>  updated 2026-09-24T01:51:03.737+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to log in with my username and password, so that I can shop with my own cart and order history.
Acceptance criteria
- Given a registered customer, when they log in with the right password, then they land on the Featured catalogue.
- Given a wrong password, when they submit, then they see "Username and password do not match." and stay on the login page.
- Given a locked account, when it logs in with the right password, then it sees "This account is locked. Contact support." and cannot reach any shop page.
Notes
Demo accounts: standard_user (customer), locked_user (locked), admin_user (admin).


## SHOP-8 - Redirect to login when there is no session  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-8>  updated 2026-09-24T01:51:04.455+0800

Description (may be stale - the comment thread wins):
> As the shop owner, I want every shop page to need a session, so that carts and orders are never shown to a visitor who has not logged in.
Acceptance criteria
- Given no session, when a visitor opens any page other than login, then they are sent to the login page with the message "You must log in to view that page."
- Given a session, when the customer logs out, then the cart is cleared and the next shop page needs a new login.


## SHOP-9 - Restrict the admin page to admins  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-9>  updated 2026-09-24T01:51:05.161+0800

Description (may be stale - the comment thread wins):
> As the shop owner, I want only admins to use the admin page, so that customers cannot change stock or promotions.
Acceptance criteria
- Given admin_user, when they open Admin, then they see the stock and promo controls.
- Given a customer, when they open admin.html directly, then they see "Admins only." and no controls.
- Given a customer, then the Admin link is not shown in the header.


## SHOP-10 - Search products by name  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-10>  updated 2026-09-24T01:51:14.704+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to search products by name, so that I can find an item without paging through the whole range.
Acceptance criteria
- Given All products, when I type part of a name, then only products whose name contains that text are listed.
- The match ignores case: "lamp", "LAMP" and "Lamp" all find Desk Lamp.
- Given a search with no matches (for example "zebra"), then I see "No products match." and no pager.


## SHOP-11 - Filter products by category and stock  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-11>  updated 2026-09-24T01:51:16.053+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to filter by category and hide items that are out of stock, so that I only see what I can buy.
Acceptance criteria
- Given the category Kitchen, then only Kitchen products are listed.
- Given "In stock only", then products with 0 stock are hidden.
- Filters and search combine: every condition must hold (AND).
- Kitchen with In stock only returns exactly 8 products on one page.


## SHOP-12 - Page through All products  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-12>  updated 2026-09-24T01:51:17.593+0800

Description (may be stale - the comment thread wins):
> As a customer, I want the full range split into pages of 8, so that the page stays quick to scan.
Acceptance criteria
- 8 products per page; the page count is the number of matches divided by 8, rounded up.
- All 18 products unfiltered = 3 pages; "Page 1 of 3" is shown.
- Paging through every page shows every matching product exactly once.
- There is no Next button on the last page and no Previous button on the first.


## SHOP-13 - Product detail page  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-13>  updated 2026-09-24T01:51:18.903+0800

Description (may be stale - the comment thread wins):
> As a customer, I want a page per product with its price, stock, description and reviews, so that I can decide before adding it to my cart.
Acceptance criteria
- The page shows name, price, category, stock status and description.
- The average rating is the mean of the review ratings, shown to one decimal ("4.7 out of 5 (3 reviews)").
- A product without reviews shows "No reviews yet".
- A quantity of 1-5 can be chosen before Add to cart.


## SHOP-14 - Write a product review  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-14>  updated 2026-09-24T01:51:19.563+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to rate and review a product, so that other customers can learn from my experience.
Acceptance criteria
- A review needs a rating of 1 to 5 stars; without one I see "Choose a rating from 1 to 5 stars."
- The review text must be 10 to 500 characters; otherwise I see "Review text must be 10 to 500 characters."
- A rejected review is not saved.
- A saved review appears in the list at once and the average rating updates.


## SHOP-15 - Allow one review per customer per product  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-15>  updated 2026-09-24T01:51:20.246+0800

Description (may be stale - the comment thread wins):
> As the shop owner, I want each customer to review a product only once, so that ratings cannot be inflated.
Acceptance criteria
- Given I already reviewed a product, when I submit another review for it, then I see "You have already reviewed this product." and nothing is saved.


## SHOP-16 - Change quantities in the cart  (Done)
<${ATLASSIAN_BASE_URL}/browse/SHOP-16>  updated 2026-09-24T01:51:05.860+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to change the quantity of each cart line, so that I can buy more than one of an item.
Acceptance criteria
- Each line has a quantity from 1 to 5; changing it updates the line total at once.
- A line can be removed.
- The cart badge shows the total number of items (the sum of quantities) and updates immediately.
- The badge is hidden whenever the cart is empty.


## SHOP-17 - Block out-of-stock products from the cart  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-17>  updated 2026-09-24T01:51:21.671+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to know when an item is sold out or nearly gone, so that I do not order something the shop cannot send.
Acceptance criteria
- A product with 0 stock shows "Out of stock" and its Add button is disabled, on every page that lists it and on its product page.
- A product with 1 to 3 left shows "Only N left".
- When an admin sets a product's stock to 0, the catalogue reflects it at once.


## SHOP-18 - Apply promo codes at checkout  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-18>  updated 2026-09-24T01:51:23.087+0800

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

## SHOP-19 - Allow only one discount code per order  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-19>  updated 2026-09-24T01:51:24.607+0800

Description (may be stale - the comment thread wins):
> As Finance, I want customers to use at most one discount code per order, so that margins stay predictable.
Acceptance criteria
- Given SAVE10 is applied, when WELCOME5 is entered, then "Only one discount code can be used per order." is shown and the discount does not change.
- FREESHIP is not a discount code: it can be combined with SAVE10 or WELCOME5.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:37.140+0800 Lalit Singh: Rule changed after the pricing review: stacking two discount codes is no longer allowed. The old rule is struck through on the Business rules page and must not be implemented.

## SHOP-20 - Charge tax on the discounted subtotal  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-20>  updated 2026-09-24T01:51:29.599+0800

Description (may be stale - the comment thread wins):
> As Finance, I want tax charged on what the customer actually pays for goods, so that we do not over-collect tax on discounted orders.
Acceptance criteria
- Tax is 8% of the subtotal after discounts, rounded to the nearest cent.
- Shipping is not taxed.
- Total = subtotal - discount + tax + shipping.
- Example: Desk Lamp ($42.50) with WELCOME5 = $37.50 taxable, tax $3.00.

Comment thread (oldest first, newest wins):
- 2026-09-24T01:50:38.652+0800 Lalit Singh: Finance sign-off: 8% on the discounted subtotal, rounding half up to the cent. No tax on shipping.

## SHOP-21 - Choose a delivery region at checkout  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-21>  updated 2026-09-24T01:51:31.464+0800

Description (may be stale - the comment thread wins):
> As a customer outside the metro area, I want to choose my delivery region, so that I pay the right shipping for where I live.
Acceptance criteria
- Metro (the default): flat $6.50, free when the subtotal after discounts is over $75.00.
- Regional: the Metro fee plus a $5.00 surcharge; over $75.00 the customer pays the $5.00 surcharge only.
- Remote: always $14.00; FREESHIP does not apply.
- Full name is 2-60 characters and the address line is required.


## SHOP-22 - See my order history  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-22>  updated 2026-09-24T01:51:32.156+0800

Description (may be stale - the comment thread wins):
> As a customer, I want to see my past orders, so that I can check what I bought and what I paid.
Acceptance criteria
- The Orders page lists my orders, newest first, with order number, date, item count, total and status "Placed".
- I only see my own orders.
- Submitting checkout more than once records one order.


## SHOP-23 - Manage stock and promo codes as admin  (In Progress)
<${ATLASSIAN_BASE_URL}/browse/SHOP-23>  updated 2026-09-24T01:51:32.828+0800

Description (may be stale - the comment thread wins):
> As the shop admin, I want to set stock levels and switch promo codes on and off, so that I can react to sell-outs and campaigns without a deployment.
Acceptance criteria
- Stock can be set from 0 to 99 per product; anything else shows "Stock must be a whole number from 0 to 99." and is not saved.
- A stock change shows in the catalogue at once.
- A disabled promo code behaves exactly like an unknown code.


## SHOP-37 - Checkout accepts an order without a postcode  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-37>  updated 2026-09-24T01:50:58.386+0800

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


## SHOP-38 - Double-clicking Place order records two orders  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-38>  updated 2026-09-24T01:50:58.876+0800

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
<${ATLASSIAN_BASE_URL}/browse/SHOP-41>  updated 2026-09-24T01:51:00.401+0800

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


## SHOP-42 - Regional deliveries are charged the Metro shipping fee  (To Do)
<${ATLASSIAN_BASE_URL}/browse/SHOP-42>  updated 2026-09-24T01:51:00.869+0800

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

