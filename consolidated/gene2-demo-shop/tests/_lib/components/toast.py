"""Toast / snackbar / flash-message component."""
from __future__ import annotations

from playwright.sync_api import Page, expect

T = 10_000


class Toast:
    def __init__(
        self,
        page: Page,
        root: str = "[role='status'], .toast, .snackbar, .flash, .Toastify__toast, [aria-live='polite']",
    ):
        self.page = page
        self.root = root

    def _t(self):
        return self.page.locator(self.root).first

    def wait(self, timeout: int = T) -> "Toast":
        expect(self._t()).to_be_visible(timeout=timeout)
        return self

    def text(self) -> str:
        return self._t().inner_text().strip()

    def kind(self) -> str:
        cls = (self._t().get_attribute("class") or "").lower()
        for k in ("success", "error", "warning", "info", "danger"):
            if k in cls:
                return "error" if k == "danger" else k
        return "info"

    def dismiss(self) -> None:
        btn = self._t().locator("button, [aria-label='Close'], .close")
        if btn.count():
            btn.first.click(timeout=T)
