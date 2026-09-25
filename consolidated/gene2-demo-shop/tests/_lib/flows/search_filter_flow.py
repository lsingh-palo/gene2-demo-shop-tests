"""Search and filter flow helpers."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000

SEARCH_INPUT = "[type='search'], [name='q'], [name='search'], [data-test='search'], input[placeholder*='earch']"
RESULT_ITEM = "[data-test='result'], .result, .search-result, .product, li.item"


def search(page: Page, term: str, search_input: str = SEARCH_INPUT) -> None:
    page.fill(search_input, term, timeout=T)
    page.press(search_input, "Enter", timeout=T)
    page.wait_for_load_state("networkidle", timeout=15_000)


def apply_filter(page: Page, name: str, value: str) -> None:
    control = page.locator(
        f"select[name='{name}'], [data-test='{name}'], [aria-label='{name}'], "
        f"select#{name}"
    ).first
    tag = (control.evaluate("e => e.tagName") or "").lower()
    if tag == "select":
        control.select_option(value, timeout=T)
    else:
        page.get_by_label(name).first.fill(value, timeout=T)
    page.wait_for_load_state("networkidle", timeout=15_000)


def clear_filters(page: Page) -> None:
    btn = page.get_by_role("button", name="Clear filters")
    if btn.count() == 0:
        btn = page.locator("button:has-text('Clear'), a:has-text('Reset')")
    if btn.count():
        btn.first.click(timeout=T)
        page.wait_for_load_state("networkidle", timeout=15_000)


def result_count(page: Page, result_item: str = RESULT_ITEM) -> int:
    return page.locator(result_item).count()
