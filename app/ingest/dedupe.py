from __future__ import annotations

import hashlib


def sha256_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ContentHashCache:
    def __init__(self) -> None:
        self._hashes: dict[str, str] = {}

    def seen(self, relative_path: str, content_hash: str) -> bool:
        return self._hashes.get(relative_path) == content_hash

    def remember(self, relative_path: str, content_hash: str) -> None:
        self._hashes[relative_path] = content_hash
