#!/usr/bin/env python3
"""The Jira Cloud REST v3 calls that `gene2 stories` and `gene2 clean` use, in one small client.

Every call is in the Jira Cloud platform REST v3 spec (checked 2026-09-25): search/jql, issue
comments (get, add, update, delete), delete issue. Credentials only through tools/_secrets.py.
Tests pass a fake with the same methods, so nothing here is called without a site.
"""
from __future__ import annotations

import urllib.parse


def host_of(url: str) -> str:
    return (urllib.parse.urlparse(url or "").hostname or "").lower()


def adf(text: str) -> dict:
    return {"type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": line}] if line else []}
                        for line in text.splitlines() or [text]]}


def adf_text(node) -> str:
    """Plain text of an ADF document: one line per paragraph."""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    parts = [adf_text(c) for c in node.get("content", [])]
    sep = "\n" if node.get("type") == "doc" else ""
    return sep.join(parts)


class JiraClient:
    def __init__(self):
        import requests
        import _secrets
        self.base, auth = _secrets.atlassian()
        self.s = requests.Session()
        self.s.auth = auth
        self.s.headers.update({"Accept": "application/json"})

    def _req(self, method, path, **kw):
        r = self.s.request(method, self.base + path, timeout=30, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.text.strip() else {}

    def search(self, jql: str, fields: str = "summary,labels") -> list[dict]:
        out, token = [], None
        while True:
            params = {"jql": jql, "fields": fields, "maxResults": 100, **({"nextPageToken": token} if token else {})}
            d = self._req("GET", "/rest/api/3/search/jql", params=params)
            out += d.get("issues", [])
            token = d.get("nextPageToken")
            if not token or d.get("isLast", True):
                return out

    def comments(self, key: str) -> list[dict]:
        out, start = [], 0
        while True:
            d = self._req("GET", f"/rest/api/3/issue/{key}/comment", params={"startAt": start, "maxResults": 100})
            out += d.get("comments", [])
            start += len(d.get("comments", []))
            if start >= d.get("total", 0) or not d.get("comments"):
                return out

    def add_comment(self, key: str, text: str) -> None:
        self._req("POST", f"/rest/api/3/issue/{key}/comment", json={"body": adf(text)})

    def update_comment(self, key: str, cid: str, text: str) -> None:
        self._req("PUT", f"/rest/api/3/issue/{key}/comment/{cid}", json={"body": adf(text)})

    def delete_comment(self, key: str, cid: str) -> None:
        self._req("DELETE", f"/rest/api/3/issue/{key}/comment/{cid}")

    def delete_issue(self, key: str) -> None:
        self._req("DELETE", f"/rest/api/3/issue/{key}")
