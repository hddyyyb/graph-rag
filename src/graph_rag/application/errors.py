from __future__ import annotations

class QueryExecutionError(RuntimeError):
    def __init__(self, stage: str, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.stage = stage
        self.cause = cause
    

