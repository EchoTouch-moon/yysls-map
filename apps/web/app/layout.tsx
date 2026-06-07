import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "燕云卷宗 · 剧情关系图谱",
  description: "用关系图与时间线读懂燕云十六声的角色、势力和暗线。",
};

const links = [
  { href: "/graph", label: "关系图谱" },
  { href: "/timeline", label: "剧情时间线" },
  { href: "/characters", label: "人物卷宗" },
  { href: "/submit", label: "补充线索" },
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="border-b border-[var(--line)] bg-[rgba(19,21,18,.84)] backdrop-blur-xl">
          <div className="mx-auto flex max-w-[1500px] items-center justify-between px-5 py-4 lg:px-10">
            <Link href="/" className="flex items-center gap-3">
              <span className="grid size-9 place-items-center border border-[var(--cinnabar-bright)] text-sm text-[var(--cinnabar-bright)]">
                燕
              </span>
              <span>
                <strong className="block tracking-[0.24em]">燕云卷宗</strong>
                <small className="text-[10px] tracking-[0.18em] text-[var(--fog)]">
                  非官方剧情关系图谱
                </small>
              </span>
            </Link>
            <nav aria-label="主导航" className="hidden gap-7 text-sm text-[var(--paper)] md:flex">
              {links.map((link) => (
                <Link key={link.href} href={link.href} className="transition hover:text-white">
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}

