"""DataTable component. Read rows/cells, sort, find a row, trigger a row action."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000


class DataTable:
    def __init__(self, page: Page, root: str = "table"):
        self.page = page
        self.root = root

    def _t(self):
        return self.page.locator(self.root).first

    def headers(self) -> list[str]:
        cells = self._t().locator("thead th, thead td, [role='columnheader']")
        return [cells.nth(i).inner_text().strip() for i in range(cells.count())]

    def row_count(self) -> int:
        return self._rows().count()

    def _rows(self):
        # browsers auto-insert <tbody>, so "tbody tr" covers markup with or without one;
        # fall back to ARIA rows for non-<table> grids
        t = self._t()
        body = t.locator("tbody tr")
        return body if body.count() else t.locator("[role='row']")

    def cell(self, row: int, col) -> str:
        """col: 0-based index, or a header name. Counts th and td so key-value tables
        (first cell a <th>) work."""
        r = self._rows().nth(row)
        if isinstance(col, str):
            col = self.headers().index(col)
        cells = r.locator("th, td, [role='cell'], [role='gridcell'], [role='columnheader'], [role='rowheader']")
        return cells.nth(col).inner_text().strip()

    def sort_by(self, column: str) -> None:
        self._t().locator("thead th, [role='columnheader']").filter(has_text=column).first.click(timeout=T)

    def find_row(self, text: str) -> int:
        rows = self._rows()
        for i in range(rows.count()):
            if text in rows.nth(i).inner_text():
                return i
        return -1

    def row_action(self, row: int, action: str) -> None:
        r = self._rows().nth(row)
        btn = r.get_by_role("button", name=action)
        if btn.count() == 0:
            btn = r.locator(f"button:has-text('{action}'), a:has-text('{action}')")
        btn.first.click(timeout=T)
