"""BasePage - the Page Object base class every generated page object subclasses.

Locate and act, with explicit timeouts and light logging. Assertions live in tests, not here.
Synchronous Playwright API only.
"""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import Page, expect

ACTION_TIMEOUT = 10_000
NAV_TIMEOUT = 60_000
ASSERT_TIMEOUT = 30_000


class BasePage:
    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url.rstrip("/")

    # navigation -------------------------------------------------------------
    def open(self, path: str = "") -> "BasePage":
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self._log(f"open {url}")
        self.page.goto(url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
        return self

    # actions --------------------------------------------------------------
    def click(self, selector: str, timeout: int = ACTION_TIMEOUT) -> None:
        self._log(f"click {selector}")
        self.page.click(selector, timeout=timeout)

    def fill(self, selector: str, value: str, timeout: int = ACTION_TIMEOUT) -> None:
        self._log(f"fill {selector}")
        self.page.fill(selector, value, timeout=timeout)

    def select(self, selector: str, value: str, timeout: int = ACTION_TIMEOUT) -> None:
        self._log(f"select {selector} = {value}")
        self.page.select_option(selector, value, timeout=timeout)

    def check(self, selector: str, timeout: int = ACTION_TIMEOUT) -> None:
        self.page.check(selector, timeout=timeout)

    def press(self, selector: str, key: str, timeout: int = ACTION_TIMEOUT) -> None:
        self.page.press(selector, key, timeout=timeout)

    # reads --------------------------------------------------------------
    def text(self, selector: str, timeout: int = ACTION_TIMEOUT) -> str:
        return self.page.locator(selector).first.inner_text(timeout=timeout)

    def value(self, selector: str, timeout: int = ACTION_TIMEOUT) -> str:
        return self.page.locator(selector).first.input_value(timeout=timeout)

    def count(self, selector: str) -> int:
        return self.page.locator(selector).count()

    def visible(self, selector: str, timeout: int = 2_000) -> bool:
        try:
            return self.page.locator(selector).first.is_visible(timeout=timeout)
        except Exception:
            return False

    # resilient locate -----------------------------------------------------
    def loc(self, primary: str, *fallbacks: str, name: str = ""):
        """Return a Locator for the first selector that resolves to a visible element.

        The primary selector is preferred. If a fallback is used, it is logged as a heal
        candidate so drift is visible rather than silently masked - the run summary reads
        reports/heal-fallbacks.log, and Rule 20 (self-healing) turns those into a repair.
        Fallbacks are optional; a page object can pass just the primary.
        """
        selectors = [primary, *fallbacks]
        for i, sel in enumerate(selectors):
            try:
                cand = self.page.locator(sel).first
                if cand.is_visible(timeout=2_000 if i == 0 else 1_000):
                    if i > 0:
                        self._heal_note(name or primary, primary, sel)
                    return cand
            except Exception:
                continue
        # nothing resolved - return the primary Locator so the caller gets the real error
        return self.page.locator(primary).first

    def _heal_note(self, what: str, primary: str, used: str) -> None:
        line = f"{os.environ.get('PYTEST_CURRENT_TEST','?').split('::')[-1]} | {what} | primary={primary} | used={used} | url={self.page.url}"
        print(f"[heal] fallback locator used: {line}")
        try:
            log = Path("reports") / "heal-fallbacks.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a") as f:
                f.write(line + "\n")
        except Exception:
            pass

    # waits --------------------------------------------------------------
    def wait_visible(self, selector: str, timeout: int = ASSERT_TIMEOUT) -> None:
        expect(self.page.locator(selector).first).to_be_visible(timeout=timeout)

    def wait_gone(self, selector: str, timeout: int = ASSERT_TIMEOUT) -> None:
        expect(self.page.locator(selector).first).to_be_hidden(timeout=timeout)

    def wait_url(self, url_or_pattern, timeout: int = ASSERT_TIMEOUT) -> None:
        expect(self.page).to_have_url(url_or_pattern, timeout=timeout)

    # evidence ---------------------------------------------------------------
    def shot(self, name: str, module: str = "page") -> Path:
        """Parallel-safe screenshot: name-browser-worker.png under reports/screenshots/{module}/."""
        browser = getattr(self.page.context.browser, "browser_type", None)
        browser_name = getattr(browser, "name", "chromium") if browser else "chromium"
        worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
        out_dir = Path("reports") / "screenshots" / module
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{name}-{browser_name}-{worker}.png"
        self.page.screenshot(path=str(path))
        return path

    # internal ---------------------------------------------------------------
    def _log(self, msg: str) -> None:
        if os.environ.get("GENE2_VERBOSE_PAGES"):
            print(f"[page] {msg}")
