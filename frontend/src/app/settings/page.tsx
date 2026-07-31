"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, CircleAlert, KeyRound, Loader2, MapPin, Save, Server, Settings } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { applyTheme, getHealth, getSettings, saveSettings, type AppSettings } from "@/lib/api";

export default function SettingsPage() {
  const [form, setForm] = useState<AppSettings>({ apiEndpoint: "http://127.0.0.1:8000", analysisRadius: 1000, theme: "system", apiAccessToken: "" });
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [checking, setChecking] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refreshHealth = async (target = form) => {
    setChecking(true);
    try { setHealth(await getHealth(target)); setMessage(null); }
    catch (error) { setHealth(null); setMessage(error instanceof Error ? error.message : "后端连接失败"); }
    finally { setChecking(false); }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const saved = getSettings();
      setForm(saved);
      applyTheme(saved.theme);
      setChecking(true);
      void getHealth(saved)
        .then((result) => { setHealth(result); setMessage(null); })
        .catch((error) => { setHealth(null); setMessage(error instanceof Error ? error.message : "后端连接失败"); })
        .finally(() => setChecking(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const save = () => {
    saveSettings(form);
    applyTheme(form.theme);
    setMessage("设置已保存在当前浏览器");
    window.setTimeout(() => setMessage(null), 2500);
  };

  return (
    <div className="space-y-8 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}><h1 className="flex items-center gap-3 text-3xl font-bold"><Settings className="h-8 w-8 text-system-gray" />系统设置</h1><p className="mt-2 text-system-gray">浏览器连接参数与后端只读状态</p></motion.div>
      <Card><CardHeader><CardTitle className="flex items-center gap-2"><Server className="h-5 w-5 text-system-blue" />后端连接</CardTitle><CardDescription>上游服务密钥只保存在后端；这里的访问令牌仅在后端启用鉴权时填写</CardDescription></CardHeader><CardContent className="space-y-4"><div className="grid gap-4 md:grid-cols-2"><label className="block space-y-2"><span className="text-sm font-medium">FastAPI 地址</span><input value={form.apiEndpoint} onChange={(event) => setForm({ ...form, apiEndpoint: event.target.value.replace(/\/$/, "") })} className="field" /></label><label className="block space-y-2"><span className="text-sm font-medium">API 访问令牌（可选）</span><input type="password" autoComplete="off" value={form.apiAccessToken} onChange={(event) => setForm({ ...form, apiAccessToken: event.target.value })} className="field" /></label></div><div className="flex items-center justify-between rounded-xl bg-system-gray-6/50 p-4"><div>{health ? <><p className="flex items-center gap-2 font-medium text-system-green"><CheckCircle className="h-4 w-4" />后端在线</p><p className="mt-1 text-xs text-system-gray">版本 {String(health.version || "-")} · {String(health.llm_provider || "-")}/{String(health.llm_model || "-")} · 数据模式 {String(health.data_mode || "-")}</p></> : <><p className="flex items-center gap-2 font-medium text-system-orange"><CircleAlert className="h-4 w-4" />尚未连接</p><p className="mt-1 text-xs text-system-gray">请确认后端已经启动</p></>}</div><button onClick={() => void refreshHealth(form)} disabled={checking} className="rounded-xl border border-[var(--glass-border)] px-4 py-2 text-sm font-medium">{checking ? <Loader2 className="h-4 w-4 animate-spin" /> : "检测当前地址"}</button></div></CardContent></Card>
      <div className="grid gap-6 md:grid-cols-3"><Card><CardHeader><CardTitle className="flex items-center gap-2"><MapPin className="h-5 w-5 text-system-green" />默认分析半径</CardTitle></CardHeader><CardContent><select value={form.analysisRadius} onChange={(event) => setForm({ ...form, analysisRadius: Number(event.target.value) })} className="field"><option value={500}>500 米</option><option value={800}>800 米</option><option value={1000}>1000 米</option><option value={1500}>1500 米</option><option value={2000}>2000 米</option></select></CardContent></Card><Card><CardHeader><CardTitle>显示主题</CardTitle></CardHeader><CardContent><select value={form.theme} onChange={(event) => setForm({ ...form, theme: event.target.value as AppSettings["theme"] })} className="field"><option value="system">跟随系统</option><option value="light">浅色</option><option value="dark">深色</option></select></CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2"><KeyRound className="h-5 w-5 text-system-purple" />服务配置</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><Status label="高德 Web 服务" ok={Boolean(health?.amap_configured)} /><Status label="LLM" ok={Boolean(health?.llm_configured)} /><Status label="Krill 备用" ok={Boolean(health?.krill_fallback_configured)} /></CardContent></Card></div>
      {message && <p role="status" className="rounded-xl bg-system-blue/5 p-3 text-sm text-system-blue">{message}</p>}
      <div className="flex justify-end"><button onClick={save} className="flex items-center gap-2 rounded-xl bg-system-blue px-6 py-3 font-medium text-white"><Save className="h-5 w-5" />保存设置</button></div>
    </div>
  );
}

function Status({ label, ok }: { label: string; ok: boolean }) { return <div className="flex items-center justify-between rounded-xl border border-[var(--glass-border)] px-4 py-3"><span>{label}</span><span className={ok ? "text-system-green" : "text-system-orange"}>{ok ? "已配置" : "未配置"}</span></div>; }
