"""FormWizard component - multi-step form. Fills the current step from a dict, steps back/next."""
from __future__ import annotations

import re

from playwright.sync_api import Page

T = 10_000


class FormWizard:
    def __init__(
        self,
        page: Page,
        step_indicator: str = ".steps li, [role='tablist'] [role='tab'], .wizard-step",
        next_btn: str = "button:has-text('Next'), [data-test='next']",
        back_btn: str = "button:has-text('Back'), button:has-text('Previous'), [data-test='back']",
        submit_btn: str = "button:has-text('Submit'), button:has-text('Finish'), button[type='submit']",
    ):
        self.page = page
        self._steps = step_indicator
        self._next = next_btn
        self._back = back_btn
        self._submit = submit_btn

    def step_count(self) -> int:
        return self.page.locator(self._steps).count()

    def current_step(self) -> int:
        steps = self.page.locator(self._steps)
        for i in range(steps.count()):
            cls = steps.nth(i).get_attribute("class") or ""
            if "active" in cls or steps.nth(i).get_attribute("aria-selected") == "true":
                return i + 1
        return 1

    def fill_step(self, values: dict[str, str]) -> None:
        for field, value in values.items():
            loc = self.page.locator(
                f"[name='{field}'], #{field}, [data-test='{field}'], "
                f"label:has-text('{field}') + input, label:has-text('{field}') input"
            ).first
            tag = (loc.evaluate("e => e.tagName") or "").lower()
            if tag == "select":
                loc.select_option(value, timeout=T)
            elif re.match(r"true|false", str(value), re.I):
                loc.set_checked(str(value).lower() == "true", timeout=T)
            else:
                loc.fill(value, timeout=T)

    def next(self) -> None:
        self.page.click(self._next, timeout=T)

    def back(self) -> None:
        self.page.click(self._back, timeout=T)

    def submit(self) -> None:
        self.page.click(self._submit, timeout=T)
