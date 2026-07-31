import unittest

from config.settings import settings
from graph.agent import create_agent_graph
from main import run_analysis
from nodes.competition_analysis import _deep_merge, _sanitize_enrichment
from nodes.revenue_simulation import DEFAULTS, SCENARIOS, simulate_market
from nodes.state import CompetitorInfo, POIAnalysis, TrafficInfo, create_initial_state


class RevenueSimulationTests(unittest.TestCase):
    def test_competeai_scenarios_are_complete_and_deterministic(self):
        state = create_initial_state(
            "测试咖啡",
            "北京市朝阳区",
            "咖啡店",
            avg_ticket=40,
            seat_count=50,
            daily_fixed_cost=3000,
            variable_cost_rate=0.35,
        )
        state["competitors"] = [
            CompetitorInfo("竞品 A", "220", "测试路", rating="4.5", average_cost="38"),
            CompetitorInfo("竞品 B", "680", "测试街", rating="4.1", average_cost="32"),
        ]
        state["traffic"] = TrafficInfo(traffic_score={"综合": 8.2})
        state["poi_analysis"] = POIAnalysis(
            poi_counts={"写字楼": 12, "住宅": 8, "商场": 3, "学校": 1, "医院": 1}
        )

        first = simulate_market(state)
        second = simulate_market(state)

        self.assertEqual(first, second)
        self.assertEqual(len(first["scenario_simulations"]), 3)
        profitable = [item for item in first["scenario_simulations"] if item["monthly_profit"] > 0]
        if profitable:
            self.assertEqual(first["viability_status"], "viable")
            self.assertIn(first["recommended_strategy"], {"value", "balanced", "premium"})
        else:
            self.assertEqual(first["viability_status"], "not_viable")
            self.assertIsNone(first["recommended_strategy"])
        self.assertEqual(first["assumptions"]["avg_ticket"], 40)
        for scenario in first["scenario_simulations"]:
            self.assertEqual(len(scenario["competitive_response_rounds"]), 3)
            self.assertEqual(len(scenario["daily_series"]), 7)
            self.assertGreater(scenario["daily_orders"], 0)

    def test_all_negative_scenarios_are_not_recommended(self):
        state = create_initial_state("高成本测试", "测试地址", "咖啡店", daily_fixed_cost=100000)
        result = simulate_market(state)
        self.assertTrue(all(item["monthly_profit"] < 0 for item in result["scenario_simulations"]))
        self.assertEqual(result["viability_status"], "not_viable")
        self.assertIsNone(result["recommended_strategy"])
        self.assertIn("不建议直接执行", result["recommendation_message"])

    def test_every_supported_store_type_has_explicit_defaults(self):
        expected = {
            "餐厅",
            "咖啡店",
            "奶茶店",
            "火锅店",
            "烧烤店",
            "快餐店",
            "面馆",
            "西餐厅",
            "日料店",
            "韩餐厅",
            "川菜馆",
            "粤菜馆",
            "甜品店",
            "面包店",
        }
        self.assertEqual(set(DEFAULTS), expected)

    def test_projection_keeps_fixed_cost_fixed(self):
        state = create_initial_state(
            "投影测试",
            "测试地址",
            "咖啡店",
            daily_fixed_cost=4000,
            variable_cost_rate=0.4,
        )
        result = simulate_market(state)
        source_id = result["recommended_strategy"] or result["best_available_strategy"]
        source = next(item for item in result["scenario_simulations"] if item["id"] == source_id)
        marketing = next(item["marketing_cost"] for item in SCENARIOS if item["id"] == source_id)
        expected_m1 = source["monthly_revenue"] * 0.9 * 0.6 - (4000 + marketing) * 30
        self.assertAlmostEqual(result["monthly_projection"][0]["profit"], expected_m1, places=2)
        self.assertIn("仅改变客单价", result["sensitivity_analysis"]["method"])


class LLMEnrichmentSafetyTests(unittest.TestCase):
    def test_llm_cannot_override_deterministic_evidence(self):
        baseline = {
            "competition_intensity": {"score": 6.8, "sample_size": 20},
            "pricing_strategy": {
                "suggested_range": {"low": 30, "high": 50},
                "recommendation": "baseline",
            },
        }
        untrusted = {
            "competition_intensity": {"score": 0, "sample_size": 999999},
            "pricing_strategy": {
                "suggested_range": {"low": 0, "high": 1},
                "recommendation": "safe narrative",
            },
            "invented_key": "must be dropped",
        }
        merged = _deep_merge(baseline, _sanitize_enrichment(untrusted))
        self.assertEqual(merged["competition_intensity"], baseline["competition_intensity"])
        self.assertEqual(merged["pricing_strategy"]["suggested_range"], {"low": 30, "high": 50})
        self.assertEqual(merged["pricing_strategy"]["recommendation"], "safe narrative")
        self.assertNotIn("invented_key", merged)


class _LocationFailureTools:
    def __init__(self):
        self.calls = []

    async def geocode(self, address):
        self.calls.append("geocode")
        return {"geocodes": [], "_meta": {"source": "test"}}

    def provenance(self):
        return {"used_mock_data": False, "used_real_data": False, "warnings": []}


class GraphRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_location_failure_stops_before_data_collection(self):
        tools = _LocationFailureTools()
        graph = create_agent_graph(tools)
        result = await graph.ainvoke(create_initial_state("失败测试", "无效地址"))
        self.assertIsNone(result["location"])
        self.assertEqual(result["workflow_status"], "failed")
        self.assertEqual(tools.calls, ["geocode"])
        self.assertIsNone(result["traffic"])


class MockWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_full_langgraph_mock_workflow_contains_every_stage(self):
        old_mode = settings.data_mode
        old_transport = settings.amap_transport
        settings.data_mode = "mock"
        settings.amap_transport = "rest"
        try:
            report, state = await run_analysis(
                store_name="基准测试咖啡",
                store_address="北京市朝阳区建国路88号",
                store_type="咖啡店",
                analysis_radius=1000,
                use_llm=False,
                deep_analysis=True,
                save_report=False,
                display_report=False,
            )
        finally:
            settings.data_mode = old_mode
            settings.amap_transport = old_transport

        self.assertGreater(len(report), 1000)
        self.assertIsNotNone(state["location"])
        self.assertTrue(state["competitors"])
        self.assertIsNotNone(state["traffic"])
        self.assertIsNotNone(state["weather"])
        self.assertIsNotNone(state["poi_analysis"])
        self.assertTrue(all(value > 0 for value in state["poi_analysis"].poi_counts.values()))
        self.assertIsNotNone(state["competition_analysis"])
        self.assertIsNotNone(state["revenue_simulation"])
        self.assertIsNotNone(state["charts"])
        self.assertTrue(state["charts"].revenue_chart)
        self.assertTrue(state["provenance"]["used_mock_data"])
        self.assertEqual(state["errors"], [])


if __name__ == "__main__":
    unittest.main()
