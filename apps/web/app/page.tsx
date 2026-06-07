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
    <main>
      {/* Hero */}
      <section className="mx-auto grid min-h-[72vh] max-w-[1500px] items-center gap-16 px-5 py-20 lg:grid-cols-[1.05fr_.95fr] lg:px-10">
        <div>
          <SectionHeading
            eyebrow="江湖人物关系检索卷"
            level={1}
            description="选择自己的剧情进度，在不被剧透的前提下探索角色、势力、事件与隐藏关系。这里不是原文数据库，而是一份由玩家共同校订的江湖卷宗。"
          >
            <>
              看不懂燕云剧情？
              <span className="mt-3 block text-[var(--paper)]">沿着一条线，找到暗处的人。</span>
            </>
          </SectionHeading>

          {/* CTA row */}
          <div className="mt-10 flex flex-wrap gap-4">
            <Link
              href="/graph"
              className="bg-[var(--cinnabar)] px-7 py-4 text-sm tracking-[0.16em] transition hover:bg-[var(--cinnabar-bright)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              展开关系图
            </Link>
            <Link
              href="/timeline"
              className="border border-[var(--line)] px-7 py-4 text-sm tracking-[0.16em] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              查看时间线
            </Link>
          </div>

          {/* Progress selector — card variant for hero context */}
          <ProgressSelect variant="card" className="mt-12 max-w-sm" />
        </div>

        {/* Decorative dossier card */}
        <div className="relative min-h-[480px] overflow-hidden border border-[var(--line)] bg-[rgba(32,35,31,.58)] p-6 shadow-2xl shadow-black/30">
          <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(circle,var(--paper)_1px,transparent_1px)] [background-size:26px_26px]" />
          <div className="relative flex items-center justify-between border-b border-[var(--line)] pb-4 text-xs tracking-[0.2em] text-[var(--fog)]">
            <span>卷一 · 关系摘录</span>
            <span>防剧透：初入江湖</span>
          </div>
          <div className="relative mt-14 grid grid-cols-3 gap-8">
            {["旧识", "主角", "引路人", "疑点", "清河", "故人"].map((label, index) => (
              <div
                key={label}
                className={`grid min-h-24 place-items-center border bg-[var(--paper)] p-3 text-center text-sm text-[var(--ink)] shadow-xl ${
                  index === 1
                    ? "border-[var(--cinnabar)] outline outline-4 outline-[rgba(157,46,37,.18)]"
                    : "border-black/20"
                }`}
              >
                {label}
              </div>
            ))}
          </div>
          <p className="absolute bottom-6 left-6 right-6 border-l-2 border-[var(--cinnabar)] pl-4 text-xs leading-6 text-[var(--fog)]">
            部分关系涉及后续章节，已按当前进度隐藏。
          </p>
        </div>
      </section>

      {/* Feature cards */}
      <ArchiveCardList entries={entries} />

      {/* Disclaimer footer */}
      <footer className="mx-auto max-w-[1500px] px-5 py-12 text-xs leading-6 text-[var(--fog)] lg:px-10">
        本站为玩家自发整理的非官方剧情关系图谱项目，与游戏官方及相关权利方无隶属、授权或合作关系。
      </footer>
    </main>
  );
}
