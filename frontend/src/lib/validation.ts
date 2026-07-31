import type { AnalyzeRequest } from "@/lib/api";

export function positiveNumber(value: string, label: string): number | undefined {
  if (!value.trim()) return undefined;
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) throw new Error(`${label}必须是大于 0 的数字`);
  return number;
}

export function variableRate(value: string): number | undefined {
  const number = positiveNumber(value, "变动成本率");
  if (number === undefined) return undefined;
  const normalized = number >= 1 && number < 100 ? number / 100 : number;
  if (normalized <= 0 || normalized >= 1) throw new Error("变动成本率请输入 0–1 的小数或 1–99 的百分数");
  return normalized;
}

export function validateSimulationInputs(values: {
  avgTicket: string;
  seatCount: string;
  dailyFixedCost: string;
  variableCostRate: string;
}): Pick<AnalyzeRequest, "avg_ticket" | "seat_count" | "daily_fixed_cost" | "variable_cost_rate"> {
  const parsed = {
    avg_ticket: positiveNumber(values.avgTicket, "平均客单价"),
    seat_count: positiveNumber(values.seatCount, "座位数"),
    daily_fixed_cost: positiveNumber(values.dailyFixedCost, "日固定成本"),
    variable_cost_rate: variableRate(values.variableCostRate),
  };
  if (parsed.seat_count !== undefined && !Number.isInteger(parsed.seat_count)) {
    throw new Error("座位数必须是整数");
  }
  return parsed;
}
