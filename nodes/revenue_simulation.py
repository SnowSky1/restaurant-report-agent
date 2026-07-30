"""Transparent CompeteAI-inspired market and revenue simulation.

This is not a claim of ground-truth forecasting.  It is a deterministic,
multi-agent scenario model: one target restaurant, nearby competitor agents
and consumer segments compete over several response rounds.  Every financial
output carries its assumptions and should be replaced with actual POS/cost
data when available.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean
from typing import Any

from .state import AgentState


DEFAULTS = {
    "咖啡店": {"avg_ticket": 36.0, "seats": 42, "fixed": 3200.0, "variable": 0.36},
    "奶茶店": {"avg_ticket": 24.0, "seats": 18, "fixed": 2400.0, "variable": 0.34},
    "快餐店": {"avg_ticket": 32.0, "seats": 48, "fixed": 3600.0, "variable": 0.42},
    "火锅店": {"avg_ticket": 118.0, "seats": 90, "fixed": 8500.0, "variable": 0.45},
    "餐厅": {"avg_ticket": 58.0, "seats": 64, "fixed": 5200.0, "variable": 0.43},
}


@dataclass
class MarketAgent:
    name: str
    price: float
    rating: float
    distance: float
    is_target: bool = False


SCENARIOS = [
    {"id": "value", "name": "价格渗透", "price_factor": 0.90, "quality_bonus": 0.00, "marketing_cost": 180.0},
    {"id": "balanced", "name": "均衡经营", "price_factor": 1.00, "quality_bonus": 0.08, "marketing_cost": 120.0},
    {"id": "premium", "name": "品质溢价", "price_factor": 1.10, "quality_bonus": 0.22, "marketing_cost": 220.0},
]


async def revenue_simulation_node(state: AgentState) -> dict:
    errors = list(state.get("errors", []))
    try:
        result = simulate_market(state)
        return {"revenue_simulation": result, "errors": errors}
    except Exception as error:
        errors.append(f"营收模拟失败：{error}")
        return {"revenue_simulation": None, "errors": errors}


def simulate_market(state: AgentState) -> dict[str, Any]:
    store_type = state.get("store_type", "餐厅")
    defaults = DEFAULTS.get(store_type, DEFAULTS["餐厅"])
    avg_ticket = _positive(state.get("avg_ticket"), defaults["avg_ticket"])
    seats = int(_positive(state.get("seat_count"), defaults["seats"]))
    fixed_cost = _positive(state.get("daily_fixed_cost"), defaults["fixed"])
    variable_rate = min(max(_positive(state.get("variable_cost_rate"), defaults["variable"]), 0.05), 0.9)

    competitors = list(state.get("competitors") or [])[:10]
    competitor_costs = [
        _positive(getattr(item, "average_cost", None), avg_ticket)
        for item in competitors
    ]
    competitor_ratings = [
        _positive(getattr(item, "rating", None), 4.1)
        for item in competitors
    ]

    traffic = state.get("traffic")
    traffic_score = float(getattr(traffic, "traffic_score", {}).get("综合", 5.0)) if traffic else 5.0
    poi = state.get("poi_analysis")
    counts = getattr(poi, "poi_counts", {}) if poi else {}
    daily_market_orders = _market_demand(counts, traffic_score)
    capacity = max(24, seats * 3)

    consumers = _consumer_segments(counts)
    agents = [
        MarketAgent(state.get("store_name", "目标门店"), avg_ticket, 4.3, 0.0, True)
    ]
    for index, item in enumerate(competitors):
        agents.append(
            MarketAgent(
                getattr(item, "name", f"竞品{index + 1}"),
                competitor_costs[index],
                competitor_ratings[index],
                _positive(getattr(item, "distance", None), 800.0),
            )
        )
    if len(agents) == 1:
        # The synthetic competitor keeps choice math meaningful while clearly
        # remaining an assumption rather than an observed POI.
        agents.append(MarketAgent("区域替代供给（假设）", avg_ticket * 0.96, 4.1, 650.0))

    simulations = [
        _simulate_scenario(
            scenario,
            agents,
            consumers,
            daily_market_orders,
            capacity,
            fixed_cost,
            variable_rate,
        )
        for scenario in SCENARIOS
    ]
    recommended = max(simulations, key=lambda item: item["monthly_profit"])
    baseline = next(item for item in simulations if item["id"] == "balanced")

    return {
        "model": "competeai-inspired multi-agent scenario simulation v1",
        "currency": "CNY",
        "recommended_strategy": recommended["id"],
        "recommended_strategy_name": recommended["name"],
        "base_revenue": {
            "daily_orders": baseline["daily_orders"],
            "daily_revenue": baseline["daily_revenue"],
            "monthly_revenue": baseline["monthly_revenue"],
            "monthly_profit": baseline["monthly_profit"],
            "break_even_orders_per_day": baseline["break_even_orders_per_day"],
        },
        "scenario_simulations": simulations,
        "sensitivity_analysis": {
            "ticket_minus_10pct_monthly_profit": next(item for item in simulations if item["id"] == "value")["monthly_profit"],
            "ticket_plus_10pct_monthly_profit": next(item for item in simulations if item["id"] == "premium")["monthly_profit"],
            "most_sensitive_variable": "订单量与客单价共同决定结果；请用真实 POS 数据替换默认假设",
        },
        "monthly_projection": _monthly_projection(recommended["monthly_revenue"], recommended["monthly_profit"]),
        "assumptions": {
            "avg_ticket": avg_ticket,
            "seat_count": seats,
            "daily_fixed_cost": fixed_cost,
            "variable_cost_rate": variable_rate,
            "estimated_daily_market_orders": daily_market_orders,
            "capacity_orders_per_day": capacity,
            "observed_competitor_agents": len(competitors),
            "simulation_rounds": 3,
            "days_per_month": 30,
            "poi_counts_are_api_sample": True,
        },
        "risk_assessment": [
            "结果是情景模拟，不是财务承诺",
            "未提供真实租金、人工、菜单毛利和 POS 订单时使用行业默认值",
            "高德 POI 数量受单页上限影响，不能视为完整市场普查",
            "实施前应以至少四周真实经营数据校准模型",
        ],
    }


def _simulate_scenario(
    scenario: dict[str, Any],
    source_agents: list[MarketAgent],
    consumers: list[dict[str, float]],
    market_orders: int,
    capacity: int,
    fixed_cost: float,
    variable_rate: float,
) -> dict[str, Any]:
    agents = [MarketAgent(**vars(agent)) for agent in source_agents]
    target = agents[0]
    target.price *= scenario["price_factor"]
    target.rating = min(5.0, target.rating + scenario["quality_bonus"])

    shares: list[float] = []
    for round_index in range(3):
        target_share = _target_share(agents, consumers)
        shares.append(target_share)
        # Competitor agents respond gradually to a strong or weak target.
        for competitor in agents[1:]:
            if target_share > 0.30:
                competitor.price *= 0.985
                competitor.rating = min(5.0, competitor.rating + 0.02)
            elif target_share < 0.12:
                competitor.price *= 1.005
        target.rating = min(5.0, target.rating + 0.01 * round_index)

    share = mean(shares)
    daily_orders = round(min(capacity, market_orders * share), 1)
    daily_revenue = round(daily_orders * target.price, 2)
    daily_profit = round(daily_revenue * (1 - variable_rate) - fixed_cost - scenario["marketing_cost"], 2)
    monthly_revenue = round(daily_revenue * 30, 2)
    monthly_profit = round(daily_profit * 30, 2)
    contribution_per_order = target.price * (1 - variable_rate)
    break_even = round((fixed_cost + scenario["marketing_cost"]) / max(contribution_per_order, 0.01), 1)

    weekday_factors = [0.88, 0.93, 1.00, 1.04, 1.16, 1.28, 1.12]
    daily_series = [
        {"name": day, "orders": round(daily_orders * factor), "revenue": round(daily_revenue * factor, 2)}
        for day, factor in zip(["周一", "周二", "周三", "周四", "周五", "周六", "周日"], weekday_factors)
    ]

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "average_ticket": round(target.price, 2),
        "market_share": round(share, 4),
        "daily_orders": daily_orders,
        "daily_revenue": daily_revenue,
        "monthly_revenue": monthly_revenue,
        "monthly_profit": monthly_profit,
        "break_even_orders_per_day": break_even,
        "competitive_response_rounds": [round(value, 4) for value in shares],
        "daily_series": daily_series,
    }


def _target_share(agents: list[MarketAgent], segments: list[dict[str, float]]) -> float:
    weighted_share = 0.0
    total_weight = sum(segment["weight"] for segment in segments) or 1.0
    reference_price = mean(agent.price for agent in agents)
    for segment in segments:
        utilities = []
        for agent in agents:
            price_ratio = agent.price / max(reference_price, 1)
            utility = (
                agent.rating * segment["quality_weight"]
                - price_ratio * segment["price_weight"]
                - (agent.distance / 1000) * segment["distance_weight"]
                + (0.18 if agent.is_target else 0.0)
            )
            utilities.append(utility)
        maximum = max(utilities)
        exponentials = [math.exp(value - maximum) for value in utilities]
        share = exponentials[0] / sum(exponentials)
        weighted_share += share * segment["weight"]
    return weighted_share / total_weight


def _consumer_segments(counts: dict[str, int]) -> list[dict[str, float]]:
    raw = {
        "office": max(counts.get("写字楼", 0), 1),
        "resident": max(counts.get("住宅", 0), 1),
        "shopper": max(counts.get("商场", 0), 1),
        "student": max(counts.get("学校", 0), 1),
    }
    total = sum(raw.values())
    return [
        {"weight": raw["office"] / total, "price_weight": 1.0, "quality_weight": 0.75, "distance_weight": 1.25},
        {"weight": raw["resident"] / total, "price_weight": 1.25, "quality_weight": 0.8, "distance_weight": 1.0},
        {"weight": raw["shopper"] / total, "price_weight": 0.85, "quality_weight": 1.05, "distance_weight": 0.75},
        {"weight": raw["student"] / total, "price_weight": 1.55, "quality_weight": 0.55, "distance_weight": 1.0},
    ]


def _market_demand(counts: dict[str, int], traffic_score: float) -> int:
    estimate = (
        36
        + counts.get("写字楼", 0) * 2.2
        + counts.get("住宅", 0) * 1.5
        + counts.get("商场", 0) * 3.0
        + counts.get("学校", 0) * 1.3
        + counts.get("医院", 0) * 1.0
        + traffic_score * 5.0
    )
    return round(min(max(estimate, 45), 420))


def _monthly_projection(revenue: float, profit: float) -> list[dict[str, Any]]:
    factors = [0.90, 0.96, 1.00, 1.03, 1.06, 1.08]
    return [
        {"month": f"M{index}", "revenue": round(revenue * factor, 2), "profit": round(profit * factor, 2)}
        for index, factor in enumerate(factors, 1)
    ]


def _positive(value: Any, default: float) -> float:
    try:
        number = float(value)
        return number if number > 0 else float(default)
    except (TypeError, ValueError):
        return float(default)
