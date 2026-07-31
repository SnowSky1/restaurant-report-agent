import unittest
from types import SimpleNamespace

from mcp_client.client import MCPClient


class _Session:
    async def call_tool(self, tool_name, arguments):
        return SimpleNamespace(
            isError=True,
            structuredContent={"looks": "valid"},
            content=[SimpleNamespace(text='{"also": "looks valid"}')],
        )


class MCPClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_error_result_is_never_parsed_as_success(self):
        client = MCPClient("https://example.invalid/sse")
        client._session = _Session()
        with self.assertRaisesRegex(RuntimeError, "returned an error"):
            await client.call_tool("test", {})


if __name__ == "__main__":
    unittest.main()
