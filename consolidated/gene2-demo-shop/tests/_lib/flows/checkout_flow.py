"""E-commerce checkout flow helpers. Selectors default to common patterns; override per app."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000

ADD_TO_CART = "[data-test^='add-to-cart'], button:has-text('Add to cart'), .add-to-cart"
CART_LINK = "[data-test='shopping-cart-link'], a[href*='cart'], .cart-icon"
CHECKOUT_BTN = "[data-test='checkout'], button:has-text('Checkout'), a:has-text('Checkout')"
CONTINUE_BTN = "[data-test='continue'], button:has-text('Continue'), button:has-text('Next')"
FINISH_BTN = "[data-test='finish'], button:has-text('Finish'), button:has-text('Place order')"


def add_to_cart(page: Page, item_selector: str = ADD_TO_CART, index: int = 0) -> None:
    page.locator(item_selector).nth(index).click(timeout=T)


def go_to_cart(page: Page, cart_link: str = CART_LINK) -> None:
    page.click(cart_link, timeout=T)


def checkout(page: Page, address: dict, checkout_btn: str = CHECKOUT_BTN) -> None:
    """address: {"firstName": ..., "lastName": ..., "postalCode": ...}"""
    page.click(checkout_btn, timeout=T)
    for field, value in address.items():
        loc = page.locator(
            f"[data-test='{field}'], #{field}, [name='{field}'], "
            f"[placeholder*='{field}']"
        ).first
        loc.fill(str(value), timeout=T)
    page.click(CONTINUE_BTN, timeout=T)


def place_order(page: Page, finish_btn: str = FINISH_BTN) -> None:
    page.click(finish_btn, timeout=T)
