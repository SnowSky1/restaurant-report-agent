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

        tools = AmapTools("", "test-key", data_mode="real", transport="rest", timeout=1)
        await tools.http.aclose()
        tools.http = httpx.AsyncClient(
            base_url="https://restapi.amap.com",
            transport=httpx.MockTransport(handler),
        )
        try:
            result = await tools.search_around("116.4,39.9", types="050000")
            self.assertEqual(result["_meta"]["source"], "amap_rest")
            self.assertEqual(result["pois"][0]["name"], "真实测试 POI")
            self.assertTrue(tools.provenance()["used_real_data"])
            self.assertFalse(tools.provenance()["used_mock_data"])
        finally:
            await tools.close()


if __name__ == "__main__":
    unittest.main()
