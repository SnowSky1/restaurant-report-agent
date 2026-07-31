"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  BarChart3,
  MapPin,
  Users,
  CloudSun,
  FileText,
  Settings,
} from "lucide-react";

const navigation = [
  { name: "总览报告", href: "/reports/overview", icon: FileText },
  { name: "位置交通", href: "/reports/location", icon: MapPin },
  { name: "商业环境", href: "/reports/environment", icon: Users },
  { name: "天气影响", href: "/reports/weather", icon: CloudSun },
  { name: "竞争分析", href: "/reports/competitors", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 flex-col gap-4 border-r border-solid border-[var(--glass-border)] bg-background/50 px-4 py-6">
      <div className="flex-1 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-system-blue text-white shadow-sm"
                  : "text-system-gray hover:bg-system-gray-6 hover:text-foreground"
              )}
            >
              <item.icon className={cn("h-4 w-4", isActive ? "text-white" : "text-system-gray")} />
              {item.name}
            </Link>
          );
        })}
      </div>
      <div className="mt-auto">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-system-gray hover:bg-system-gray-6 hover:text-foreground transition-all duration-200"
        >
          <Settings className="h-4 w-4 text-system-gray" />
          系统设置
        </Link>
      </div>
    </aside>
  );
}
