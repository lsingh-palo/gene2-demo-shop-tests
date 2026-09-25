"""Pagination component."""
from __future__ import annotations

import re

from playwright.sync_api import Page

T = 10_000


class Pagination:
    def __init__(self, page: Page, root: str = "[aria-label='pagination'], .pagination, nav.pager"):
        self.page = page
        self.root = root

    def _p(self):
        return self.page.locator(self.root).first

    def next(self) -> None:
        self._click(["Next", ">", "Next page", "›"])

    def prev(self) -> None:
        self._click(["Previous", "<", "Prev", "Previous page", "‹"])

    def go_to(self, page_number: int) -> None:
        self._p().get_by_role("link", name=str(page_number)).first.click(timeout=T)

    def current(self) -> int:
        cur = self._p().locator(".active, [aria-current='page'], [aria-selected='true']")
        if cur.count():
            m = re.search(r"\d+", cur.first.inner_text())
            if m:
                return int(m.group())
        return 1

    def is_last(self) -> bool:
        nxt = self._p().get_by_role("button", name=re.compile("next", re.I))
        if nxt.count() == 0:
            nxt = self._p().locator("a:has-text('Next'), button:has-text('Next')")
        if nxt.count() == 0:
            return True
        el = nxt.first
        return el.is_disabled() or (el.get_attribute("aria-disabled") == "true")

    def _click(self, labels: list[str]) -> None:
        p = self._p()
        for lbl in labels:
            cand = p.get_by_role("link", name=lbl)
            if cand.count() == 0:
                cand = p.locator(f"a:has-text('{lbl}'), button:has-text('{lbl}')")
            if cand.count():
                cand.first.click(timeout=T)
                return
        raise AssertionError(f"pagination control not found for any of {labels}")
