import Link from "next/link";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full glass">
      <div className="flex h-14 items-center px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="text-xl tracking-tight text-foreground">
            Restaurant<span className="text-system-blue">AI</span>
          </span>
        </Link>
        <nav className="ml-auto flex items-center gap-4 sm:gap-6">
          <Link
            href="/"
            className="text-sm font-medium text-system-gray hover:text-foreground transition-colors"
          >
            首页
          </Link>
          <Link
            href="/reports/overview"
            className="text-sm font-medium text-system-gray hover:text-foreground transition-colors"
          >
            我的报告
          </Link>
          <Link
            href="/settings"
            className="text-sm font-medium text-system-gray hover:text-foreground transition-colors"
          >
            设置
          </Link>
        </nav>
      </div>
    </header>
  );
}
