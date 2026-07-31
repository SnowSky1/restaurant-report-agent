import logging
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.main import app
from config.settings import settings
from nodes.state import ChartData, LocationInfo, POIAnalysis, TrafficInfo, WeatherData


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def test_health_and_validation(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(health.headers["x-content-type-options"], "nosniff")
        self.assertTrue(health.headers["x-request-id"])
        self.assertIn("supported_store_types", health.json())
        self.assertGreaterEqual(logging.getLogger("httpx").level, logging.WARNING)

        invalid = self.client.post(
            "/api/analyze",
            json={"store_name": "A", "store_address": "北京市", "location": "999,999"},
        )
        self.assertEqual(invalid.status_code, 422)

        preflight = self.client.options(
            "/api/analyze",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(preflight.headers["access-control-allow-origin"], "http://127.0.0.1:3000")

    def test_analyze_serializes_complete_response(self):
        report = "# 测试报告\n\n完整内容"
        state = {
            "run_id": "run-test",
            "store_name": "测试店",
            "store_address": "北京市朝阳区",
            "store_type": "咖啡店",
            "analysis_radius": 1000,
            "location": LocationInfo("116.4,39.9", "北京市朝阳区", city="北京市", source="mock"),
            "competitors": [],
            "traffic": TrafficInfo(traffic_score={"综合": 7.2}, summary="交通良好"),
            "weather": WeatherData(current={"weather": "晴", "temperature": "26"}),
            "poi_analysis": POIAnalysis(poi_counts={"写字楼": 2, "住宅": 1}),
            "charts": ChartData(revenue_chart={"type": "line", "data": []}),
            "competition_analysis": {"competition_intensity": {"score": 4.2}},
            "revenue_simulation": {
                "recommended_strategy": "balanced",
                "scenario_simulations": [
                    {
                        "id": "balanced",
                        "name": "均衡经营",
                        "daily_series": [{"name": "周一", "revenue": 1000, "orders": 30}],
                    }
                ],
            },
            "provenance": {
                "used_mock_data": True,
                "used_real_data": False,
                "warnings": ["测试回退"],
            },
            "errors": [],
        }
        analysis_mock = AsyncMock(return_value=(report, state))
        with patch("api.main.run_analysis", new=analysis_mock):
            response = self.client.post(
                "/api/analyze",
                json={
                    "store_name": "测试店",
                    "store_address": "北京市朝阳区",
                    "store_type": "咖啡店",
                    "location": "116.400000,39.900000",
                    "use_llm": False,
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["report_markdown"], report)
        self.assertEqual(body["data"]["run_id"], "run-test")
        self.assertEqual(body["data"]["request_id"], response.headers["x-request-id"])
        self.assertEqual(body["data"]["traffic_score_value"], 7.2)
        self.assertEqual(body["data"]["lineChartData"][0]["orders"], 30)
        self.assertTrue(body["data"]["provenance"]["used_mock_data"])
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["data"]["status"], "degraded")
        self.assertFalse(analysis_mock.await_args.kwargs["save_report"])
        self.assertIsNotNone(analysis_mock.await_args.kwargs["amap_tools"])

    def test_analyze_rejects_report_without_location(self):
        with patch(
            "api.main.run_analysis",
            new=AsyncMock(return_value=("# 不可信报告", {"errors": ["位置解析失败"]})),
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "store_name": "测试店",
                    "store_address": "无效地址",
                    "use_llm": False,
                },
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("位置解析失败", response.json()["detail"])

    def test_optional_api_token_protects_costly_endpoints(self):
        old_token = settings.api_access_token
        settings.api_access_token = "test-access-token"
        try:
            unauthorized = self.client.post(
                "/api/analyze",
                json={
                    "store_name": "测试店",
                    "store_address": "北京市",
                    "use_llm": False,
                },
            )
            ready = self.client.get("/api/ready")
        finally:
            settings.api_access_token = old_token
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(ready.status_code, 401)


if __name__ == "__main__":
    unittest.main()
