import unittest

from config.settings import settings
from main import run_analysis
from nodes.revenue_simulation import simulate_market
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
        state["poi_analysis"] = POIAnalysis(poi_counts={"写字楼": 12, "住宅": 8, "商场": 3, "学校": 1, "医院": 1})

        first = simulate_market(state)
        second = simulate_market(state)

        self.assertEqual(first, second)
        self.assertEqual(len(first["scenario_simulations"]), 3)
        self.assertIn(first["recommended_strategy"], {"value", "balanced", "premium"})
        self.assertEqual(first["assumptions"]["avg_ticket"], 40)
        for scenario in first["scenario_simulations"]:
            self.assertEqual(len(scenario["competitive_response_rounds"]), 3)
            self.assertEqual(len(scenario["daily_series"]), 7)
            self.assertGreater(scenario["daily_orders"], 0)


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
