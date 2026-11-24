from pydantic import BaseModel


class LlmMetrics(BaseModel):
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    duration_s: float = 0.0