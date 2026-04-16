from __future__ import annotations

from typing import Protocol


class DocumentLoaderPort(Protocol):
    def load_from_path(self, file_path: str) -> str:
        ...