"""Exact full-specification cache available to every coding comparator.

No semantic similarity or task-ID lookup. A hit preserves a previously generated
program, including its errors; independent checking remains mandatory. Original
discovery, storage and verification are not free. This is prior art, not NEUMANN
novelty or unseen-task generalization.
"""
import hashlib
import json

from neumann1.code_contract import admit


def specification(task):
    data = {key: task[key] for key in ("prompt", "entry_point")}
    if any(type(value) is not str or not value for value in data.values()):
        raise ValueError("complete textual specification required")
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class ExactCodeCache:
    def __init__(self):
        self._items = {}

    def put(self, task, source):
        text = specification(task)
        admit(source, task["entry_point"])
        key = hashlib.sha256(text.encode()).hexdigest()
        item = (text, source, hashlib.sha256(source.encode()).hexdigest())
        if key in self._items and self._items[key] != item:
            raise ValueError("conflicting cache population")
        self._items[key] = item

    def get(self, task):
        text = specification(task)
        key = hashlib.sha256(text.encode()).hexdigest()
        item = self._items.get(key)
        if item is None:
            return None
        original, source, digest = item
        if original != text or hashlib.sha256(source.encode()).hexdigest() != digest:
            raise ValueError("cache identity mismatch")
        admit(source, task["entry_point"])
        return source

