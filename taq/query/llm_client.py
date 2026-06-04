from taq.core.config import config
from taq.core.exceptions import LLMError
from taq.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self):
        self.provider = config.llm.provider
        self.model = config.llm.model
        self.base_url = config.llm.base_url.rstrip("/")
        self.api_key = config.llm.api_key
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        if self.provider == "ollama":
            return await self._ollama(prompt, system_prompt)
        elif self.provider == "openai":
            return await self._openai(prompt, system_prompt)
        raise LLMError(f"Unknown provider: {self.provider}")

    async def _ollama(self, prompt: str, system: str) -> str:
        import httpx
        payload = {"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": self.temperature, "num_predict": self.max_tokens}}
        if system:
            payload["system"] = system
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(f"{self.base_url}/api/generate", json=payload)
                r.raise_for_status()
                return r.json().get("response", "")
        except httpx.ConnectError:
            raise LLMError(f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            raise LLMError(f"Ollama failed: {e}")

    async def _openai(self, prompt: str, system: str) -> str:
        import httpx
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(f"{self.base_url}/v1/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": msgs, "temperature": self.temperature, "max_tokens": self.max_tokens})
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise LLMError(f"OpenAI failed: {e}")


llm_client = LLMClient()
