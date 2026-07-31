"""Evidence-aware, deterministic comparison of candidate restaurant sites.

The comparison layer intentionally does not ask an LLM to rank sites.  It
normalizes the same observable metrics for every candidate, applies explicit
weights and hard constraints, and then perturbs the weights to show whether
the winner is stable.  This keeps the decision reproducible and auditable.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

CRITERIA: dict[str, dict[str, Any]] = {
    "demand_potential": {
        "label": "需求潜力",
        "direction": "higher",
        "unit": "估算市场订单/日",
        "description": "由周边业态样本与交通便利度推导的相对需求代理，不是客流实测。",
    },
    "accessibility": {
        "label": "交通可达性",
        "direction": "higher",
        "unit": "0-10",
        "description": "地铁、公交和停车样本形成的交通综合分。",
    },
    "competitive_headroom": {
        "label": "竞争空间",
        "direction": "higher",
        "unit": "0-10",
        "description": "竞争强度的反向指标；越高表示同类竞争压力相对越小。",
    },
    "profitability": {
        "label": "利润潜力",
        "direction": "higher",
        "unit": "元/月",
        "description": "相同经营假设下三个模拟情景中的最高月利润。",
    },
    "evidence_quality": {
        "label": "证据质量",
        "direction": "higher",
        "unit": "0-100",
        "description": "真实来源、字段覆盖、样本量、错误和经营参数校准的综合评分。",
    },
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "demand_potential": 0.25,
    "accessibility": 0.20,
    "competitive_headroom": 0.15,
    "profitability": 0.30,
    "evidence_quality": 0.10,
}


def assess_evidence_quality(
    data: dict[str, Any], *, calibrated_input_count: int = 0
) -> dict[str, Any]:
    """Score the decision evidence without scoring the attractiveness of a site."""

    provenance = data.get("provenance") or {}
    used_real = bool(provenance.get("used_real_data"))
    used_mock = bool(provenance.get("used_mock_data"))
    errors = list(data.get("errors") or [])
    factors: list[dict[str, Any]] = []
    limitations: list[str] = []

    if used_real and not used_mock:
        source_score = 30.0
        source_note = "所需地图数据均来自真实接口"
    elif used_real and used_mock:
        source_score = 18.0
        source_note = "真实数据与模拟回退混用"
        limitations.append("存在模拟回退，候选点之间可能不是完全同源数据")
    elif used_mock:
        source_score = 6.0
        source_note = "仅使用模拟数据"
        limitations.append("模拟数据只能验证流程，不能支撑真实投资决策")
    else:
        source_score = 0.0
        source_note = "数据来源未确认"
        limitations.append("无法确认地图数据来源")
    factors.append(
        {"name": "来源可信度", "score": source_score, "max_score": 30, "note": source_note}
    )

    location = data.get("location") or {}
    traffic = data.get("traffic") or {}
    poi = data.get("poi_analysis") or {}
    revenue = data.get("revenue_simulation") or {}
    competition_present = data.get("competition_score") is not None
    coverage_checks = [
        (bool(location.get("coordinates")), 5),
        (bool(traffic.get("traffic_score") or {}), 7),
        (bool(poi.get("poi_counts")), 7),
        (bool(revenue.get("scenario_simulations")), 7),
        (competition_present, 4),
    ]
    coverage_score = float(sum(points for present, points in coverage_checks if present))
    factors.append(
        {
            "name": "关键字段覆盖",
            "score": coverage_score,
            "max_score": 30,
            "note": f"覆盖 {sum(1 for present, _ in coverage_checks if present)}/5 个决策域",
        }
    )
    if coverage_score < 30:
        limitations.append("至少一个关键决策域缺失")

    competitor_count = max(0, int(data.get("competitor_count") or 0))
    poi_total = sum(_number(value) for value in (poi.get("poi_counts") or {}).values())
    sample_score = min(12.0, competitor_count / 10 * 12) + min(8.0, poi_total / 50 * 8)
    factors.append(
        {
            "name": "样本充分度",
            "score": round(sample_score, 1),
            "max_score": 20,
            "note": f"竞品 {competitor_count} 个，环境 POI 样本 {int(poi_total)} 个",
        }
    )
    if competitor_count < 5:
        limitations.append("同类竞品样本少于 5 个，竞争结论稳定性有限")

    operation_score = 10.0 if not errors else max(0.0, 10 - len(errors) * 3)
    factors.append(
        {
            "name": "运行完整性",
            "score": operation_score,
            "max_score": 10,
            "note": "无工作流错误" if not errors else f"记录到 {len(errors)} 个错误",
        }
    )
    if errors:
        limitations.append("工作流存在错误或缺失结果")

    calibrated = min(max(int(calibrated_input_count), 0), 4)
    calibration_score = calibrated / 4 * 10
    factors.append(
        {
            "name": "经营参数校准",
            "score": calibration_score,
            "max_score": 10,
            "note": f"已提供 {calibrated}/4 个自有经营参数",
        }
    )
    if calibrated < 4:
        limitations.append("财务模型仍包含行业默认假设，建议补齐客单、座位、固定与变动成本")

    score = round(min(100.0, sum(float(item["score"]) for item in factors)), 1)
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D"
    return {
        "score": score,
        "grade": grade,
        "factors": factors,
        "limitations": list(dict.fromkeys(limitations)),
        "method": "evidence-quality-v1",
    }


def compare_candidate_sites(
    candidates: list[dict[str, Any]],
    *,
    weights: dict[str, float] | None = None,
    require_viable: bool = True,
    minimum_evidence_score: float = 50.0,
) -> dict[str, Any]:
    """Rank already-analyzed candidates with explainable MCDA and sensitivity."""

    if len(candidates) < 2:
        raise ValueError("至少需要两个成功分析的候选点")
    normalized_weights = _normalize_weights(weights or DEFAULT_WEIGHTS)
    prepared = [_prepare_candidate(item) for item in candidates]
    normalized_metrics = _normalize_metrics(prepared)

    for item in prepared:
        item["criteria"] = {}
        score = 0.0
        for criterion, weight in normalized_weights.items():
            normalized = normalized_metrics[criterion][item["candidate_id"]]
            contribution = normalized * weight
            item["criteria"][criterion] = {
                "label": CRITERIA[criterion]["label"],
                "raw_value": item["raw_metrics"][criterion],
                "normalized_score": round(normalized, 1),
                "weight": round(weight, 4),
                "contribution": round(contribution, 2),
            }
            score += contribution
        item["score"] = round(score, 1)
        disqualifiers: list[str] = []
        if require_viable and item["viability_status"] != "viable":
            disqualifiers.append("没有通过盈利与产能可行性闸门")
        if item["evidence_quality"]["score"] < minimum_evidence_score:
            disqualifiers.append(f"证据质量低于 {minimum_evidence_score:g} 分门槛")
        item["eligible"] = not disqualifiers
        item["disqualifiers"] = disqualifiers
        _add_strengths_and_risks(item)

    ordered = sorted(prepared, key=lambda item: (-item["score"], item["candidate_id"]))
    eligible = [item for item in ordered if item["eligible"]]
    for index, item in enumerate(eligible, 1):
        item["rank"] = index
    for item in ordered:
        item.setdefault("rank", None)

    best_available = ordered[0]
    relative_leader = eligible[0] if eligible else None
    # Profitability remains an invariant for an executable recommendation,
    # even when the user chooses to rank non-viable sites for diagnosis.
    recommended = (
        relative_leader
        if relative_leader and relative_leader["viability_status"] == "viable"
        else None
    )
    stability = _weight_sensitivity(prepared, normalized_metrics, normalized_weights)
    leader_rate = (
        stability["top_pick_rate"].get(relative_leader["candidate_id"], 0.0)
        if relative_leader
        else 0.0
    )
    stability["leader_candidate_id"] = relative_leader["candidate_id"] if relative_leader else None
    stability["leader_pick_rate"] = leader_rate
    if recommended:
        winner_rate = stability["top_pick_rate"].get(recommended["candidate_id"], 0.0)
        stability["recommended_pick_rate"] = winner_rate
        stability["level"] = (
            "high" if winner_rate >= 0.8 else "medium" if winner_rate >= 0.6 else "low"
        )
        decision_status = "recommended"
        message = (
            f"{recommended['candidate_name']} 在当前权重和硬约束下排名第一；"
            f"权重扰动后仍有 {winner_rate:.0%} 的情景保持第一。"
        )
    elif relative_leader:
        stability["recommended_pick_rate"] = 0.0
        stability["level"] = "not_applicable"
        decision_status = "relative_ranking_only"
        message = (
            "候选点已完成相对排名，但没有任何点通过盈利与产能可行性闸门；"
            "不输出执行推荐，第一名仅表示当前指标下的相对领先点。"
        )
    else:
        stability["recommended_pick_rate"] = 0.0
        stability["level"] = "not_applicable"
        decision_status = "no_eligible_candidate"
        message = "所有候选点均触发硬约束，不输出可执行推荐；仅展示相对最优点供继续核验。"

    warnings = _comparison_warnings(ordered)
    return {
        "decision_status": decision_status,
        "message": message,
        "recommended_candidate_id": recommended["candidate_id"] if recommended else None,
        "best_available_candidate_id": best_available["candidate_id"],
        "weights": {key: round(value, 4) for key, value in normalized_weights.items()},
        "hard_constraints": {
            "require_viable": require_viable,
            "minimum_evidence_score": minimum_evidence_score,
        },
        "criteria_definitions": CRITERIA,
        "ranking": ordered,
        "sensitivity": stability,
        "warnings": warnings,
        "validation_plan": _validation_plan(recommended or best_available, stability),
        "method": {
            "name": "evidence-aware weighted site comparison v1",
            "normalization": "候选集合内 min-max；所有值相同时记 50 分",
            "sensitivity": "每个权重分别上下扰动 20%，重新归一化并统计第一名频率",
            "llm_used_for_ranking": False,
            "scope": "候选点初筛；不能替代客流实测、租约审查和真实门店销售模型",
        },
    }


def _prepare_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    data = candidate.get("data") or {}
    revenue = data.get("revenue_simulation") or {}
    scenarios = revenue.get("scenario_simulations") or []
    best_profit = max((_number(item.get("monthly_profit")) for item in scenarios), default=0.0)
    evidence = data.get("evidence_quality") or assess_evidence_quality(data)
    competition_intensity = min(10.0, max(0.0, _number(data.get("competition_score"))))
    provenance = data.get("provenance") or {}
    return {
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_name": str(candidate.get("candidate_name") or data.get("storeName") or "候选点"),
        "candidate_address": str(
            candidate.get("candidate_address") or data.get("storeAddress") or ""
        ),
        "status": data.get("status", "degraded"),
        "location": data.get("location") or {},
        "viability_status": revenue.get("viability_status", "not_viable"),
        "recommended_strategy": revenue.get("recommended_strategy"),
        "best_monthly_profit": round(best_profit, 2),
        "competitor_count": int(data.get("competitor_count") or 0),
        "evidence_quality": evidence,
        "raw_metrics": {
            "demand_potential": _number(
                (revenue.get("assumptions") or {}).get("estimated_daily_market_orders")
            ),
            "accessibility": _number(data.get("traffic_score_value")),
            "competitive_headroom": round(10.0 - competition_intensity, 2),
            "profitability": best_profit,
            "evidence_quality": _number(evidence.get("score")),
        },
        "provenance": {
            "used_real_data": bool(provenance.get("used_real_data")),
            "used_mock_data": bool(provenance.get("used_mock_data")),
            "sources": list(provenance.get("sources") or []),
            "api_calls": int(provenance.get("api_calls") or 0),
            "upstream_latency_ms": round(_number(provenance.get("upstream_latency_ms")), 1),
        },
        "errors": list(data.get("errors") or []),
    }


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    unknown = set(weights) - set(CRITERIA)
    if unknown:
        raise ValueError(f"未知比较指标：{', '.join(sorted(unknown))}")
    complete = {key: max(0.0, _number(weights.get(key, 0.0))) for key in CRITERIA}
    total = sum(complete.values())
    if total <= 0:
        raise ValueError("至少一个比较权重必须大于 0")
    return {key: value / total for key, value in complete.items()}


def _normalize_metrics(candidates: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for criterion in CRITERIA:
        values = [item["raw_metrics"][criterion] for item in candidates]
        low, high = min(values), max(values)
        if high == low:
            result[criterion] = {item["candidate_id"]: 50.0 for item in candidates}
            continue
        result[criterion] = {
            item["candidate_id"]: (item["raw_metrics"][criterion] - low) / (high - low) * 100
            for item in candidates
        }
    return result


def _weight_sensitivity(
    candidates: list[dict[str, Any]],
    metrics: dict[str, dict[str, float]],
    weights: dict[str, float],
) -> dict[str, Any]:
    eligible = [item for item in candidates if item["eligible"]]
    if not eligible:
        return {"scenario_count": 0, "top_pick_rate": {}, "note": "没有通过硬约束的候选点"}
    scenarios = [weights]
    for criterion in CRITERIA:
        for factor in (0.8, 1.2):
            perturbed = dict(weights)
            perturbed[criterion] *= factor
            scenarios.append(_normalize_weights(perturbed))
    winners: Counter[str] = Counter()
    for scenario in scenarios:
        ranked = sorted(
            eligible,
            key=lambda item: (
                -sum(
                    metrics[criterion][item["candidate_id"]] * weight
                    for criterion, weight in scenario.items()
                ),
                item["candidate_id"],
            ),
        )
        winners[ranked[0]["candidate_id"]] += 1
    return {
        "scenario_count": len(scenarios),
        "top_pick_rate": {
            item["candidate_id"]: round(winners[item["candidate_id"]] / len(scenarios), 4)
            for item in eligible
        },
        "note": "该比例只反映权重扰动稳定性，不代表预测成功概率。",
    }


def _add_strengths_and_risks(candidate: dict[str, Any]) -> None:
    ordered = sorted(
        candidate["criteria"].items(),
        key=lambda item: item[1]["normalized_score"],
        reverse=True,
    )
    strengths = [
        f"{details['label']} {details['normalized_score']:.0f} 分"
        for _, details in ordered[:2]
        if details["normalized_score"] >= 60
    ]
    candidate["strengths"] = strengths or ["各项相对表现接近，暂无突出优势"]
    risks = [
        f"{details['label']}相对分仅 {details['normalized_score']:.0f}"
        for _, details in ordered
        if details["normalized_score"] <= 40
    ]
    risks.extend(candidate["disqualifiers"])
    risks.extend((candidate["evidence_quality"].get("limitations") or [])[:2])
    candidate["risks"] = list(dict.fromkeys(risks))


def _comparison_warnings(candidates: list[dict[str, Any]]) -> list[str]:
    warnings = [
        "全部分数都是当前候选集合内的相对分，不应跨批次直接比较。",
        "利润潜力来自透明情景模拟，并非销售预测或财务承诺。",
    ]
    source_patterns = {
        (item["provenance"]["used_real_data"], item["provenance"]["used_mock_data"])
        for item in candidates
    }
    if len(source_patterns) > 1:
        warnings.append("候选点的数据来源模式不一致，排名可比性下降。")
    if any(item["status"] == "degraded" for item in candidates):
        warnings.append("至少一个候选点处于降级状态，请先核对其证据质量与错误。")
    return warnings


def _validation_plan(candidate: dict[str, Any], stability: dict[str, Any]) -> list[dict[str, str]]:
    plan = [
        {
            "stage": "现场客流核验",
            "action": "对排名前两位连续 7 天记录午餐、晚餐和周末分时客流，并区分路过与进店意向。",
            "success_metric": "形成同口径分时客流表，覆盖至少 14 个高峰时段。",
        },
        {
            "stage": "经营参数校准",
            "action": "取得候选铺位真实租金、人工、能耗、面积和菜单毛利，重新运行比较。",
            "success_metric": "四个经营参数全部由可追溯报价或历史流水替代默认值。",
        },
        {
            "stage": "轻量需求实验",
            "action": f"围绕 {candidate['candidate_name']} 做外卖预售、快闪或到店券实验，记录曝光到购买转化。",
            "success_metric": "获得至少 100 个有效意向样本并计算获客成本。",
        },
    ]
    if stability.get("level") in {"low", "medium"}:
        plan.append(
            {
                "stage": "排名稳健性复核",
                "action": "让经营、财务和拓展负责人分别设置权重，比较排名是否翻转。",
                "success_metric": "记录权重分歧；若第一名翻转，则保留两点进入下一轮尽调。",
            }
        )
    return plan


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
