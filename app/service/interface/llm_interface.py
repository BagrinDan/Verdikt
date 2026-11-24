from abc import ABC, abstractmethod
from app.models.responses.llm_reply import LlmReply



class LlmInterface(ABC):
    @abstractmethod
    async def chat(self, 
                   model: str,
                   messages: list[dict],
                   max_tokens: int,
                   logprobs: bool = False) -> LlmReply:
        ...
