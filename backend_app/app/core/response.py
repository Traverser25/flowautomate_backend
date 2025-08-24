from typing import Any, Optional
from pydantic import BaseModel

class APIResponse(BaseModel):
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "Success"):
        return cls(message=message, data=data, error=None)

    @classmethod
    def fail(cls, error: str, message: str = "Failed"):
        return cls(message=message, data=None, error=error)
