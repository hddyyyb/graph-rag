from datetime import datetime
from zoneinfo import ZoneInfo

class SystemClock:
    def now_iso(self) -> str:
        now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
        return now


class FixedClock:
    def __init__(self, txt):
        self.content = txt

    def now_iso(self) -> str:
        return self.content
