"""Tiny thread-safe LRU used to skip repeat provider calls for identical input.

Common case: a message fails (provider hiccup), the user hits "resend", and the
exact same audio/text arrives again — without this that costs another API call
against an already-strained quota.

In-process only. A multi-worker deployment would need Redis here instead; the
call sites don't change, only this module.
"""
from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Any


class LRUCache:
    def __init__(self, maxsize: int):
        self.maxsize = max(0, maxsize)
        self._data: "OrderedDict[str, Any]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        if self.maxsize == 0:
            return None
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def set(self, key: str, value: Any) -> None:
        if self.maxsize == 0:
            return
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


def key_for(*parts: Any) -> str:
    """Stable cache key from any mix of bytes/str/other args."""
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, bytes):
            h.update(b"b:")
            h.update(p)
        else:
            h.update(b"s:")
            h.update(str(p).encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()
