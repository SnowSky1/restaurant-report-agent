"""Small, real MCP-over-SSE client.

The old implementation silently returned canned map data.  This client either
connects to an MCP server or raises a clear error; mock fallback is handled by
the data provider where it can be disclosed to callers.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
from datetime import timedelta
import json
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPClient:
    def __init__(self, sse_url: str, api_key: str | None = None, timeout: float = 30.0):
        self.sse_url = sse_url
        self.api_key = api_key
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def initialize(self) -> None:
        if self._session is not None:
            return
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        stack = AsyncExitStack()
        try:
            read_stream, write_stream = await stack.enter_async_context(
                sse_client(
                    self.sse_url,
                    headers=headers or None,
                    timeout=self.timeout,
                    sse_read_timeout=max(self.timeout, 60.0),
                )
            )
            session = await stack.enter_async_context(
                ClientSession(
                    read_stream,
                    write_stream,
                    read_timeout_seconds=timedelta(seconds=self.timeout),
                )
            )
            await session.initialize()
        except Exception:
            await stack.aclose()
            raise

        self._stack = stack
        self._session = session

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        await self.initialize()
        assert self._session is not None
        result = await self._session.call_tool(tool_name, arguments)

        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict):
            return structured

        for block in getattr(result, "content", []):
            text = getattr(block, "text", None)
            if not text:
                continue
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {"content": text}

        if getattr(result, "isError", False):
            raise RuntimeError(f"MCP tool {tool_name} returned an error")
        return {}

    async def close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = None
        self._session = None
