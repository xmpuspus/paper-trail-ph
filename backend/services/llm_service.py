from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Abstraction over Claude and OpenAI APIs. Uses Anthropic when available, falls back to OpenAI."""

    def __init__(self) -> None:
        self._anthropic_client: Any = None
        self._openai_client: Any = None
        self._provider: str = "none"
        self._init_client()

    def _init_client(self) -> None:
        if settings.anthropic_api_key:
            try:
                import anthropic

                self._anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key,
                )
                self._provider = "anthropic"
                logger.info("LLM provider: Anthropic (Claude)")
                return
            except ImportError:
                logger.warning("anthropic package not installed, trying openai")

        if settings.openai_api_key:
            try:
                import openai

                self._openai_client = openai.AsyncOpenAI(
                    api_key=settings.openai_api_key,
                )
                self._provider = "openai"
                logger.info("LLM provider: OpenAI")
                return
            except ImportError:
                logger.warning("openai package not installed")

        logger.warning("No LLM API key configured. LLM features disabled.")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        if self._provider == "anthropic" and self._anthropic_client:
            return await self._generate_anthropic(prompt, system, max_tokens)
        if self._provider == "openai" and self._openai_client:
            return await self._generate_openai(prompt, system, max_tokens)
        return "LLM service is not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."

    def _get_anthropic_client(self, api_key: str | None = None) -> Any:
        """Return the default Anthropic client, or create a temporary one for a user-provided key."""
        if api_key:
            import anthropic

            return anthropic.AsyncAnthropic(api_key=api_key)
        return self._anthropic_client

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
        api_key: str | None = None,
    ) -> AsyncGenerator[str, None]:
        client = self._get_anthropic_client(api_key)
        if api_key and client:
            async for token in self._stream_anthropic(prompt, system, client):
                yield token
        elif self._provider == "anthropic" and self._anthropic_client:
            async for token in self._stream_anthropic(prompt, system):
                yield token
        elif self._provider == "openai" and self._openai_client:
            async for token in self._stream_openai(prompt, system):
                yield token
        else:
            yield "LLM service is not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."

    async def stream_messages(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        api_key: str | None = None,
    ) -> AsyncGenerator[str, None]:
        client = self._get_anthropic_client(api_key)
        if api_key and client:
            async for token in self._stream_anthropic_messages(messages, system, client):
                yield token
        elif self._provider == "anthropic" and self._anthropic_client:
            async for token in self._stream_anthropic_messages(messages, system):
                yield token
        elif self._provider == "openai" and self._openai_client:
            async for token in self._stream_openai_messages(messages, system):
                yield token
        else:
            yield "LLM service is not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."

    # -- Anthropic --

    async def _generate_anthropic(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = await self._anthropic_client.messages.create(**kwargs)
        return response.content[0].text

    async def _stream_anthropic(
        self,
        prompt: str,
        system: str | None,
        client: Any = None,
    ) -> AsyncGenerator[str, None]:
        client = client or self._anthropic_client
        kwargs: dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def _stream_anthropic_messages(
        self,
        messages: list[dict[str, str]],
        system: str | None,
        client: Any = None,
    ) -> AsyncGenerator[str, None]:
        client = client or self._anthropic_client
        cleaned = _ensure_alternating(messages)
        kwargs: dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2048,
            "messages": cleaned,
        }
        if system:
            kwargs["system"] = system

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    # -- OpenAI --

    async def _generate_openai(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _stream_openai(
        self,
        prompt: str,
        system: str | None,
    ) -> AsyncGenerator[str, None]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await self._openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def _stream_openai_messages(
        self,
        messages: list[dict[str, str]],
        system: str | None,
    ) -> AsyncGenerator[str, None]:
        openai_messages: list[dict[str, str]] = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)

        stream = await self._openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


def _ensure_alternating(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ensure messages alternate between user and assistant (Anthropic requirement)."""
    cleaned: list[dict[str, str]] = []
    for msg in messages:
        if cleaned and cleaned[-1]["role"] == msg["role"]:
            cleaned[-1] = {
                "role": msg["role"],
                "content": cleaned[-1]["content"] + "\n\n" + msg["content"],
            }
        else:
            cleaned.append(dict(msg))
    if cleaned and cleaned[0]["role"] != "user":
        cleaned = cleaned[1:]
    return cleaned
