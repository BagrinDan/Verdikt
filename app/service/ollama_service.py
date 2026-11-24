
import time
from loguru import logger
from ollama import AsyncClient


from app.models.domain.llm_metrics_base import LlmMetrics
from app.models.responses.llm_reply import LlmReply
from app.service.interface.llm_interface import LlmInterface



class OllamaService(LlmInterface):
    def __init__(
            self, 
            host: str = "http://localhost:11434", # TODO: Change 
            timeout: int = 600 
        ):
        self.client = AsyncClient(
            host=host, 
            timeout=timeout
        )

    async def chat(self, model, messages, max_tokens, logprobs=False) -> LlmReply:
        started = time.time()
        request = await self.client.chat(
            model=model,
            messages=messages,
            options={"num_predict": max_tokens, "temperature": 0, "num_ctx": 8192},
            keep_alive="30m",
            logprobs=logprobs,
            top_logprobs=20 if logprobs else None,
        )
        return LlmReply(
            text=request.message.content.strip(),
            metrics=LlmMetrics(model=model,
                               tokens_in=request.prompt_eval_count or 0,
                               tokens_out=request.eval_count or 0,
                               duration_s=round(time.time() - started, 2)),
            top_logprobs=[(t.token, t.logprob) for t in request.logprobs[0].top_logprobs] if logprobs and request.logprobs else [],
        )


# [DETELE_ME or SMOKE_TEST_ME] For a quick test 
if __name__ == "__main__":
    import asyncio

    model = "qwen2.5:0.5b"
    question = "Answer PONG"

    async def _demo():
        r = await OllamaService().chat(
            model,
            [{
              "role": "user", 
              "content": question
            }],
            max_tokens=3, logprobs=True)
        print("text:", repr(r.text))
        print("metrics:", r.metrics)
        print("top_logprobs:", r.top_logprobs[:5])

    asyncio.run(_demo())