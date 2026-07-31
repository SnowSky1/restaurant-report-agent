"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, BadgeDollarSign, BarChart3, ShieldCheck, Target } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { RevenueChart } from "@/components/ui/Chart";
import { useReport } from "@/context/ReportContext";

function record(value: unknown): Record<string, unknown> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {}; }
function rows(value: unknown): Array<Record<string, unknown>> { return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object") : []; }

export default function CompetitorsPage() {
  const { reportData } = useReport();
  if (!reportData) return <Empty />;
  const analysis = reportData.competition_analysis;
  const intensity = record(analysis.competition_intensity);
  const position = record(analysis.market_position);
  const pricing = record(analysis.pricing_strategy);
  const threats = rows(analysis.competitive_threats);
  const actions = rows(analysis.action_plan);
  const revenue = reportData.revenue_simulation;
  const scenarios = revenue.scenario_simulations || [];
  return (
    <div className="space-y-8 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}><h1 className="flex items-center gap-3 text-3xl font-bold"><BarChart3 className="h-8 w-8 text-system-orange" />竞争、定价与营收</h1><p className="mt-2 text-system-gray">CompeteAI 启发的规则分析、LLM 解释与多智能体情景模拟</p></motion.div>
      <div className="grid gap-4 md:grid-cols-3"><Card><CardHeader><CardTitle className="text-sm">竞争强度</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{String(intensity.score ?? reportData.competition_score)}/10</p><p className="mt-1 text-sm text-system-gray">{String(intensity.level ?? "-")} · {reportData.competitor_count} 家样本</p></CardContent></Card><Card><CardHeader><CardTitle className="text-sm">建议定位</CardTitle></CardHeader><CardContent><p className="text-xl font-semibold">{String(position.recommended ?? "待验证")}</p><p className="mt-1 text-xs text-system-gray">{String(position.target_segment ?? "-")}</p></CardContent></Card><Card><CardHeader><CardTitle className="text-sm">推荐经营情景</CardTitle></CardHeader><CardContent><p className="text-xl font-semibold text-system-green">{revenue.recommended_strategy_name || "均衡经营"}</p><p className="mt-1 text-xs text-system-gray">情景模型，不是财务承诺</p></CardContent></Card></div>
      <div className="grid gap-6 lg:grid-cols-5"><Card className="lg:col-span-3"><CardHeader><CardTitle>营收与利润情景</CardTitle><CardDescription>价格变化后，竞争者将进行三轮小幅响应</CardDescription></CardHeader><CardContent className="h-[360px]">{scenarios.length ? <RevenueChart scenarios={scenarios} /> : <div className="flex h-full items-center justify-center text-system-gray">暂无模拟结果</div>}</CardContent></Card><Card className="lg:col-span-2"><CardHeader><CardTitle className="flex items-center gap-2"><BadgeDollarSign className="h-5 w-5 text-system-green" />定价建议</CardTitle></CardHeader><CardContent className="space-y-4"><p className="leading-7">{String(pricing.current_assessment ?? "暂无竞品公开价格")}</p><div className="rounded-xl bg-system-blue/5 p-4 text-sm">{String(pricing.recommendation ?? "请以真实成本和转化数据校准")}</div></CardContent></Card></div>
      <Card><CardHeader><CardTitle>附近竞争门店</CardTitle><CardDescription>按距离排序的高德 POI 样本</CardDescription></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[720px] text-left text-sm"><thead><tr className="border-b border-[var(--glass-border)] text-system-gray"><th className="p-3">门店</th><th className="p-3">距离</th><th className="p-3">评分</th><th className="p-3">公开人均</th><th className="p-3">地址</th></tr></thead><tbody>{reportData.competitors.map((item, index) => <tr key={`${item.name}-${index}`} className="border-b border-[var(--glass-border)]/60"><td className="p-3 font-medium">{item.name}</td><td className="p-3">{item.distance || "-"} 米</td><td className="p-3">{item.rating || "-"}</td><td className="p-3">{item.average_cost ? `¥${item.average_cost}` : "-"}</td><td className="p-3 text-system-gray">{item.address || "-"}</td></tr>)}</tbody></table></CardContent></Card>
      <div className="grid gap-6 lg:grid-cols-2"><Card><CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-system-orange" />主要威胁</CardTitle></CardHeader><CardContent className="space-y-3">{threats.map((threat, index) => <div key={index} className="rounded-xl border border-system-orange/20 bg-system-orange/5 p-4"><p className="font-medium">{String(threat.threat ?? "竞争风险")}</p><p className="mt-1 text-xs text-system-gray">{String(threat.source ?? "-")} · {String(threat.severity ?? "-")}</p></div>)}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-5 w-5 text-system-blue" />行动计划</CardTitle></CardHeader><CardContent className="space-y-3">{actions.map((action, index) => <div key={index} className="flex gap-3 rounded-xl border border-[var(--glass-border)] p-4"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-system-blue text-xs font-bold text-white">{String(action.priority ?? index + 1)}</span><div><p className="font-medium">{String(action.action ?? "-")}</p><p className="mt-1 text-xs text-system-gray">{String(action.timeline ?? "-")} · {String(action.expected_roi ?? "-")}</p></div></div>)}</CardContent></Card></div>
      <Card><CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-system-purple" />模型边界</CardTitle></CardHeader><CardContent><ul className="list-disc space-y-2 pl-5 text-sm text-system-gray">{(revenue.risk_assessment || []).map((risk) => <li key={risk}>{risk}</li>)}</ul></CardContent></Card>
    </div>
  );
}

function Empty() { return <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5 text-center"><BarChart3 className="h-12 w-12 text-system-gray-3" /><p className="text-system-gray">请先在首页生成报告</p><Link href="/" className="rounded-xl bg-system-blue px-6 py-2.5 text-white">返回首页</Link></div>; }
