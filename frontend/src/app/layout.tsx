import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: "餐饮店经营分析报告",
  description: "基于人工智能的餐饮店多维度经营分析报告",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased min-h-screen flex flex-col">
        <Providers>
          <Navbar />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto bg-background p-4 md:p-8">
              <div className="mx-auto max-w-6xl">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
