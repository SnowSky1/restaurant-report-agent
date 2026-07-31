export interface ChartPoint {
  name: string;
  value: number;
  orders?: number;
}

export interface Competitor {
  name: string;
  distance: string;
  address: string;
  rating?: string;
  average_cost?: string;
  type?: string;
  source?: string;
}

export interface ReportData {
  status: "complete" | "degraded";
  request_id?: string;
  run_id: string;
  storeName: string;
  storeAddress: string;
  storeType: string;
  analysisRadius: number;
  location: {
    coordinates?: string;
    address?: string;
    business_area?: string;
    district?: string;
    city?: string;
    source?: string;
  };
  competition_score: number;
  competitor_count: number;
  traffic_score: string;
  traffic_score_value: number;
  traffic_desc: string;
  poi_main_type: string;
  poi_desc: string;
  weather_main: string;
  weather_desc: string;
  lineChartData: ChartPoint[];
  pieChartData: ChartPoint[];
  competitors: Competitor[];
  traffic: {
    subway_stations?: Array<Record<string, unknown>>;
    bus_stations?: Array<Record<string, unknown>>;
    parking_lots?: Array<Record<string, unknown>>;
    traffic_score?: Record<string, number>;
    summary?: string;
  };
  weather: {
    current?: Record<string, string>;
    forecast?: Array<Record<string, string>>;
    business_impact?: string;
  };
  poi_analysis: {
    poi_counts?: Record<string, number>;
    poi_details?: Array<Record<string, unknown>>;
    poi_summary?: string;
  };
  competition_analysis: Record<string, unknown>;
  revenue_simulation: RevenueSimulation;
  charts: Record<string, unknown>;
  provenance: {
    mode?: string;
    transport?: string;
    sources?: string[];
    used_real_data?: boolean;
    used_mock_data?: boolean;
    warnings?: string[];
    status?: "complete" | "degraded";
    api_calls?: number;
    cache_hits?: number;
    upstream_latency_ms?: number;
    operations?: Array<{ tool: string; source: string; api_calls: number; cache_hits: number; latency_ms: number; message?: string }>;
    sample_scope?: string;
  };
  evidence_quality?: EvidenceQuality;
  errors: string[];
  report_markdown: string;
}

export interface EvidenceQuality {
  score: number;
  grade: "A" | "B" | "C" | "D";
  factors: Array<{ name: string; score: number; max_score: number; note: string }>;
  limitations: string[];
  method: string;
}

export interface RevenueScenario {
  id: string;
  name: string;
  average_ticket: number;
  market_share: number;
  daily_orders: number;
  daily_revenue: number;
  monthly_revenue: number;
  monthly_profit: number;
  break_even_orders_per_day: number;
  daily_series: Array<{ name: string; orders: number; revenue: number }>;
}

export interface RevenueSimulation {
  model?: string;
  viability_status?: "viable" | "not_viable";
  recommendation_message?: string;
  recommended_strategy?: string;
  recommended_strategy_name?: string;
  base_revenue?: {
    daily_orders?: number;
    daily_revenue?: number;
    monthly_revenue?: number;
    monthly_profit?: number;
    break_even_orders_per_day?: number;
  };
  scenario_simulations?: RevenueScenario[];
  assumptions?: Record<string, number | boolean | string>;
  risk_assessment?: string[];
}

export interface AnalyzeRequest {
  store_name: string;
  store_address: string;
  store_type: string;
  analysis_radius: number;
  location?: string;
  deep_analysis: boolean;
  use_llm: boolean;
  avg_ticket?: number;
  seat_count?: number;
  daily_fixed_cost?: number;
  variable_cost_rate?: number;
}

interface AnalyzeResponse {
  success: boolean;
  status: "complete" | "degraded";
  message: string;
  report_markdown: string;
  data: ReportData;
}

export interface CandidateSiteInput {
  candidate_id: string;
  name: string;
  address: string;
  location?: string;
}

export interface ComparisonWeights {
  demand_potential: number;
  accessibility: number;
  competitive_headroom: number;
  profitability: number;
  evidence_quality: number;
}

export interface CompareRequest {
  candidates: CandidateSiteInput[];
  store_type: string;
  analysis_radius: number;
  avg_ticket?: number;
  seat_count?: number;
  daily_fixed_cost?: number;
  variable_cost_rate?: number;
  weights: ComparisonWeights;
  require_viable: boolean;
  minimum_evidence_score: number;
}

export interface RankedCandidate {
  candidate_id: string;
  candidate_name: string;
  candidate_address: string;
  rank: number | null;
  score: number;
  eligible: boolean;
  disqualifiers: string[];
  strengths: string[];
  risks: string[];
  status: "complete" | "degraded";
  viability_status: "viable" | "not_viable";
  best_monthly_profit: number;
  competitor_count: number;
  evidence_quality: EvidenceQuality;
  raw_metrics: ComparisonWeights;
  criteria: Record<
    keyof ComparisonWeights,
    {
      label: string;
      raw_value: number;
      normalized_score: number;
      weight: number;
      contribution: number;
    }
  >;
  provenance: {
    used_real_data: boolean;
    used_mock_data: boolean;
    sources: string[];
    api_calls: number;
    upstream_latency_ms: number;
  };
  errors: string[];
}

export interface CompareResultData {
  request_id: string;
  status: "complete" | "degraded";
  store_type: string;
  analysis_radius: number;
  screening_mode: "deterministic_no_llm";
  successful_candidate_count: number;
  failed_candidates: Array<{
    candidate_id: string;
    candidate_name: string;
    candidate_address: string;
    error: string;
  }>;
  decision_status: "recommended" | "relative_ranking_only" | "no_eligible_candidate";
  message: string;
  recommended_candidate_id: string | null;
  best_available_candidate_id: string;
  weights: ComparisonWeights;
  ranking: RankedCandidate[];
  sensitivity: {
    scenario_count: number;
    top_pick_rate: Record<string, number>;
    leader_candidate_id: string | null;
    leader_pick_rate: number;
    recommended_pick_rate: number;
    level: "high" | "medium" | "low" | "not_applicable";
    note: string;
  };
  warnings: string[];
  validation_plan: Array<{ stage: string; action: string; success_metric: string }>;
}

interface CompareResponse {
  success: boolean;
  status: "complete" | "degraded";
  message: string;
  data: CompareResultData;
}

export interface AppSettings {
  apiEndpoint: string;
  analysisRadius: number;
  theme: "light" | "dark" | "system";
  apiAccessToken: string;
}

const DEFAULT_API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const SETTINGS_KEY = "restaurant-agent-settings-v1";
const ACCESS_TOKEN_KEY = "restaurant-agent-access-token-v1";

export function getSettings(): AppSettings {
  const defaults: AppSettings = { apiEndpoint: DEFAULT_API, analysisRadius: 1000, theme: "system", apiAccessToken: "" };
  if (typeof window === "undefined") return defaults;
  try {
    return {
      ...defaults,
      ...JSON.parse(window.localStorage.getItem(SETTINGS_KEY) || "{}"),
      apiAccessToken: window.sessionStorage.getItem(ACCESS_TOKEN_KEY) || "",
    };
  } catch {
    return defaults;
  }
}

export function saveSettings(settings: AppSettings): void {
  const { apiAccessToken, ...persisted } = settings;
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(persisted));
  if (apiAccessToken) window.sessionStorage.setItem(ACCESS_TOKEN_KEY, apiAccessToken);
  else window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function applyTheme(theme: AppSettings["theme"]): void {
  if (theme === "system") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.dataset.theme = theme;
}

function requestHeaders(settings = getSettings()): Record<string, string> {
  return settings.apiAccessToken ? { "X-API-Key": settings.apiAccessToken } : {};
}

async function readJson<T>(response: Response): Promise<T> {
  const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload as T;
}

export async function analyzeStore(request: AnalyzeRequest, externalSignal?: AbortSignal): Promise<AnalyzeResponse> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  externalSignal?.addEventListener("abort", abort, { once: true });
  const timeout = window.setTimeout(() => controller.abort(), 190_000);
  const settings = getSettings();
  try {
    const response = await fetch(`${settings.apiEndpoint}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...requestHeaders(settings) },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    return await readJson<AnalyzeResponse>(response);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      if (externalSignal?.aborted) throw new Error("分析已取消");
      throw new Error("分析超过 190 秒，请稍后重试或关闭 LLM 深度解释");
    }
    throw error;
  } finally {
    externalSignal?.removeEventListener("abort", abort);
    window.clearTimeout(timeout);
  }
}

export async function compareSites(
  request: CompareRequest,
  externalSignal?: AbortSignal
): Promise<CompareResponse> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  externalSignal?.addEventListener("abort", abort, { once: true });
  const timeout = window.setTimeout(() => controller.abort(), 420_000);
  const settings = getSettings();
  try {
    const response = await fetch(`${settings.apiEndpoint}/api/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...requestHeaders(settings) },
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    return await readJson<CompareResponse>(response);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      if (externalSignal?.aborted) throw new Error("候选点比较已取消");
      throw new Error("候选点比较超过 7 分钟，请减少候选点或稍后重试");
    }
    throw error;
  } finally {
    externalSignal?.removeEventListener("abort", abort);
    window.clearTimeout(timeout);
  }
}

export async function geocodeAddress(address: string): Promise<{
  location: { location: string; formatted_address?: string; business_area?: string; matched_poi?: string };
  provenance: ReportData["provenance"];
}> {
  const settings = getSettings();
  const response = await fetch(`${settings.apiEndpoint}/api/geocode?address=${encodeURIComponent(address)}`, { headers: requestHeaders(settings) });
  return readJson(response);
}

export async function reverseGeocode(coordinates: string): Promise<{
  location: { formatted_address?: string };
  provenance: ReportData["provenance"];
}> {
  const settings = getSettings();
  const response = await fetch(`${settings.apiEndpoint}/api/reverse-geocode?location=${encodeURIComponent(coordinates)}`, { headers: requestHeaders(settings) });
  return readJson(response);
}

export async function getHealth(settings = getSettings()): Promise<Record<string, unknown>> {
  const response = await fetch(`${settings.apiEndpoint}/api/health`, { headers: requestHeaders(settings) });
  return readJson(response);
}
