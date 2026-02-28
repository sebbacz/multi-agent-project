import os
from typing import Protocol
from openai import AsyncOpenAI

class LLMClient(Protocol):
    mode_name: str
    async def generate(self, system: str, user: str) -> str: ...

class RuleBasedLLM:
    mode_name = "rule_based"
    async def generate(self, system: str, user: str) -> str:
        raise RuntimeError("RuleBasedLLM should not be called for generation.")

class OpenAIResponsesLLM:
    mode_name = "openai_responses"

    def __init__(self, model: str):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    async def generate(self, system: str, user: str) -> str:
        # Responses API (recommended)
        resp = await self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        return resp.output_text

def build_llm_client():
    model = os.getenv("OPENAI_MODEL", "gpt-5.2-mini") #model choice
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIResponsesLLM(model=model)
    return RuleBasedLLM()
