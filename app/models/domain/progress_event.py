from typing import Optional
from pydantic import BaseModel

from app.models.domain.enums import EventStatus, Step


class ProgressEvent(BaseModel):
    step: Step 
    status: EventStatus
    message: str = ""
    current: Optional[int] = None
    total: Optional[int] = None

    @classmethod
    def active(cls, step: Step, message: str = "", **kw):
        return cls(step=step, status=EventStatus.ACTIVE, message=message, **kw)

    @classmethod
    def completed(cls, step: Step, message: str = ""):
        return cls(step=step, status=EventStatus.COMPLETED, message=message)

    @classmethod
    def error(cls, step: Step, message: str):
        return cls(step=step, status=EventStatus.ERROR, message=message)
