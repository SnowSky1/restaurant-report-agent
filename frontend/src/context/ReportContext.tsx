"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { ReportData } from "@/lib/api";

interface ReportContextValue {
  reportData: ReportData | null;
  setReportData: (data: ReportData | null) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

// v2 invalidates reports generated before status/viability safeguards existed.
const STORAGE_KEY = "restaurant-agent-last-report-v2";
const ReportContext = createContext<ReportContextValue | undefined>(undefined);

export function ReportProvider({ children }: { children: ReactNode }) {
  const [reportData, setReportDataState] = useState<ReportData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      try {
        const saved = window.sessionStorage.getItem(STORAGE_KEY);
        if (saved) setReportDataState(JSON.parse(saved) as ReportData);
      } catch {
        window.sessionStorage.removeItem(STORAGE_KEY);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const setReportData = useCallback((data: ReportData | null) => {
    setReportDataState(data);
    if (data) window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    else window.sessionStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({ reportData, setReportData, isLoading, setIsLoading }),
    [reportData, setReportData, isLoading],
  );

  return <ReportContext.Provider value={value}>{children}</ReportContext.Provider>;
}

export function useReport(): ReportContextValue {
  const context = useContext(ReportContext);
  if (!context) throw new Error("useReport must be used within a ReportProvider");
  return context;
}

export type { ReportData };
