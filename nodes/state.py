"""Typed state shared by the LangGraph workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict
from uuid import uuid4


@dataclass
class LocationInfo:
    coordinates: str
    address: str
    business_area: str = ""
    district: str = ""
    city: str = ""
    adcode: str = ""
    source: str = "unknown"


@dataclass
class CompetitorInfo:
    name: str
    distance: str
    address: str
    rating: str = ""
    type: str = ""
    typecode: str = ""
    location: str = ""
    average_cost: str = ""
    source: str = "unknown"


@dataclass
class TrafficInfo:
    subway_stations: list[dict[str, Any]] = field(default_factory=list)
    bus_stations: list[dict[str, Any]] = field(default_factory=list)
    parking_lots: list[dict[str, Any]] = field(default_factory=list)
    traffic_score: dict[str, float] = field(default_factory=dict)
    summary: str = ""


@dataclass
class WeatherData:
    current: dict[str, Any] = field(default_factory=dict)
    forecast: list[dict[str, Any]] = field(default_factory=list)
    business_impact: str = ""


@dataclass
class POIAnalysis:
    poi_counts: dict[str, int] = field(default_factory=dict)
    poi_details: list[dict[str, Any]] = field(default_factory=list)
    poi_summary: str = ""


@dataclass
class ChartData:
    competitor_chart: dict[str, Any] = field(default_factory=dict)
    poi_chart: dict[str, Any] = field(default_factory=dict)
    traffic_chart: dict[str, Any] = field(default_factory=dict)
    revenue_chart: dict[str, Any] = field(default_factory=dict)


class AgentState(TypedDict, total=False):
    run_id: str
    store_name: str
    store_address: str
    store_type: str
    analysis_radius: int
    input_coordinates: str | None
    avg_ticket: float | None
    seat_count: int | None
    daily_fixed_cost: float | None
    variable_cost_rate: float | None

    location: LocationInfo | None
    competitors: list[CompetitorInfo] | None
    traffic: TrafficInfo | None
    weather: WeatherData | None
    poi_analysis: POIAnalysis | None
    competition_analysis: dict[str, Any] | None
    revenue_simulation: dict[str, Any] | None
    charts: ChartData | None
    provenance: dict[str, Any]
    final_report: str | None
    workflow_status: str
    errors: list[str]


def create_initial_state(
    store_name: str,
    store_address: str,
    store_type: str = "餐厅",
    analysis_radius: int = 1000,
    *,
    input_coordinates: str | None = None,
    avg_ticket: float | None = None,
    seat_count: int | None = None,
    daily_fixed_cost: float | None = None,
    variable_cost_rate: float | None = None,
) -> AgentState:
    return AgentState(
        run_id=uuid4().hex,
        store_name=store_name,
        store_address=store_address,
        store_type=store_type,
        analysis_radius=analysis_radius,
        input_coordinates=input_coordinates,
        avg_ticket=avg_ticket,
        seat_count=seat_count,
        daily_fixed_cost=daily_fixed_cost,
        variable_cost_rate=variable_cost_rate,
        location=None,
        competitors=[],
        traffic=None,
        weather=None,
        poi_analysis=None,
        competition_analysis=None,
        revenue_simulation=None,
        charts=None,
        provenance={},
        final_report=None,
        workflow_status="pending",
        errors=[],
    )
