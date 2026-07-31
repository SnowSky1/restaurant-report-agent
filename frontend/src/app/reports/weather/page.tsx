"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { CloudRain, CloudSun, Droplets, Sun, Thermometer, Wind } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { useReport } from "@/context/ReportContext";

function value(row: Record<string, string>, key: string, fallback = "-"): string { return row[key] || fallback; }

export default function WeatherPage() {
  const { reportData } = useReport();
  if (!reportData) return <Empty />;
  const current = reportData.weather.current || {};
  const forecast = reportData.weather.forecast || [];
  const rainy = value(current, "weather").includes("雨");
  return (
    <div className="space-y-8 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}><h1 className="flex items-center gap-3 text-3xl font-bold"><CloudSun className="h-8 w-8 text-system-yellow" />天气影响</h1><p className="mt-2 text-system-gray">高德天气与门店经营提示</p></motion.div>
      <div className="grid gap-4 md:grid-cols-4"><Card className="bg-gradient-to-br from-system-yellow/10 to-system-orange/5 md:col-span-2"><CardHeader><CardTitle>当前天气</CardTitle><CardDescription>更新时间 {value(current, "report_time")}</CardDescription></CardHeader><CardContent className="flex items-center gap-5">{rainy ? <CloudRain className="h-16 w-16 text-system-blue" /> : <Sun className="h-16 w-16 text-system-yellow" />}<div><p className="text-4xl font-bold">{value(current, "weather", "未知")}</p><p className="mt-1 text-system-gray">{value(current, "temperature")}°C</p></div></CardContent></Card><Metric title="湿度" value={`${value(current, "humidity")} %`} icon={Droplets} color="text-system-blue" /><Metric title="风况" value={`${value(current, "wind_direction")} ${value(current, "wind_power")}级`} icon={Wind} color="text-system-green" /></div>
      <Card><CardHeader><CardTitle>经营影响</CardTitle></CardHeader><CardContent><p className="leading-7">{reportData.weather.business_impact || "天气影响相对中性"}</p></CardContent></Card>
      <Card><CardHeader><CardTitle>未来天气</CardTitle><CardDescription>来自高德预报或明确标注的回退数据</CardDescription></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{forecast.length ? forecast.map((day, index) => <div key={`${String(day.date)}-${index}`} className="rounded-xl border border-[var(--glass-border)] p-4"><p className="text-sm text-system-gray">{String(day.date || `第${index + 1}天`)}</p><p className="mt-2 text-lg font-semibold">{String(day.dayweather || "未知")}</p><p className="mt-1 text-sm">{String(day.nighttemp || "-")}–{String(day.daytemp || "-")}°C</p><p className="mt-1 text-xs text-system-gray">{String(day.daywind || "-")}风 {String(day.daypower || "-")}级</p></div>) : <p className="text-system-gray">暂无多日预报</p>}</CardContent></Card>
    </div>
  );
}

function Metric({ title, value: displayValue, icon: Icon, color }: { title: string; value: string; icon: typeof Thermometer; color: string }) { return <Card><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-sm"><Icon className={`h-4 w-4 ${color}`} />{title}</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{displayValue}</p></CardContent></Card>; }
function Empty() { return <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5 text-center"><CloudSun className="h-12 w-12 text-system-gray-3" /><p className="text-system-gray">请先在首页生成报告</p><Link href="/" className="rounded-xl bg-system-blue px-6 py-2.5 text-white">返回首页</Link></div>; }
