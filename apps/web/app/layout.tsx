import type { Metadata } from "next";

import { SiteHeader } from "@/components/layout/SiteHeader";

import "./globals.css";

export const metadata: Metadata = {
  title: "燕云卷宗 · 剧情关系图谱",
  description: "用关系图与时间线读懂燕云十六声的角色、势力和暗线。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
