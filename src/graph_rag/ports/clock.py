from typing import Protocol

class ClockPort(Protocol):
    def now_iso(self) -> str:
        ...