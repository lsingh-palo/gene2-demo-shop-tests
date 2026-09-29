#!/usr/bin/env python3
"""Per-suite ledger of every bug the harness filed, and how it turned out.

The true-positive rate of filed bugs is the KPI that tells you whether the harness's triage can
be trusted - and it is only knowable later, when a filed bug is fixed (true positive) or closed
as "not a bug" (false positive). This ledger is where that later outcome lands.

`consolidated/{slug}/bugs.json`:
    {"bugs": [{"bugkey": "3f9a...", "title": "...", "module": "cart", "jira": "ABC-12",
               "status": "open|fixed|confirmed|rejected", "filed": "...", "updated": "...",
               "note": "..."}]}

jira_bug.py records "open" on file and "fixed" on --resolve. A person marks the rest:
    python tools/bug_ledger.py mark --slug app-example-com --bugkey 3f9a... --status rejected \\
        --note "product decision, working as intended"
    python tools/bug_ledger.py rate --slug app-example-com
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

STATUSES = ("open", "fixed", "confirmed", "rejected")
TRUE_POSITIVE = {"fixed", "confirmed"}


def path_for(slug: str, root: str = "consolidated") -> pathlib.Path:
    return pathlib.Path(root) / slug / "bugs.json"


def load(slug: str, root: str = "consolidated") -> dict:
    p = path_for(slug, root)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"bugs": []}


def record(slug: str, bugkey: str, status: str, root: str = "consolidated", **fields) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    data = load(slug, root)
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
    entry = next((b for b in data["bugs"] if b["bugkey"] == bugkey), None)
    if entry is None:
        entry = {"bugkey": bugkey, "filed": now}
        data["bugs"].append(entry)
    entry.update({k: v for k, v in fields.items() if v is not None})
    entry["status"] = status
    entry["updated"] = now
    p = path_for(slug, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return entry


def true_positive_rate(slug: str, root: str = "consolidated") -> float | None:
    """Among bugs with a known outcome, the share that were real. None until any has resolved."""
    decided = [b for b in load(slug, root)["bugs"] if b.get("status") != "open"]
    if not decided:
        return None
    return round(sum(1 for b in decided if b["status"] in TRUE_POSITIVE) / len(decided), 3)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mark")
    m.add_argument("--slug", required=True)
    m.add_argument("--bugkey", required=True)
    m.add_argument("--status", required=True, choices=STATUSES)
    m.add_argument("--note")
    r = sub.add_parser("rate")
    r.add_argument("--slug", required=True)
    a = p.parse_args(argv)
    if a.cmd == "mark":
        e = record(a.slug, a.bugkey, a.status, note=a.note)
        print(f"{e['bugkey']}: {e['status']}")
        return 0
    rate = true_positive_rate(a.slug)
    print("n/a (no filed bug has a known outcome yet)" if rate is None else f"{rate:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
