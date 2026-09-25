"""FileUpload component - standard input[type=file] and drag-drop zones."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page

T = 10_000


class FileUpload:
    def __init__(
        self,
        page: Page,
        input_sel: str = "input[type='file']",
        dropzone_sel: str = "[data-test='dropzone'], .dropzone, .upload-area",
        file_list_sel: str = ".uploaded-files li, [data-test='file-item'], .file-list li",
    ):
        self.page = page
        self._input = input_sel
        self._zone = dropzone_sel
        self._list = file_list_sel

    def set_files(self, paths: str | list[str]) -> None:
        if isinstance(paths, str):
            paths = [paths]
        self.page.set_input_files(self._input, [str(Path(p)) for p in paths], timeout=T)

    def uploaded(self) -> list[str]:
        items = self.page.locator(self._list)
        return [items.nth(i).inner_text().strip() for i in range(items.count())]

    def remove(self, filename: str) -> None:
        row = self.page.locator(self._list).filter(has_text=filename).first
        row.locator("button, [aria-label='Remove'], .remove").first.click(timeout=T)

    def has_dropzone(self) -> bool:
        return self.page.locator(self._zone).count() > 0
