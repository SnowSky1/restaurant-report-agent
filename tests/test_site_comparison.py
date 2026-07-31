import unittest

from services.site_comparison import assess_evidence_quality, compare_candidate_sites


def candidate(
    candidate_id: str,
    *,
    demand: float,
    traffic: float,
    competition: float,
    profit: float,
    viable: bool = True,
    mock: bool = False,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "candidate_name": f"候选点 {candidate_id}",
        "candidate_address": f"测试地址 {candidate_id}",
        "data": {
            "status": "degraded" if mock else "complete",
            "location": {"coordinates": "116.4,39.9"},
            "competition_score": competition,
            "competitor_count": 10,
            "traffic_score_value": traffic,
            "traffic": {"traffic_score": {"综合": traffic}},
            "poi_analysis": {"poi_counts": {"写字楼": 30, "住宅": 20}},
            "revenue_simulation": {
                "viability_status": "viable" if viable else "not_viable",
                "recommended_strategy": "balanced" if viable else None,
                "assumptions": {"estimated_daily_market_orders": demand},
                "scenario_simulations": [
                    {"id": "balanced", "monthly_profit": profit},
                    {"id": "premium", "monthly_profit": profit * 0.8},
                ],
            },
            "provenance": {
                "used_real_data": not mock,
                "used_mock_data": mock,
                "sources": ["amap" if not mock else "mock"],
            },
            "errors": [],
        },
    }


class SiteComparisonTests(unittest.TestCase):
    def test_evidence_quality_exposes_source_and_calibration_limits(self):
        data = candidate("A", demand=100, traffic=8, competition=5, profit=10000, mock=True)["data"]
        quality = assess_evidence_quality(data, calibrated_input_count=0)

        self.assertLess(quality["score"], 70)
        self.assertIn(quality["grade"], {"C", "D"})
        self.assertTrue(any("模拟数据" in item for item in quality["limitations"]))
        self.assertTrue(any("行业默认" in item for item in quality["limitations"]))

    def test_comparison_is_explainable_and_deterministic(self):
        candidates = [
            candidate("A", demand=120, traffic=7, competition=6, profit=30000),
            candidate("B", demand=80, traffic=9, competition=3, profit=18000),
        ]
        for item in candidates:
            item["data"]["evidence_quality"] = assess_evidence_quality(
                item["data"], calibrated_input_count=4
            )

        first = compare_candidate_sites(candidates)
        second = compare_candidate_sites(candidates)

        self.assertEqual(first, second)
        self.assertEqual(first["recommended_candidate_id"], "A")
        self.assertEqual(first["ranking"][0]["rank"], 1)
        self.assertIn("criteria", first["ranking"][0])
        self.assertIn("contribution", first["ranking"][0]["criteria"]["profitability"])
        self.assertEqual(first["sensitivity"]["scenario_count"], 11)
        self.assertFalse(first["method"]["llm_used_for_ranking"])
        self.assertEqual(len(first["validation_plan"]), 3)

    def test_viability_is_a_hard_gate_not_a_cosmetic_warning(self):
        candidates = [
            candidate("A", demand=200, traffic=10, competition=1, profit=-1000, viable=False),
            candidate("B", demand=150, traffic=8, competition=2, profit=-2000, viable=False),
        ]
        for item in candidates:
            item["data"]["evidence_quality"] = assess_evidence_quality(
                item["data"], calibrated_input_count=4
            )

        comparison = compare_candidate_sites(candidates, require_viable=True)

        self.assertEqual(comparison["decision_status"], "no_eligible_candidate")
        self.assertIsNone(comparison["recommended_candidate_id"])
        self.assertEqual(comparison["best_available_candidate_id"], "A")
        self.assertTrue(all(not item["eligible"] for item in comparison["ranking"]))
        self.assertTrue(all(item["rank"] is None for item in comparison["ranking"]))

    def test_disabling_rank_gate_still_does_not_recommend_a_loss(self):
        candidates = [
            candidate("A", demand=200, traffic=9, competition=2, profit=-100, viable=False),
            candidate("B", demand=100, traffic=7, competition=4, profit=-500, viable=False),
        ]
        for item in candidates:
            item["data"]["evidence_quality"] = assess_evidence_quality(
                item["data"], calibrated_input_count=4
            )

        comparison = compare_candidate_sites(candidates, require_viable=False)

        self.assertEqual(comparison["decision_status"], "relative_ranking_only")
        self.assertIsNone(comparison["recommended_candidate_id"])
        self.assertEqual(comparison["ranking"][0]["rank"], 1)
        self.assertEqual(comparison["sensitivity"]["recommended_pick_rate"], 0)
        self.assertGreater(comparison["sensitivity"]["leader_pick_rate"], 0)

    def test_zero_weights_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "权重"):
            compare_candidate_sites(
                [
                    candidate("A", demand=1, traffic=1, competition=1, profit=1),
                    candidate("B", demand=2, traffic=2, competition=2, profit=2),
                ],
                weights={
                    key: 0
                    for key in (
                        "demand_potential",
                        "accessibility",
                        "competitive_headroom",
                        "profitability",
                        "evidence_quality",
                    )
                },
            )


if __name__ == "__main__":
    unittest.main()
