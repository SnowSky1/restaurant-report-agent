"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { AlertCircle, AlertTriangle, ArrowRight, CloudSun, Database, Loader2, MapPin, Navigation, Store, TrendingUp, Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { LineChart, PieChart, RevenueChart } from "@/components/ui/Chart";
import { useReport } from "@/context/ReportContext";
import { analyzeStore, getSettings, type AnalyzeRequest } from "@/lib/api";
import { validateSimulationInputs } from "@/lib/validation";

const MapSelector = dynamic(() => import("@/components/ui/MapSelector").then((module) => module.MapSelector), { ssr: false });

const item: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 280, damping: 24 } },
};

function LoadingState() {
  return (
    <div className="flex min-h-[48vh] flex-col items-center justify-center gap-6">
      <Loader2 className="h-11 w-11 animate-spin text-system-blue" />
      <div className="text-center"><h3 className="text-lg font-medium">正在运行完整分析图</h3><p className="mt-2 text-sm text-system-gray">真实地图数据、竞争分析、营收模拟与报告生成可能需要 20–90 秒</p></div>
    </div>
  );
}

export default function Home() {
  const { reportData, setReportData, isLoading, setIsLoading } = useReport();
  const [showMap, setShowMap] = useState(false);
  const [showAssumptions, setShowAssumptions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storeName, setStoreName] = useState("星巴克咖啡（建国路店）");
  const [storeAddress, setStoreAddress] = useState("北京市朝阳区建国路88号SOHO现代城");
  const [storeType, setStoreType] = useState("咖啡店");
  const [radius, setRadius] = useState(1000);
  const [location, setLocation] = useState<string | null>(null);
  const [deepAnalysis, setDeepAnalysis] = useState(true);
  const [useLlm, setUseLlm] = useState(true);
  const [avgTicket, setAvgTicket] = useState("");
  const [seatCount, setSeatCount] = useState("");
  const [dailyFixedCost, setDailyFixedCost] = useState("");
  const [variableCostRate, setVariableCostRate] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setRadius(getSettings().analysisRadius), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const handleAnalyze = async () => {
    if (!storeName.trim() || !storeAddress.trim()) {
      setError("请填写店铺名称和地址");
      return;
    }
    setReportData(null);
    let parsed: Pick<AnalyzeRequest, "avg_ticket" | "seat_count" | "daily_fixed_cost" | "variable_cost_rate">;
    try {
      parsed = validateSimulationInputs({ avgTicket, seatCount, dailyFixedCost, variableCostRate });
    } catch (validationError) {
      setError(validationError instanceof Error ? validationError.message : "模拟假设输入无效");
      return;
    }
    setError(null);
    setIsLoading(true);
    const request: AnalyzeRequest = {
      store_name: storeName.trim(),
      store_address: storeAddress.trim(),
      store_type: storeType,
      analysis_radius: radius,
      deep_analysis: deepAnalysis,
      use_llm: useLlm,
    };
    if (location) request.location = location;
    Object.assign(request, parsed);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const result = await analyzeStore(request, controller.signal);
      setReportData({ ...result.data, report_markdown: result.report_markdown });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "分析请求失败");
    } finally {
      abortRef.current = null;
      setIsLoading(false);
    }
  };

  const handleCancel = () => abortRef.current?.abort();

  const handleMapSelect = (selected: { lng: number; lat: number; address: string }) => {
    setLocation(`${selected.lng.toFixed(6)},${selected.lat.toFixed(6)}`);
    if (selected.address && !selected.address.includes(",")) setStoreAddress(selected.address);
  };

  const scenarios = reportData?.revenue_simulation?.scenario_simulations || [];
  const revenue = reportData?.revenue_simulation?.base_revenue;

  return (
    <div className="space-y-8 pb-12">
      <AnimatePresence>{showMap && <MapSelector initialAddress={storeAddress} onClose={() => setShowMap(false)} onSelect={handleMapSelect} />}</AnimatePresence>

      <section className="space-y-3 pt-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-system-blue/20 bg-system-blue/10 px-3 py-1 text-xs font-medium text-system-blue"><Database className="h-3.5 w-3.5" />LangGraph · 高德真实数据优先 · CompeteAI 情景模拟</div>
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">餐饮经营分析工作台</h1>
        <p className="max-w-3xl text-system-gray">输入门店与成本假设，生成位置、交通、客群、竞争、定价和营收情景报告。模拟数据会被明确标注，不会伪装成实时结果。</p>
      </section>

      <Card className="overflow-hidden border-none bg-gradient-to-br from-system-blue/10 via-transparent to-system-purple/5 shadow-sm">
        <CardContent className="space-y-5 p-6 md:p-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <label className="space-y-2"><span className="text-sm font-medium">店铺名称</span><input value={storeName} onChange={(event) => setStoreName(event.target.value)} className="field" /></label>
            <label className="space-y-2 lg:col-span-2"><span className="text-sm font-medium">店铺地址</span><div className="flex gap-2"><input value={storeAddress} onChange={(event) => { setStoreAddress(event.target.value); setLocation(null); }} className="field min-w-0 flex-1" /><button aria-label="地图选点" onClick={() => setShowMap(true)} className="rounded-xl border border-[var(--glass-border)] bg-white/80 px-3 text-system-blue shadow-sm hover:bg-white dark:bg-system-gray-6"><Navigation className="h-5 w-5" /></button></div></label>
            <label className="space-y-2"><span className="text-sm font-medium">业态类型</span><select value={storeType} onChange={(event) => setStoreType(event.target.value)} className="field">{["餐厅", "咖啡店", "奶茶店", "火锅店", "烧烤店", "快餐店", "面馆", "西餐厅", "日料店", "韩餐厅", "川菜馆", "粤菜馆", "甜品店", "面包店"].map((type) => <option key={type}>{type}</option>)}</select></label>
          </div>

          <div className="grid gap-4 border-t border-[var(--glass-border)] pt-4 md:grid-cols-4">
            <label className="space-y-2"><span className="text-sm font-medium">分析半径</span><select value={radius} onChange={(event) => setRadius(Number(event.target.value))} className="field"><option value={500}>500 米</option><option value={800}>800 米</option><option value={1000}>1000 米</option><option value={1500}>1500 米</option><option value={2000}>2000 米</option></select></label>
            <label className="flex items-center gap-3 rounded-xl border border-[var(--glass-border)] px-4 py-3"><input type="checkbox" checked={deepAnalysis} onChange={(event) => setDeepAnalysis(event.target.checked)} className="h-4 w-4 accent-system-blue" /><span><span className="block text-sm font-medium">深度竞争分析</span><span className="text-xs text-system-gray">启用 CompeteAI 节点</span></span></label>
            <label className="flex items-center gap-3 rounded-xl border border-[var(--glass-border)] px-4 py-3"><input type="checkbox" checked={useLlm} onChange={(event) => setUseLlm(event.target.checked)} className="h-4 w-4 accent-system-blue" /><span><span className="block text-sm font-medium">LLM 解释</span><span className="text-xs text-system-gray">使用后端配置模型，失败时规则回退</span></span></label>
            <button onClick={isLoading ? handleCancel : handleAnalyze} className={`rounded-xl px-6 py-3 font-medium text-white shadow-md transition-all active:scale-[0.98] ${isLoading ? "bg-system-red hover:opacity-90" : "bg-system-blue hover:bg-blue-600"}`}>{isLoading ? "取消分析" : "开始完整分析"}</button>
          </div>

          <button onClick={() => setShowAssumptions((value) => !value)} className="text-sm font-medium text-system-blue">{showAssumptions ? "收起" : "展开"}营收模拟假设（可选）</button>
          <AnimatePresence>{showAssumptions && <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="grid gap-4 overflow-hidden md:grid-cols-4"><label className="space-y-2"><span className="text-xs text-system-gray">平均客单价（元）</span><input value={avgTicket} onChange={(event) => setAvgTicket(event.target.value)} inputMode="decimal" className="field" placeholder="留空使用业态默认" /></label><label className="space-y-2"><span className="text-xs text-system-gray">座位数</span><input value={seatCount} onChange={(event) => setSeatCount(event.target.value)} inputMode="numeric" className="field" placeholder="留空使用默认" /></label><label className="space-y-2"><span className="text-xs text-system-gray">日固定成本（元）</span><input value={dailyFixedCost} onChange={(event) => setDailyFixedCost(event.target.value)} inputMode="decimal" className="field" placeholder="租金、人工等" /></label><label className="space-y-2"><span className="text-xs text-system-gray">变动成本率</span><input value={variableCostRate} onChange={(event) => setVariableCostRate(event.target.value)} inputMode="decimal" className="field" placeholder="例如 0.4 或 40" /></label></motion.div>}</AnimatePresence>
          {location && <p className="flex items-center gap-2 text-xs text-system-gray"><MapPin className="h-3.5 w-3.5" />已选择精确坐标：{location}</p>}
          {error && <div role="alert" className="flex items-start gap-3 rounded-xl border border-system-red/20 bg-system-red/5 p-4 text-sm text-system-red"><AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />{error}</div>}
        </CardContent>
      </Card>

      <AnimatePresence mode="wait">
        {isLoading ? <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><LoadingState /></motion.div> : reportData ? (
          <motion.div key={reportData.run_id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><h2 className="text-3xl font-bold tracking-tight">{reportData.storeName}</h2><p className="mt-2 flex items-center gap-2 text-system-gray"><MapPin className="h-4 w-4" />{reportData.location.address || reportData.storeAddress}</p></div><div className={`inline-flex items-center gap-2 self-start rounded-full px-3 py-1.5 text-xs font-medium ${reportData.status === "degraded" ? "bg-system-orange/10 text-system-orange" : "bg-system-green/10 text-system-green"}`}>{reportData.status === "degraded" ? <AlertTriangle className="h-3.5 w-3.5" /> : <Database className="h-3.5 w-3.5" />}{reportData.status === "degraded" ? "部分完成·请核对" : "完整真实数据"}</div></div>

            {reportData.status === "degraded" && <div className="rounded-2xl border border-system-orange/20 bg-system-orange/5 p-4 text-sm"><p className="font-medium text-system-orange">本次分析存在缺失、错误或模拟回退</p><p className="mt-1 text-system-gray">{[...(reportData.provenance.warnings || []), ...reportData.errors].slice(0, 5).join("；") || "部分必需数据未完整返回"}</p>{[...(reportData.provenance.warnings || []), ...reportData.errors].length > 5 && <p className="mt-1 text-xs text-system-gray">另有 {[...(reportData.provenance.warnings || []), ...reportData.errors].length - 5} 条，请在完整报告中查看。</p>}</div>}

            <motion.div variants={{ show: { transition: { staggerChildren: 0.08 } } }} initial="hidden" animate="show" className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[{ title: "竞争强度", value: `${reportData.competition_score}/10`, desc: `${reportData.competitor_count} 家同类门店`, icon: AlertTriangle, color: "text-system-orange" }, { title: "交通便利度", value: reportData.traffic_score, desc: reportData.traffic_desc, icon: TrendingUp, color: "text-system-green" }, { title: "商业环境", value: reportData.poi_main_type, desc: reportData.poi_desc, icon: Users, color: "text-system-blue" }, { title: "当前天气", value: reportData.weather_main, desc: reportData.weather_desc, icon: CloudSun, color: "text-system-yellow" }].map((metric) => <motion.div key={metric.title} variants={item}><Card className="h-full"><CardHeader className="flex flex-row items-center justify-between pb-2"><CardTitle className="text-sm font-medium">{metric.title}</CardTitle><metric.icon className={`h-4 w-4 ${metric.color}`} /></CardHeader><CardContent><div className="text-2xl font-bold">{metric.value}</div><p className="mt-1 line-clamp-2 text-xs text-system-gray">{metric.desc}</p></CardContent></Card></motion.div>)}
            </motion.div>

            <div className="grid gap-4 lg:grid-cols-7">
              <Card className="lg:col-span-4"><CardHeader><CardTitle>模拟周营收趋势</CardTitle><CardDescription>{reportData.revenue_simulation.viability_status === "viable" ? "基于可优先验证情景" : "基于相对最优但仍不可行的情景"}，不是历史流水</CardDescription></CardHeader><CardContent className="h-[300px]">{reportData.lineChartData.length ? <LineChart data={reportData.lineChartData} /> : <div className="flex h-full items-center justify-center text-system-gray">暂无趋势数据</div>}</CardContent></Card>
              <Card className="lg:col-span-3"><CardHeader><CardTitle>周边设施样本</CardTitle><CardDescription>高德 POI 单页样本结构</CardDescription></CardHeader><CardContent className="h-[300px]">{reportData.pieChartData.length ? <PieChart data={reportData.pieChartData} /> : <div className="flex h-full items-center justify-center text-system-gray">暂无 POI 数据</div>}</CardContent></Card>
            </div>

            {scenarios.length > 0 && <Card><CardHeader className="flex flex-row items-start justify-between"><div><CardTitle>CompeteAI 定价与营收情景</CardTitle><CardDescription>{reportData.revenue_simulation.recommendation_message || "尚未形成可执行建议"}；基准月营收 ¥{Math.round(revenue?.monthly_revenue || 0).toLocaleString()}，月利润 ¥{Math.round(revenue?.monthly_profit || 0).toLocaleString()}</CardDescription></div></CardHeader><CardContent className="h-[340px]"><RevenueChart scenarios={scenarios} /></CardContent></Card>}

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{[{ href: "/reports/overview", label: "完整报告" }, { href: "/reports/location", label: "位置交通" }, { href: "/reports/environment", label: "商业环境" }, { href: "/reports/weather", label: "天气影响" }, { href: "/reports/competitors", label: "竞争与营收" }].map((link) => <Link key={link.href} href={link.href} className="flex items-center justify-between rounded-xl border border-[var(--glass-border)] bg-[var(--card-bg)] px-4 py-3 text-sm font-medium shadow-sm transition-transform hover:-translate-y-0.5">{link.label}<ArrowRight className="h-4 w-4 text-system-blue" /></Link>)}</div>
          </motion.div>
        ) : <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex min-h-[38vh] flex-col items-center justify-center gap-4 text-center text-system-gray"><div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-system-gray-6"><Store className="h-8 w-8 text-system-gray-4" /></div><div><p className="font-medium text-foreground">尚未生成本次报告</p><p className="mt-1 text-sm">表单已经可用，点击“开始完整分析”即可运行完整工作流</p></div></motion.div>}
      </AnimatePresence>
    </div>
  );
}
