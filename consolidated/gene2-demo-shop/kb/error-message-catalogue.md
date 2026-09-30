---
source: confluence ${ATLASSIAN_BASE_URL}/wiki/pages/491528
title: Error message catalogue
last_verified: 2026-09-30
review_by: 2026-12-29
parse_warnings: 0
note: current-state only. Struck-through / superseded text removed. Verify against the source before relying on any rule.
---


Owner: UX. Status: Approved. Last change: 18 September 2026.
The exact wording of every message the shop shows. Tests and support scripts use this page.
When a requirement page quotes a message, the wording here is the same.
REQ-MSG-01 - Where messages appear
A message appears next to the form that caused it, as text (never colour alone), and the form
keeps what the customer typed, except the admin stock field, which returns to the saved value.
Only one message is shown at a time. The checkout form checks in
this order: full name, postcode, address.
REQ-MSG-02 - Message catalogue
Id
Where
When
Exact text
Rule
ERR-01
Login
a shop page was opened without a session
You must log in to view that page.
REQ-AUTH-01
ERR-02
Login
username or password is empty
Username and password are required.
-
ERR-03
Login
the account is locked
This account is locked. Contact support.
REQ-LOCK
ERR-04
Login
wrong password or unknown username
Username and password do not match.
REQ-LOCK
ERR-05
Product review
the customer already reviewed this product
You have already reviewed this product.
REQ-REVIEW-02
ERR-06
Product review
no rating chosen
Choose a rating from 1 to 5 stars.
REQ-REVIEW-01
ERR-07
Product review
text shorter than 10 or longer than 500 characters
Review text must be 10 to 500 characters.
REQ-REVIEW-01
ERR-08
Checkout, promo code
unknown or disabled code
This code is not valid.
REQ-PROMO-01
ERR-09
Checkout, promo code
the same code entered twice
This code is already applied.
REQ-PROMO-01
ERR-10
Checkout, promo code
a second discount code
Only one discount code can be used per order.
REQ-PROMO-02
ERR-11
Checkout, promo code
WELCOME5 below the minimum order
WELCOME5 needs a subtotal of $30 or more.
REQ-PROMO-03
ERR-12
Checkout
full name empty
Full name is required.
REQ-ADDR-01
ERR-13
Checkout
full name shorter than 2 or longer than 60 characters
Full name must be 2 to 60 characters.
REQ-ADDR-01
ERR-14
Checkout
postcode is not 6 digits
A 6-digit postcode is required.
REQ-POSTCODE
ERR-15
Checkout
address empty
Address is required.
REQ-ADDR-01
ERR-16
Admin
stock is not a whole number from 0 to 99
Stock must be a whole number from 0 to 99.
REQ-ADMIN-01
ERR-17
Admin
a customer opens the Admin page
Admins only.
REQ-AUTH-02
REQ-MSG-03 - Empty states
Where
When
Exact text
Cart
no items
Your cart is empty.
Order history
no orders for this account
No orders yet.
All products
search and filters match nothing
No products match your search.
Product detail
no reviews for the product
No reviews yet


## Struck-through / obsolete (do NOT treat as requirements)

1. ~~Invalid promo code.~~
