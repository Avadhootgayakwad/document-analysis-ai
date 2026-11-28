import json

import httpx

from app.core.config import settings


class LLMServiceError(Exception):
    pass


class LLMService:

    def __init__(self):

        self.base_url = settings.LM_STUDIO_BASE_URL.rstrip("/")
        self.configured_model = settings.LM_STUDIO_MODEL

        self.timeout = httpx.Timeout(
            180.0,
            connect=10.0
        )

    async def get_models(self):

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.get(
                    f"{self.base_url}/models"
                )

                response.raise_for_status()

                return response.json().get("data", [])

        except httpx.HTTPError as error:

            raise LLMServiceError(
                "Unable to connect to LM Studio."
            ) from error

    async def resolve_model(self):

        if self.configured_model.lower() != "auto":
            return self.configured_model

        models = await self.get_models()

        available = [
            model["id"]
            for model in models
            if model.get("id")
            and "embedding" not in model["id"].lower()
        ]

        if not available:

            raise LLMServiceError(
                "No chat model is available in LM Studio."
            )

        return next(
            (
                model
                for model in available
                if "qwen" in model.lower()
            ),
            available[0]
        )

    async def health(self):

        try:

            model = await self.resolve_model()

            return {
                "connected": True,
                "provider": "LM Studio",
                "model": model
            }

        except LLMServiceError as error:

            return {
                "connected": False,
                "provider": "LM Studio",
                "error": str(error)
            }

    async def generate(
        self,
        messages,
        temperature=0.2,
        max_tokens=1024
    ):

        model = await self.resolve_model()

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                )

                response.raise_for_status()

                result = response.json()

                return (
                    result["choices"][0]["message"]["content"]
                    or ""
                )

        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:

            raise LLMServiceError(
                "AI response generation failed."
            ) from error

    async def stream(
        self,
        messages,
        temperature=0.2,
        max_tokens=1024
    ):

        model = await self.resolve_model()

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload
                ) as response:

                    response.raise_for_status()

                    async for line in response.aiter_lines():

                        if not line.startswith("data:"):
                            continue

                        data = line[5:].strip()

                        if data == "[DONE]":
                            return

                        try:

                            event = json.loads(data)

                            choices = event.get("choices", [])

                            if not choices:
                                continue

                            content = choices[0].get(
                                "delta", {}
                            ).get("content")

                            if content:
                                yield content

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as error:

            raise LLMServiceError(
                "AI streaming connection failed."
            ) from error


llm_service = LLMService()