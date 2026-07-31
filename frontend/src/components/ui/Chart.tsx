"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart as RechartsLineChart,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartPoint, RevenueScenario } from "@/lib/api";

const COLORS = ["#007aff", "#34c759", "#ff9500", "#5856d6", "#ff2d55", "#5ac8fa"];
const tooltipStyle = {
  borderRadius: "12px",
  border: "1px solid var(--glass-border)",
  backgroundColor: "var(--card-bg)",
  boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
  color: "var(--foreground)",
};

export function LineChart({ data }: { data: ChartPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={240} initialDimension={{ width: 640, height: 300 }}>
      <RechartsLineChart data={data} margin={{ top: 5, right: 10, left: -8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--glass-border)" />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "var(--system-gray)", fontSize: 12 }} dy={10} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: "var(--system-gray)", fontSize: 12 }} />
        <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: "var(--foreground)" }} formatter={(value) => [`¥${Number(value).toLocaleString()}`, "模拟营收"]} />
        <Line type="monotone" dataKey="value" stroke="#007aff" strokeWidth={3} dot={{ r: 4, fill: "#007aff", strokeWidth: 2, stroke: "var(--card-bg)" }} activeDot={{ r: 6, strokeWidth: 0 }} animationDuration={900} />
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}

export function PieChart({ data }: { data: ChartPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={240} initialDimension={{ width: 480, height: 300 }}>
      <RechartsPieChart>
        <Pie data={data} cx="50%" cy="50%" innerRadius={58} outerRadius={82} paddingAngle={4} dataKey="value" stroke="none" animationDuration={900}>
          {data.map((entry, index) => <Cell key={`${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />)}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
        <Legend verticalAlign="bottom" height={24} />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}

export function RevenueChart({ scenarios }: { scenarios: RevenueScenario[] }) {
  const data = scenarios.map((item) => ({
    name: item.name,
    月营收: Math.round(item.monthly_revenue),
    月利润: Math.round(item.monthly_profit),
  }));
  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={240} initialDimension={{ width: 720, height: 340 }}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--glass-border)" />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} width={72} />
        <Tooltip contentStyle={tooltipStyle} formatter={(value) => `¥${Number(value).toLocaleString()}`} />
        <Legend />
        <Bar dataKey="月营收" fill="#007aff" radius={[6, 6, 0, 0]} />
        <Bar dataKey="月利润" fill="#34c759" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
