"""Authentication flow helpers."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000

USERNAME_INPUT = "[data-test='username'], #username, input[name='username'], input[name='email']"
PASSWORD_INPUT = "[data-test='password'], #password, input[name='password']"
SUBMIT_BTN = "[data-test='login-button'], button[type='submit'], #login, button:has-text('Log in')"
ERROR = "[data-test='error'], .error, [role='alert']"
LOGOUT_TRIGGER = "#logout_sidebar_link, a:has-text('Logout'), a:has-text('Sign out'), [data-test='logout']"
MENU_TRIGGER = "#react-burger-menu-btn, [aria-label='Menu'], .user-menu, .avatar"


def login(page: Page, base_url: str, creds: dict, path: str = "/", expect_success: bool = True) -> None:
    """creds: {"username": ..., "password": ...}"""
    page.goto(base_url.rstrip("/") + path, timeout=60_000, wait_until="domcontentloaded")
    page.fill(USERNAME_INPUT, creds["username"], timeout=T)
    page.fill(PASSWORD_INPUT, creds["password"], timeout=T)
    page.click(SUBMIT_BTN, timeout=T)
    if expect_success:
        page.wait_for_load_state("domcontentloaded")


def logout(page: Page) -> None:
    try:
        if page.locator(MENU_TRIGGER).count() and page.locator(MENU_TRIGGER).first.is_visible():
            page.click(MENU_TRIGGER, timeout=3_000)
            page.wait_for_timeout(300)
        if page.locator(LOGOUT_TRIGGER).count():
            page.click(LOGOUT_TRIGGER, timeout=3_000)
    except Exception:
        pass


def ensure_logged_in(page: Page, base_url: str, creds: dict, logged_in_marker: str) -> None:
    """logged_in_marker: a selector only present when authenticated."""
    if not page.locator(logged_in_marker).count():
        login(page, base_url, creds)
