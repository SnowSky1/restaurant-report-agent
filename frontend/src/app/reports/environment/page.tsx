"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Building2, GraduationCap, HeartPulse, Home, ShoppingBag, Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { PieChart } from "@/components/ui/Chart";
import { useReport } from "@/context/ReportContext";

const icons = { 写字楼: Building2, 住宅: Home, 商场: ShoppingBag, 学校: GraduationCap, 医院: HeartPulse };

export default function EnvironmentPage() {
  const { reportData } = useReport();
  if (!reportData) return <Empty />;
  const counts = reportData.poi_analysis.poi_counts || {};
  const details = reportData.poi_analysis.poi_details || [];
  return (
    <div className="space-y-8 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}><h1 className="flex items-center gap-3 text-3xl font-bold"><Users className="h-8 w-8 text-system-blue" />商业环境</h1><p className="mt-2 text-system-gray">{reportData.poi_analysis.poi_summary || "周边设施样本分析"}</p></motion.div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">{Object.entries(counts).map(([name, value]) => { const Icon = icons[name as keyof typeof icons] || Building2; return <Card key={name}><CardHeader className="flex flex-row items-center justify-between pb-2"><CardTitle className="text-sm">{name}</CardTitle><Icon className="h-4 w-4 text-system-blue" /></CardHeader><CardContent><p className="text-3xl font-bold">{value}</p><p className="mt-1 text-xs text-system-gray">单页 POI 样本</p></CardContent></Card>; })}</div>
      <div className="grid gap-6 lg:grid-cols-5"><Card className="lg:col-span-2"><CardHeader><CardTitle>样本结构</CardTitle><CardDescription>只反映本次 API 返回样本，不等于人口统计</CardDescription></CardHeader><CardContent className="h-[340px]">{reportData.pieChartData.length ? <PieChart data={reportData.pieChartData} /> : <div className="flex h-full items-center justify-center text-system-gray">暂无数据</div>}</CardContent></Card><Card className="lg:col-span-3"><CardHeader><CardTitle>代表性设施</CardTitle><CardDescription>按分类最多展示五个最近结果</CardDescription></CardHeader><CardContent className="grid max-h-[340px] gap-3 overflow-y-auto sm:grid-cols-2">{details.map((row, index) => <div key={`${String(row.name)}-${index}`} className="rounded-xl border border-[var(--glass-border)] p-3"><div className="flex items-center justify-between gap-2"><p className="font-medium">{String(row.name || "未命名")}</p><span className="rounded-full bg-system-blue/10 px-2 py-0.5 text-xs text-system-blue">{String(row.category || "其他")}</span></div><p className="mt-2 text-xs text-system-gray">约 {String(row.distance || "-")} 米 · {String(row.source || "unknown")}</p></div>)}</CardContent></Card></div>
    </div>
  );
}

function Empty() { return <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5 text-center"><Users className="h-12 w-12 text-system-gray-3" /><p className="text-system-gray">请先在首页生成报告</p><Link href="/" className="rounded-xl bg-system-blue px-6 py-2.5 text-white">返回首页</Link></div>; }
