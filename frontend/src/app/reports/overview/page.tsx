"use client";

import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";
import { AlertTriangle, FileText, MapPin } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { useReport } from "@/context/ReportContext";

export default function OverviewPage() {
  const { reportData } = useReport();
  if (!reportData) return <EmptyReport />;

  return (
    <div className="space-y-6 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="flex items-center gap-3 text-3xl font-bold"><FileText className="h-8 w-8 text-system-blue" />完整经营报告</h1>
        <p className="mt-2 flex items-center gap-2 text-system-gray"><MapPin className="h-4 w-4" />{reportData.location.address || reportData.storeAddress}</p>
      </motion.div>
      {reportData.provenance.used_mock_data && <div className="flex gap-3 rounded-2xl border border-system-orange/20 bg-system-orange/5 p-4 text-sm"><AlertTriangle className="h-5 w-5 shrink-0 text-system-orange" /><div><p className="font-medium text-system-orange">报告含模拟回退数据</p><p className="mt-1 text-system-gray">{reportData.provenance.warnings?.join("；")}</p></div></div>}
      <Card><CardHeader><CardTitle>{reportData.storeName}</CardTitle></CardHeader><CardContent><article className="report-markdown"><ReactMarkdown remarkPlugins={[remarkGfm]}>{reportData.report_markdown}</ReactMarkdown></article></CardContent></Card>
    </div>
  );
}

function EmptyReport() {
  return <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5 text-center"><FileText className="h-12 w-12 text-system-gray-3" /><div><h2 className="text-xl font-semibold">暂无报告</h2><p className="mt-2 text-sm text-system-gray">请先从首页运行一次完整分析</p></div><Link href="/" className="rounded-xl bg-system-blue px-6 py-2.5 font-medium text-white">返回首页</Link></div>;
}
