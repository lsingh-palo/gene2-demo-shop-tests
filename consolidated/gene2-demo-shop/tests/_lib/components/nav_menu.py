"""NavMenu component - top nav, sidebar, or burger menu."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000


class NavMenu:
    def __init__(
        self,
        page: Page,
        root: str = "nav, [role='navigation'], .navbar, #menu",
        toggle: str = "[aria-label='Menu'], .burger, #react-burger-menu-btn, button.hamburger",
    ):
        self.page = page
        self.root = root
        self.toggle = toggle

    def open(self) -> "NavMenu":
        if self.page.locator(self.toggle).count() and self.page.locator(self.toggle).first.is_visible():
            self.page.click(self.toggle, timeout=T)
            self.page.wait_for_timeout(300)
        return self

    def items(self) -> list[str]:
        links = self.page.locator(self.root).first.locator("a, [role='menuitem'], button")
        return [links.nth(i).inner_text().strip() for i in range(links.count()) if links.nth(i).inner_text().strip()]

    def click_item(self, label: str) -> None:
        root = self.page.locator(self.root).first
        item = root.get_by_role("link", name=label)
        if item.count() == 0:
            item = root.locator(f"a:has-text('{label}'), [role='menuitem']:has-text('{label}')")
        item.first.click(timeout=T)

    def active(self) -> str:
        root = self.page.locator(self.root).first
        act = root.locator(".active, [aria-current='page'], [aria-selected='true']")
        return act.first.inner_text().strip() if act.count() else ""
