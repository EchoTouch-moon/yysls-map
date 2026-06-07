import { TimelineExplorer } from "@/components/timeline/TimelineExplorer";

export default function TimelinePage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-16">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">事件次序卷</p>
      <h1 className="mt-4 text-4xl">剧情时间线</h1>
      <p className="mt-6 max-w-2xl leading-8 text-[var(--fog)]">
        按章节梳理事件发生的先后与影响。切换顶部剧情进度后，后续事件会从响应中完全省略。
      </p>
      <TimelineExplorer />
    </main>
  );
}
