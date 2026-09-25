"""Generic CRUD flow helpers. The caller passes a selector map for the entity."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000

# selectors: {
#   "list_url": "/items",
#   "new_button": "a:has-text('New')",
#   "form_fields": {"name": "#name", "price": "#price"},
#   "save_button": "button:has-text('Save')",
#   "row_by_text": "table tbody tr",     # rows; matched by text
#   "edit_action": "Edit",
#   "delete_action": "Delete",
#   "confirm_delete": "button:has-text('Confirm')",
# }


def _goto_list(page: Page, base_url: str, selectors: dict) -> None:
    page.goto(base_url.rstrip("/") + selectors["list_url"], timeout=60_000, wait_until="domcontentloaded")


def create(page: Page, base_url: str, selectors: dict, data: dict) -> None:
    _goto_list(page, base_url, selectors)
    page.click(selectors["new_button"], timeout=T)
    for field, value in data.items():
        page.fill(selectors["form_fields"][field], str(value), timeout=T)
    page.click(selectors["save_button"], timeout=T)


def read(page: Page, base_url: str, selectors: dict, match_text: str) -> str:
    _goto_list(page, base_url, selectors)
    row = page.locator(selectors["row_by_text"]).filter(has_text=match_text).first
    return row.inner_text().strip()


def update(page: Page, base_url: str, selectors: dict, match_text: str, data: dict) -> None:
    _goto_list(page, base_url, selectors)
    row = page.locator(selectors["row_by_text"]).filter(has_text=match_text).first
    row.get_by_role("button", name=selectors.get("edit_action", "Edit")).first.click(timeout=T)
    for field, value in data.items():
        page.fill(selectors["form_fields"][field], str(value), timeout=T)
    page.click(selectors["save_button"], timeout=T)


def delete(page: Page, base_url: str, selectors: dict, match_text: str) -> None:
    _goto_list(page, base_url, selectors)
    row = page.locator(selectors["row_by_text"]).filter(has_text=match_text).first
    row.get_by_role("button", name=selectors.get("delete_action", "Delete")).first.click(timeout=T)
    if selectors.get("confirm_delete"):
        page.click(selectors["confirm_delete"], timeout=T)


def exists(page: Page, base_url: str, selectors: dict, match_text: str) -> bool:
    _goto_list(page, base_url, selectors)
    return page.locator(selectors["row_by_text"]).filter(has_text=match_text).count() > 0
