from abc import BaseModel

from app.models.domain.enums import StageStatus
from app.models.domain.enums import Step



class StageMetrics(BaseModel):
    stage: Step
    status: StageStatus
    duration_s: float
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    summary: str = ""


