import unittest

import httpx

from tools.amap_tools import AmapTools


class AmapToolsTests(unittest.IsolatedAsyncioTestCase):
    async def test_auto_mode_marks_mock_fallback(self):
        tools = AmapTools("", "", data_mode="auto", transport="rest", timeout=1)
        try:
            result = await tools.geocode("北京市朝阳区测试地址")
            self.assertTrue(result["_meta"]["is_mock"])
            provenance = tools.provenance()
            self.assertTrue(provenance["used_mock_data"])
            self.assertFalse(provenance["used_real_data"])
            self.assertTrue(provenance["warnings"])
        finally:
            await tools.close()

    async def test_real_nearby_response_keeps_provenance(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/v3/place/around")
            self.assertEqual(request.url.params["key"], "test-key")
            return httpx.Response(
                200,
                json={
                    "status": "1",
                    "count": "1",
                    "pois": [{"id": "A1", "name": "真实测试 POI", "distance": "120"}],
                },
            )

        client = httpx.AsyncClient(
            base_url="https://restapi.amap.com",
            transport=httpx.MockTransport(handler),
        )
        tools = AmapTools(
            "",
            "test-key",
            data_mode="real",
            transport="rest",
            timeout=1,
            http_client=client,
        )
        try:
            result = await tools.search_around("116.4,39.9", types="050000")
            self.assertEqual(result["_meta"]["source"], "amap_rest")
            self.assertEqual(result["pois"][0]["name"], "真实测试 POI")
            self.assertTrue(tools.provenance()["used_real_data"])
            self.assertFalse(tools.provenance()["used_mock_data"])
        finally:
            await tools.close()
            await client.aclose()

    async def test_retry_and_cache_reduce_upstream_calls(self):
        attempts = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, request=request, json={"status": "0"})
            return httpx.Response(
                200,
                request=request,
                json={
                    "status": "1",
                    "count": "1",
                    "pois": [{"id": "C1", "name": "缓存测试", "distance": "100"}],
                },
            )

        client = httpx.AsyncClient(
            base_url="https://restapi.amap.com", transport=httpx.MockTransport(handler)
        )
        tools = AmapTools(
            "",
            "retry-cache-key",
            data_mode="real",
            transport="rest",
            http_client=client,
            max_retries=1,
            cache_ttl_seconds=60,
        )
        try:
            first = await tools.search_around("116.41,39.91", types="050000")
            second = await tools.search_around("116.41,39.91", types="050000")
            self.assertEqual(first["pois"], second["pois"])
            self.assertEqual(attempts, 2)
            self.assertEqual(tools.provenance()["api_calls"], 2)
            self.assertEqual(tools.provenance()["cache_hits"], 1)
            operations = tools.provenance()["operations"]
            self.assertEqual(operations[0]["api_calls"], 2)
            self.assertEqual(operations[1]["cache_hits"], 1)
        finally:
            await tools.close()
            self.assertFalse(client.is_closed)
            await client.aclose()

    async def test_upstream_errors_do_not_disclose_api_key(self):
        secret = "super-secret-amap-key"

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, request=request, json={"status": "0"})

        client = httpx.AsyncClient(
            base_url="https://restapi.amap.com", transport=httpx.MockTransport(handler)
        )
        tools = AmapTools(
            "",
            secret,
            data_mode="real",
            transport="rest",
            http_client=client,
            max_retries=0,
            cache_ttl_seconds=0,
        )
        try:
            with self.assertRaises(Exception) as context:
                await tools.search_around("116.42,39.92", types="050000")
            self.assertNotIn(secret, str(context.exception))
            self.assertIn("HTTP 503", str(context.exception))
        finally:
            await tools.close()
            await client.aclose()


if __name__ == "__main__":
    unittest.main()
