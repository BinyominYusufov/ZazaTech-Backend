"""Helpers to store list[str] in a SQLite TEXT column as a JSON string.

SQLite has no array type, so `technologies` / `tags` are persisted as
`json.dumps(list)` and read back with `json.loads`.
"""

from __future__ import annotations

import json


def loads_list(value: object) -> list[str]:
    """Decode a stored value into list[str]. Tolerant of None / bad data."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return []
        return [str(item) for item in data] if isinstance(data, list) else []
    return []


def dumps_list(value: list[str] | None) -> str:
    """Encode list[str] for storage. None -> '[]'."""
    return json.dumps(list(value or []))
