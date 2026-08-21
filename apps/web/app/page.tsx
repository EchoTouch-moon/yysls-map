import Link from "next/link";

import { ArchiveCardList } from "@/components/ui/ArchiveCard";
import { ProgressSelect } from "@/components/ui/ProgressSelect";
import { SectionHeading } from "@/components/ui/SectionHeading";

const entries = [
  {
    title: "故事导读",
    description: "十二分钟沿主线读完清河：目标、阻力、转折与因果，一幕一幕讲清楚。",
    href: "/timeline",
  },
  {
    title: "人物卷宗",
    description: "从初识到完整解析，逐层理解一个人物的足迹、关系与身份。",
    href: "/characters",
  },
  {
    title: "历史背景",
    description: "中渡桥、五代十国与契丹——可核对的史实卡片及其与作品的边界。",
    href: "/history",
  },
  {
    title: "关系图谱",
    description: "以任意人物为中心展开局部关系网，观察合作、旧识、敌对与隐藏关联。",
    href: "/graph",
  },
];

export default function Home() {
  return (
    <main className="archive-page">
      {/* Decorative background annotations/colophons */}
      <div className="absolute right-6 top-24 hidden lg:block" aria-hidden="true">
        <div className="marginalia-note h-48">
          <span>清河卷 · 剧情解读</span>
        </div>
      </div>

      {/* Hero */}
      <section className="mx-auto grid min-h-[76vh] max-w-[1500px] items-center gap-16 px-5 py-20 lg:grid-cols-[1.05fr_.95fr] lg:px-10">
        <div className="animate-text-fade-in">
          <SectionHeading
            eyebrow="剧情理解 · 分层阅读"
            level={1}
            description="不是原文数据库，而是一份逐层展开的剧情解析：先读懂发生了什么，再深入为什么，直到看清每条伏笔与它背后的真实历史。"
            headingClassName="text-4xl sm:text-5xl md:text-6xl lg:text-5xl xl:text-7xl text-balance text-wrap"
          >
            <>
              <span className="block">
                <span className="inline-block">把清河的故事</span>
              </span>
              <span className="mt-3 block text-[var(--paper)]">
                <span className="inline-block">真正看懂一遍。</span>
              </span>
            </>
          </SectionHeading>

          {/* CTA — story first (G1) */}
          <div className="mt-10 flex flex-wrap items-center gap-5">
            <Link
              href="/timeline"
              className="bg-[var(--cinnabar)] px-8 py-4 text-sm font-medium tracking-[0.2em] shadow-[0_10px_30px_rgba(143,47,37,.22)] transition-[background-color,transform,box-shadow] duration-300 hover:bg-[var(--cinnabar-bright)] hover:translate-y-[-1px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              看懂清河故事 · 12 分钟
            </Link>
            <Link
              href="/characters"
              className="border border-[var(--line-strong)] px-8 py-4 text-sm font-medium tracking-[0.2em] transition-[border-color,background-color,transform] duration-300 hover:border-[var(--paper)] hover:bg-[rgba(217,201,164,.06)] hover:translate-y-[-1px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              了解一个人物
            </Link>
          </div>

          {/* Secondary entries + demoted spoiler protection */}
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 text-xs tracking-[0.14em] text-[var(--fog)]">
            <Link href="/history" className="hover:text-[var(--paper)]">历史背景</Link>
            <span aria-hidden="true">·</span>
            <Link href="/timeline" className="hover:text-[var(--paper)]">完整事件时间线</Link>
            <span aria-hidden="true">·</span>
            <Link href="/graph" className="hover:text-[var(--paper)]">关系图谱</Link>
          </div>

          {/* Spoiler protection demoted to an optional secondary control (G1) */}
          <details className="group mt-8 max-w-xl border border-[var(--line)] px-4 py-3">
            <summary className="cursor-pointer list-none text-xs leading-5 text-[var(--fog)] transition hover:text-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]">
              🛡 我还在第一次游玩，避免看到重大揭示
              <span className="ml-2 inline-block text-[var(--cinnabar-bright)] transition group-open:rotate-45" aria-hidden="true">
                ＋
              </span>
            </summary>
            <p className="mt-3 text-xs leading-5 text-[var(--fog)]">
              选择已完成章节后，涉及后续揭示的内容会整体隐藏；各页面的「显示完整解析」仍可手动展开。
            </p>
            <ProgressSelect variant="compact" className="mt-3" />
          </details>
        </div>

        {/* Decorative dossier card with traditional binding threads and stamps */}
        <div className="archive-frame relative min-h-[500px] overflow-hidden p-8 pl-16 animate-dossier-unfold shadow-[0_30px_60px_rgba(0,0,0,0.45)]">
          {/* Traditional Book Spine/Binding thread decoration */}
          <div className="archive-frame-binding" />
          <div className="archive-frame-thread top-[12%]" />
          <div className="archive-frame-thread top-[38%]" />
          <div className="archive-frame-thread top-[62%]" />
          <div className="archive-frame-thread bottom-[12%]" />

          <div className="absolute inset-0 opacity-[0.18] [background-image:repeating-linear-gradient(3deg,rgba(217,201,164,.14)_0_1px,transparent_1px_8px)] pointer-events-none" />

          {/* Subtle ink halo bleed effect in the background */}
          <div className="absolute left-[25%] top-[35%] -z-10 size-48 rounded-full bg-[var(--cinnabar)] opacity-[0.035] blur-[80px] pointer-events-none" />

          <div className="relative flex items-center justify-between border-b border-[var(--line)] pb-4 text-xs tracking-[0.2em] text-[var(--fog)]">
            <span>清河篇 · 理解路径</span>
            <span>初识 → 足迹 → 解析</span>
          </div>

          <ol className="relative mt-12 grid gap-5 pl-6">
            {[
              { title: "初识一个人物", note: "他是谁、从哪来、站在哪一边" },
              { title: "跟随剧情足迹", note: "他在主线的哪些转折点出现" },
              { title: "看清关系网络", note: "谁与他同行、谁与他为敌" },
              { title: "主动揭开解析", note: "准备好之后，再看完整的答案" },
            ].map((step, index) => (
              <li key={step.title} className="relative">
                <span className="absolute -left-6 top-1 size-2.5 border border-[var(--cinnabar-bright)] bg-[var(--ink)]" aria-hidden="true" />
                <p className="text-sm text-[var(--paper-light)]">
                  <span className="mr-3 text-xs tabular-nums text-[var(--cinnabar-bright)]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {step.title}
                </p>
                <p className="mt-1 pl-8 text-xs leading-5 text-[var(--fog)]">{step.note}</p>
              </li>
            ))}
          </ol>

          <p className="absolute bottom-8 left-16 right-8 border-l-2 border-[var(--cinnabar)] pl-4 text-xs leading-6 text-[var(--fog)]">
            深层解析默认折叠，由你决定何时翻开。
          </p>

          {/* Decorative stamp on dossier card */}
          <div className="absolute bottom-6 right-8 cinnabar-seal-large pointer-events-none z-10" aria-hidden="true">
            <span>燕云</span>
            <span>解卷</span>
          </div>
        </div>
      </section>

      {/* Feature cards */}
      <div className="animate-card-slide-in">
        <ArchiveCardList entries={entries} />
      </div>

      {/* Disclaimer footer */}
      <footer className="mx-auto max-w-[1500px] px-5 py-12 text-xs leading-6 text-[var(--fog)] lg:px-10">
        本站为玩家自发整理的非官方剧情解析项目，与游戏官方及相关权利方无隶属、授权或合作关系。
      </footer>
    </main>
  );
}
