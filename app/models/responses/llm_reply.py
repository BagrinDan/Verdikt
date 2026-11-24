

from pydantic import BaseModel
from app.models.domain.llm_metrics_base import LlmMetrics



class LlmReply(BaseModel):
    text: str
    metrics: LlmMetrics
    top_logprobs: list[tuple[str, float]] = []