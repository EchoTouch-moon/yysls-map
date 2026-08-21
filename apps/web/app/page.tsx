import Link from "next/link";

import { ArchiveCardList } from "@/components/ui/ArchiveCard";
import { ProgressSelect } from "@/components/ui/ProgressSelect";
import { SectionHeading } from "@/components/ui/SectionHeading";

const entries = [
  { title: "关系图谱", description: "从人物之间的线索进入，观察合作、旧识、敌对与隐藏关联。", href: "/graph" },
  { title: "剧情时间线", description: "按章节重新排列事件，理解关系如何发生变化。", href: "/timeline" },
  { title: "人物卷宗", description: "聚焦一个角色，查看其所在势力与局部关系网。", href: "/characters" },
  { title: "搜索路径", description: "检索角色、势力与事件，寻找两名角色之间的最短可见关系链。", href: "/search" },
];

export default function Home() {
  return (
    <main className="archive-page">
      {/* Decorative background annotations/colophons */}
      <div className="absolute right-6 top-24 hidden lg:block" aria-hidden="true">
        <div className="marginalia-note h-48">
          <span>清河卷 · 人物牵系</span>
        </div>
      </div>

      {/* Hero */}
      <section className="mx-auto grid min-h-[76vh] max-w-[1500px] items-center gap-16 px-5 py-20 lg:grid-cols-[1.05fr_.95fr] lg:px-10">
        <div className="animate-text-fade-in">
          <SectionHeading
            eyebrow="江湖人物关系检索卷"
            level={1}
            description="选择自己已经完整通关的剧情节点，在不被剧透的前提下探索角色、势力、事件与隐藏关系。这里不是原文数据库，而是一份由玩家共同校订的江湖卷宗。"
            headingClassName="text-4xl sm:text-5xl md:text-6xl lg:text-5xl xl:text-7xl text-balance text-wrap"
          >
            <>
              <span className="block">
                <span className="inline-block">看不懂</span>
                <span className="inline-block">燕云剧情？</span>
              </span>
              <span className="mt-3 block text-[var(--paper)]">
                <span className="inline-block">沿着一条线，</span>
                <span className="inline-block">找到暗处的人。</span>
              </span>
            </>
          </SectionHeading>

          {/* CTA row */}
          <div className="mt-10 flex flex-wrap gap-5">
            <Link
              href="/graph"
              className="bg-[var(--cinnabar)] px-8 py-4 text-sm font-medium tracking-[0.2em] shadow-[0_10px_30px_rgba(143,47,37,.22)] transition-[background-color,transform,box-shadow] duration-300 hover:bg-[var(--cinnabar-bright)] hover:translate-y-[-1px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              展开关系图
            </Link>
            <Link
              href="/timeline"
              className="border border-[var(--line-strong)] px-8 py-4 text-sm font-medium tracking-[0.2em] transition-[border-color,background-color,transform] duration-300 hover:border-[var(--paper)] hover:bg-[rgba(217,201,164,.06)] hover:translate-y-[-1px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              查看时间线
            </Link>
          </div>

          {/* Progress selector — card variant for hero context */}
          <ProgressSelect variant="card" className="mt-14 max-w-sm" />
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
            <span>卷一 · 关系摘录</span>
            <span>防剧透：初入江湖</span>
          </div>

          <div className="relative mt-14 grid grid-cols-3 gap-6">
            {["旧识", "主角", "引路人", "疑点", "清河", "故人"].map((label, index) => (
              <div
                key={label}
                className={`character-slip grid min-h-24 place-items-center p-3 text-center text-sm transition-[transform,border-color,box-shadow] duration-300 hover:scale-105 hover:rotate-1 ${
                  index === 1
                    ? "character-slip-center character-slip-selected"
                    : ""
                }`}
              >
                {label}
              </div>
            ))}
          </div>

          <p className="absolute bottom-8 left-16 right-8 border-l-2 border-[var(--cinnabar)] pl-4 text-xs leading-6 text-[var(--fog)]">
            部分关系涉及后续章节，已按当前进度隐藏。
          </p>

          {/* Decorative stamp on dossier card */}
          <div className="absolute bottom-6 right-8 cinnabar-seal-large pointer-events-none z-10" aria-hidden="true">
            <span>燕云</span>
            <span>秘卷</span>
          </div>
        </div>
      </section>

      {/* Feature cards */}
      <div className="animate-card-slide-in">
        <ArchiveCardList entries={entries} />
      </div>

      {/* Disclaimer footer */}
      <footer className="mx-auto max-w-[1500px] px-5 py-12 text-xs leading-6 text-[var(--fog)] lg:px-10">
        本站为玩家自发整理的非官方剧情关系图谱项目，与游戏官方及相关权利方无隶属、授权或合作关系。
      </footer>
    </main>
  );
}
