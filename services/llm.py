"""Resilient LLM adapter with an optional local Claude/Krill fallback."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

import httpx
from langchain_openai import ChatOpenAI

from config.settings import Settings


@dataclass
class TextResponse:
    content: str


class KrillMessagesAdapter:
    """Minimal Anthropic Messages-compatible adapter for the user's gateway."""

    def __init__(self, base_url: str, auth_token: str, model: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.model = model
        self.timeout = timeout

    async def ainvoke(self, prompt: Any) -> TextResponse:
        text = _prompt_text(prompt)
        url = f"{self.base_url}/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 1800,
            "messages": [{"role": "user", "content": text}],
        }
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in {401, 403}:
                headers.pop("Authorization", None)
                headers["x-api-key"] = self.auth_token
                response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        parts = data.get("content") or []
        content = "".join(part.get("text", "") for part in parts if part.get("type") == "text")
        if not content:
            raise RuntimeError("Krill gateway returned no text content")
        return TextResponse(content)


class FallbackLLM:
    def __init__(self, primary: Any | None, fallback: Any | None):
        self.primary = primary
        self.fallback = fallback
        self.last_provider = "none"

    async def ainvoke(self, prompt: Any) -> Any:
        primary_error: Exception | None = None
        if self.primary is not None:
            try:
                response = await self.primary.ainvoke(prompt)
                self.last_provider = "primary"
                return response
            except Exception as error:
                primary_error = error
        if self.fallback is not None:
            response = await self.fallback.ainvoke(prompt)
            self.last_provider = "krill"
            return response
        if primary_error:
            raise primary_error
        raise RuntimeError("No LLM provider is configured")


def build_llm(settings: Settings) -> FallbackLLM | None:
    config = settings.get_llm_config()
    primary = None
    if config.get("api_key"):
        primary = ChatOpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url") or None,
            model=config["model"],
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            temperature=0.2,
        )

    fallback = None
    if settings.enable_krill_fallback:
        krill = _load_krill_config()
        if krill:
            fallback = KrillMessagesAdapter(
                krill["base_url"],
                krill["auth_token"],
                krill["model"],
                settings.llm_timeout_seconds,
            )
    if primary is None and fallback is None:
        return None
    return FallbackLLM(primary, fallback)


def _load_krill_config() -> dict[str, str] | None:
    explicit_path = os.getenv("CLAUDE_SETTINGS_PATH")
    path = Path(explicit_path) if explicit_path else Path.home() / ".claude" / "settings.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        env = data.get("env") or {}
        base_url = str(env.get("ANTHROPIC_BASE_URL") or "")
        token = str(env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY") or "")
        model = str(env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") or "gpt-5.6-luna")
        if base_url and token:
            return {"base_url": base_url, "auth_token": token, "model": model}
    except (OSError, ValueError, TypeError):
        return None
    return None


def _prompt_text(prompt: Any) -> str:
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        values = []
        for item in prompt:
            content = getattr(item, "content", None)
            values.append(str(content if content is not None else item))
        return "\n".join(values)
    return str(prompt)
