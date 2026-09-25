"""LoginForm component. Locates and acts. Tests assert on error()/the resulting page."""
from __future__ import annotations

from playwright.sync_api import Page

T = 10_000


class LoginForm:
    def __init__(
        self,
        page: Page,
        username: str = "[data-test='username'], #username, input[name='username']",
        password: str = "[data-test='password'], #password, input[name='password']",
        submit: str = "[data-test='login-button'], button[type='submit'], #login",
        error: str = "[data-test='error'], .error, [role='alert']",
        remember: str = "#remember, [name='remember']",
    ):
        self.page = page
        self._u = username
        self._p = password
        self._submit = submit
        self._error = error
        self._remember = remember

    def login(self, username: str, password: str, remember: bool = False) -> None:
        self.page.fill(self._u, username, timeout=T)
        self.page.fill(self._p, password, timeout=T)
        if remember and self.page.locator(self._remember).count():
            self.page.check(self._remember, timeout=T)
        self.page.click(self._submit, timeout=T)

    def error(self, timeout: int = 5_000) -> str:
        """First visible error element with non-empty text (a union selector can match an
        empty wrapper or an icon before the message element)."""
        loc = self.page.locator(self._error)
        try:
            loc.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        for i in range(loc.count()):
            try:
                txt = loc.nth(i).inner_text(timeout=1_000).strip()
            except Exception:
                txt = ""
            if txt:
                return txt
        return ""

    def has_error(self, timeout: int = 3_000) -> bool:
        return bool(self.error(timeout=timeout))
