"""Modal / dialog component."""
from __future__ import annotations

from playwright.sync_api import Page, expect

T = 10_000


class Modal:
    def __init__(self, page: Page, root: str = "[role='dialog'], .modal, .ReactModal__Content"):
        self.page = page
        self.root = root

    def _m(self):
        return self.page.locator(self.root).first

    def wait_open(self, timeout: int = T) -> "Modal":
        expect(self._m()).to_be_visible(timeout=timeout)
        return self

    def title(self) -> str:
        m = self._m()
        for sel in ["h1", "h2", "h3", "[role='heading']", ".modal-title", "header"]:
            if m.locator(sel).count():
                return m.locator(sel).first.inner_text().strip()
        return ""

    def confirm(self, label: str = "OK") -> None:
        self._button(label, ["Confirm", "Yes", "Save", "Submit", "OK"])

    def cancel(self, label: str = "Cancel") -> None:
        self._button(label, ["Cancel", "No", "Close", "Dismiss"])

    def close_x(self) -> None:
        self._m().locator("[aria-label='Close'], .close, button:has-text('x')").first.click(timeout=T)

    def wait_closed(self, timeout: int = T) -> None:
        expect(self._m()).to_be_hidden(timeout=timeout)

    def _button(self, label: str, fallbacks: list[str]) -> None:
        m = self._m()
        btn = m.get_by_role("button", name=label)
        if btn.count() == 0:
            for f in fallbacks:
                cand = m.get_by_role("button", name=f)
                if cand.count():
                    btn = cand
                    break
        btn.first.click(timeout=T)
