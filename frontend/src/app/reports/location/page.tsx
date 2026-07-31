"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Bus, Car, MapPin, Navigation, Train } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { useReport } from "@/context/ReportContext";

function text(row: Record<string, unknown>, key: string): string {
  const value = row[key];
  return typeof value === "string" || typeof value === "number" ? String(value) : "-";
}

export default function LocationPage() {
  const { reportData } = useReport();
  if (!reportData) return <Empty />;
  const traffic = reportData.traffic;
  const groups = [
    { title: "地铁站", rows: traffic.subway_stations || [], icon: Train, color: "text-system-blue" },
    { title: "公交站", rows: traffic.bus_stations || [], icon: Bus, color: "text-system-green" },
    { title: "停车场", rows: traffic.parking_lots || [], icon: Car, color: "text-system-orange" },
  ];
  return (
    <div className="space-y-8 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}><h1 className="flex items-center gap-3 text-3xl font-bold"><MapPin className="h-8 w-8 text-system-blue" />位置与交通</h1><p className="mt-2 text-system-gray">{reportData.location.address || reportData.storeAddress}</p></motion.div>
      <div className="grid gap-4 md:grid-cols-3"><Card><CardHeader><CardTitle className="text-sm">坐标</CardTitle></CardHeader><CardContent><p className="text-xl font-semibold">{reportData.location.coordinates || "-"}</p><p className="mt-1 text-xs text-system-gray">{reportData.location.source || "unknown"}</p></CardContent></Card><Card><CardHeader><CardTitle className="text-sm">商圈</CardTitle></CardHeader><CardContent><p className="text-xl font-semibold">{reportData.location.business_area || "待现场确认"}</p><p className="mt-1 text-xs text-system-gray">{reportData.location.district || reportData.location.city}</p></CardContent></Card><Card><CardHeader><CardTitle className="text-sm">综合交通</CardTitle></CardHeader><CardContent><p className="text-xl font-semibold text-system-green">{reportData.traffic_score_value || 0}/10 · {reportData.traffic_score}</p></CardContent></Card></div>
      <Card><CardHeader><CardTitle>交通结论</CardTitle><CardDescription>{traffic.summary || reportData.traffic_desc}</CardDescription></CardHeader><CardContent className="grid gap-3 sm:grid-cols-4">{Object.entries(traffic.traffic_score || {}).map(([name, value]) => <div key={name} className="rounded-xl bg-system-gray-6/60 p-4"><p className="text-xs text-system-gray">{name}</p><p className="mt-1 text-2xl font-bold">{value}/10</p></div>)}</CardContent></Card>
      <div className="grid gap-6 lg:grid-cols-3">{groups.map((group) => <Card key={group.title}><CardHeader><CardTitle className="flex items-center gap-2"><group.icon className={`h-5 w-5 ${group.color}`} />{group.title}</CardTitle><CardDescription>本次检出 {group.rows.length} 个</CardDescription></CardHeader><CardContent className="space-y-3">{group.rows.length ? group.rows.slice(0, 8).map((row, index) => <div key={`${text(row, "id")}-${index}`} className="rounded-xl border border-[var(--glass-border)] p-3"><p className="font-medium">{text(row, "name")}</p><p className="mt-1 text-xs text-system-gray">约 {text(row, "distance")} 米 · {text(row, "address")}</p></div>) : <p className="text-sm text-system-gray">分析半径内未检出该类设施</p>}</CardContent></Card>)}</div>
    </div>
  );
}

function Empty() { return <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5 text-center"><Navigation className="h-12 w-12 text-system-gray-3" /><p className="text-system-gray">请先在首页生成报告</p><Link href="/" className="rounded-xl bg-system-blue px-6 py-2.5 text-white">返回首页</Link></div>; }
