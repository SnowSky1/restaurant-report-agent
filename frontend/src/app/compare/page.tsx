"use client";

import { useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  FlaskConical,
  Plus,
  Scale,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";
import {
  CandidateSiteInput,
  CompareResultData,
  ComparisonWeights,
  compareSites,
} from "@/lib/api";
import { validateSimulationInputs } from "@/lib/validation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

const STORE_TYPES = [
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
];

const WEIGHT_LABELS: Record<keyof ComparisonWeights, string> = {
  demand_potential: "需求潜力",
  accessibility: "交通可达性",
  competitive_headroom: "竞争空间",
  profitability: "利润潜力",
  evidence_quality: "证据质量",
};

const INITIAL_WEIGHTS: Record<keyof ComparisonWeights, number> = {
  demand_potential: 25,
  accessibility: 20,
  competitive_headroom: 15,
  profitability: 30,
  evidence_quality: 10,
};

const initialCandidates: CandidateSiteInput[] = [
  { candidate_id: "A", name: "候选点 A", address: "" },
  { candidate_id: "B", name: "候选点 B", address: "" },
];

export default function ComparePage() {
  const [candidates, setCandidates] = useState(initialCandidates);
  const [storeType, setStoreType] = useState("餐厅");
  const [radius, setRadius] = useState(1000);
  const [weights, setWeights] = useState(INITIAL_WEIGHTS);
  const [requireViable, setRequireViable] = useState(true);
  const [minimumEvidence, setMinimumEvidence] = useState(50);
  const [avgTicket, setAvgTicket] = useState("");
  const [seatCount, setSeatCount] = useState("");
  const [dailyFixedCost, setDailyFixedCost] = useState("");
  const [variableCostRate, setVariableCostRate] = useState("");
  const [result, setResult] = useState<CompareResultData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const weightTotal = useMemo(() => Object.values(weights).reduce((sum, value) => sum + value, 0), [weights]);

  const updateCandidate = (index: number, field: keyof CandidateSiteInput, value: string) => {
    setCandidates((current) => current.map((candidate, itemIndex) => (
      itemIndex === index ? { ...candidate, [field]: value } : candidate
    )));
  };

  const addCandidate = () => {
    if (candidates.length >= 5) return;
    const candidateId = String.fromCharCode(65 + candidates.length);
    setCandidates((current) => [
      ...current,
      { candidate_id: candidateId, name: `候选点 ${candidateId}`, address: "" },
    ]);
  };

  const removeCandidate = (index: number) => {
    if (candidates.length <= 2) return;
    setCandidates((current) => current.filter((_, itemIndex) => itemIndex !== index));
  };

  const handleCompare = async () => {
    setResult(null);
    if (candidates.some((candidate) => candidate.address.trim().length < 2)) {
      setError("请为每个候选点填写可解析的地址");
      return;
    }
    if (weightTotal <= 0) {
      setError("至少一个比较权重必须大于 0");
      return;
    }
    let assumptions: ReturnType<typeof validateSimulationInputs>;
    try {
      assumptions = validateSimulationInputs({
        avgTicket,
        seatCount,
        dailyFixedCost,
        variableCostRate,
      });
    } catch (validationError) {
      setError(validationError instanceof Error ? validationError.message : "经营参数输入无效");
      return;
    }

    setError(null);
    setLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await compareSites(
        {
          candidates: candidates.map((candidate) => ({
            ...candidate,
            name: candidate.name.trim() || `候选点 ${candidate.candidate_id}`,
            address: candidate.address.trim(),
            location: candidate.location?.trim() || undefined,
          })),
          store_type: storeType,
          analysis_radius: radius,
          weights: Object.fromEntries(
            Object.entries(weights).map(([key, value]) => [key, value / 100])
          ) as unknown as ComparisonWeights,
          require_viable: requireViable,
          minimum_evidence_score: minimumEvidence,
          ...assumptions,
        },
        controller.signal
      );
      setResult(response.data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "候选点比较失败");
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  };

  const recommended = result?.ranking.find(
    (candidate) => candidate.candidate_id === result.recommended_candidate_id
  );

  return (
    <div className="space-y-8 pb-12">
      <section className="space-y-3 pt-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-system-purple/20 bg-system-purple/10 px-3 py-1 text-xs font-medium text-system-purple">
          <Scale className="h-3.5 w-3.5" />Evidence-aware MCDA · 不让 LLM 决定排名
        </div>
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">候选点决策台</h1>
        <p className="max-w-3xl text-system-gray">
          用同一业态、半径和经营假设比较 2–5 个候选点。系统执行真实数据初筛、盈利硬闸门和权重扰动，输出可解释排名而非一句主观推荐。
        </p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>一、设置共同分析口径</CardTitle>
          <CardDescription>候选点必须使用相同假设，才是有效的横向比较。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-3">
            <label className="space-y-2">
              <span className="text-sm font-medium">业态类型</span>
              <select value={storeType} onChange={(event) => setStoreType(event.target.value)} className="field">
                {STORE_TYPES.map((type) => <option key={type}>{type}</option>)}
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium">分析半径</span>
              <select value={radius} onChange={(event) => setRadius(Number(event.target.value))} className="field">
                {[500, 800, 1000, 1500, 2000].map((value) => <option key={value} value={value}>{value} 米</option>)}
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium">最低证据质量</span>
              <div className="flex items-center gap-3">
                <input type="range" min="0" max="85" step="5" value={minimumEvidence} onChange={(event) => setMinimumEvidence(Number(event.target.value))} className="min-w-0 flex-1 accent-system-blue" />
                <span className="w-12 text-right font-mono text-sm">{minimumEvidence}</span>
              </div>
            </label>
          </div>
          <details className="rounded-2xl border border-[var(--glass-border)] p-4">
            <summary className="cursor-pointer text-sm font-medium">经营参数校准（强烈建议）</summary>
            <div className="mt-4 grid gap-4 md:grid-cols-4">
              <label className="space-y-2"><span className="text-xs text-system-gray">平均客单价（元）</span><input value={avgTicket} onChange={(event) => setAvgTicket(event.target.value)} className="field" placeholder="留空使用业态默认" /></label>
              <label className="space-y-2"><span className="text-xs text-system-gray">座位数</span><input value={seatCount} onChange={(event) => setSeatCount(event.target.value)} className="field" placeholder="留空使用默认" /></label>
              <label className="space-y-2"><span className="text-xs text-system-gray">日固定成本（元）</span><input value={dailyFixedCost} onChange={(event) => setDailyFixedCost(event.target.value)} className="field" placeholder="租金、人工等" /></label>
              <label className="space-y-2"><span className="text-xs text-system-gray">变动成本率</span><input value={variableCostRate} onChange={(event) => setVariableCostRate(event.target.value)} className="field" placeholder="例如 0.4 或 40" /></label>
            </div>
          </details>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-start justify-between space-y-0">
          <div><CardTitle>二、添加候选点</CardTitle><CardDescription>地址必填；精确坐标可避免同名地址误匹配。</CardDescription></div>
          <button onClick={addCandidate} disabled={candidates.length >= 5} className="inline-flex items-center gap-2 rounded-xl bg-system-blue px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"><Plus className="h-4 w-4" />添加</button>
        </CardHeader>
        <CardContent className="space-y-3">
          {candidates.map((candidate, index) => (
            <div key={candidate.candidate_id} className="grid gap-3 rounded-2xl border border-[var(--glass-border)] p-4 md:grid-cols-[72px_1fr_2fr_1fr_44px] md:items-end">
              <div className="flex h-10 items-center justify-center rounded-xl bg-system-blue/10 font-bold text-system-blue">{candidate.candidate_id}</div>
              <label className="space-y-1"><span className="text-xs text-system-gray">名称</span><input value={candidate.name} onChange={(event) => updateCandidate(index, "name", event.target.value)} className="field" /></label>
              <label className="space-y-1"><span className="text-xs text-system-gray">地址 *</span><input value={candidate.address} onChange={(event) => updateCandidate(index, "address", event.target.value)} className="field" placeholder="例如：北京市朝阳区建国路88号" /></label>
              <label className="space-y-1"><span className="text-xs text-system-gray">经度,纬度（可选）</span><input value={candidate.location || ""} onChange={(event) => updateCandidate(index, "location", event.target.value)} className="field" placeholder="116.400000,39.900000" /></label>
              <button aria-label={`删除候选点 ${candidate.candidate_id}`} onClick={() => removeCandidate(index)} disabled={candidates.length <= 2} className="flex h-10 items-center justify-center rounded-xl text-system-red hover:bg-system-red/10 disabled:opacity-20"><Trash2 className="h-4 w-4" /></button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>三、设置决策权重</CardTitle>
          <CardDescription>权重可不等于 100，后端会自动归一化；当前合计 {weightTotal}。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-x-8 gap-y-4 md:grid-cols-2">
            {(Object.keys(WEIGHT_LABELS) as Array<keyof ComparisonWeights>).map((key) => (
              <label key={key} className="space-y-2">
                <span className="flex justify-between text-sm"><span>{WEIGHT_LABELS[key]}</span><span className="font-mono text-system-blue">{weights[key]}</span></span>
                <input type="range" min="0" max="60" step="5" value={weights[key]} onChange={(event) => setWeights((current) => ({ ...current, [key]: Number(event.target.value) }))} className="w-full accent-system-blue" />
              </label>
            ))}
          </div>
          <label className="flex items-start gap-3 rounded-2xl border border-system-orange/20 bg-system-orange/5 p-4">
            <input type="checkbox" checked={requireViable} onChange={(event) => setRequireViable(event.target.checked)} className="mt-0.5 h-4 w-4 accent-system-orange" />
            <span><span className="block text-sm font-medium">启用盈利与产能排名闸门</span><span className="text-xs text-system-gray">开启后，不可行点也不参与正式排名；关闭后可查看相对排名，但亏损点仍不会被包装成推荐。</span></span>
          </label>
          {error && <div role="alert" className="flex items-start gap-3 rounded-xl border border-system-red/20 bg-system-red/5 p-4 text-sm text-system-red"><AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />{error}</div>}
          <button onClick={loading ? () => abortRef.current?.abort() : handleCompare} className={`w-full rounded-xl px-6 py-3 font-medium text-white shadow-md transition-all ${loading ? "bg-system-red" : "bg-system-blue hover:bg-blue-600"}`}>{loading ? "取消候选点比较" : `比较 ${candidates.length} 个候选点`}</button>
          {loading && <p className="text-center text-xs text-system-gray">正在按同一口径逐点采集；筛选阶段固定关闭 LLM，降低成本与随机性。</p>}
        </CardContent>
      </Card>

      {result && (
        <section className="space-y-6">
          <Card className={recommended ? "border-system-green/30 bg-system-green/5" : "border-system-orange/30 bg-system-orange/5"}>
            <CardContent className="flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between">
              <div className="flex items-start gap-3">
                {recommended ? <CheckCircle2 className="mt-1 h-6 w-6 text-system-green" /> : <XCircle className="mt-1 h-6 w-6 text-system-orange" />}
                <div><p className="text-sm text-system-gray">决策结论</p><h2 className="mt-1 text-2xl font-bold">{recommended ? `优先验证：${recommended.candidate_name}` : result.decision_status === "relative_ranking_only" ? "仅提供相对排名，不输出推荐" : "没有候选点通过硬约束"}</h2><p className="mt-2 max-w-3xl text-sm text-system-gray">{result.message}</p></div>
              </div>
              <div className="rounded-2xl bg-[var(--card-bg)] px-5 py-3 text-center shadow-sm"><p className="text-xs text-system-gray">相对首位稳定性</p><p className="mt-1 text-2xl font-bold">{Math.round((result.sensitivity.leader_pick_rate ?? result.sensitivity.recommended_pick_rate ?? 0) * 100)}%</p><p className="text-xs text-system-gray">不是成功概率</p></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5 text-system-blue" />候选点排名与证据</CardTitle><CardDescription>总分为本批候选点内的相对分，不能跨批次比较。</CardDescription></CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-[980px] text-left text-sm">
                <thead className="border-b border-[var(--glass-border)] text-xs text-system-gray"><tr>{["排名", "候选点", "决策分", "可行性", "证据", "需求/日", "交通", "竞争空间", "最高月利润", "主要判断"].map((title) => <th key={title} className="px-3 py-3 font-medium">{title}</th>)}</tr></thead>
                <tbody>
                  {result.ranking.map((candidate) => (
                    <tr key={candidate.candidate_id} className="border-b border-[var(--glass-border)] align-top last:border-0">
                      <td className="px-3 py-4 text-lg font-bold">{candidate.rank ? `#${candidate.rank}` : "—"}</td>
                      <td className="px-3 py-4"><p className="font-medium">{candidate.candidate_name}</p><p className="mt-1 max-w-48 text-xs text-system-gray">{candidate.candidate_address}</p></td>
                      <td className="px-3 py-4"><span className="text-xl font-bold text-system-blue">{candidate.score}</span><span className="text-xs text-system-gray"> /100</span></td>
                      <td className="px-3 py-4">{candidate.viability_status === "viable" ? <span className="text-system-green">可行</span> : <span className="text-system-red">不可行</span>}</td>
                      <td className="px-3 py-4"><span className="font-medium">{candidate.evidence_quality.grade}</span> · {candidate.evidence_quality.score}</td>
                      <td className="px-3 py-4 font-mono">{Math.round(candidate.raw_metrics.demand_potential)}</td>
                      <td className="px-3 py-4 font-mono">{candidate.raw_metrics.accessibility.toFixed(1)}</td>
                      <td className="px-3 py-4 font-mono">{candidate.raw_metrics.competitive_headroom.toFixed(1)}</td>
                      <td className={`px-3 py-4 font-mono ${candidate.best_monthly_profit >= 0 ? "text-system-green" : "text-system-red"}`}>¥{Math.round(candidate.best_monthly_profit).toLocaleString()}</td>
                      <td className="px-3 py-4"><p className="text-xs text-system-green">{candidate.strengths.join("；")}</p><p className="mt-1 max-w-64 text-xs text-system-orange">{candidate.risks.slice(0, 2).join("；")}</p></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-system-green" />为什么可信</CardTitle></CardHeader><CardContent className="space-y-3 text-sm">{result.warnings.map((warning) => <div key={warning} className="flex gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-system-orange" /><span>{warning}</span></div>)}<div className="rounded-xl bg-system-blue/5 p-3 text-system-gray">权重共测试 {result.sensitivity.scenario_count} 个扰动情景；{result.sensitivity.note}</div></CardContent></Card>
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><FlaskConical className="h-5 w-5 text-system-purple" />下一步验证计划</CardTitle></CardHeader><CardContent className="space-y-4">{result.validation_plan.map((step, index) => <div key={step.stage} className="flex gap-3"><div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-system-purple/10 text-xs font-bold text-system-purple">{index + 1}</div><div><p className="font-medium">{step.stage}</p><p className="mt-1 text-sm text-system-gray">{step.action}</p><p className="mt-1 text-xs text-system-green">验收：{step.success_metric}</p></div></div>)}</CardContent></Card>
          </div>
        </section>
      )}
    </div>
  );
}
