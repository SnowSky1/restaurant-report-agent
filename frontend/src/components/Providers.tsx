"use client";

import { ReactNode, useEffect } from "react";
import { ReportProvider } from "@/context/ReportContext";
import { applyTheme, getSettings } from "@/lib/api";

export function Providers({ children }: { children: ReactNode }) {
  useEffect(() => applyTheme(getSettings().theme), []);
  return <ReportProvider>{children}</ReportProvider>;
}
