import { TimelineExplorer } from "@/components/timeline/TimelineExplorer";

export default function TimelinePage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-16 opacity-0 [animation:text-fade-in_0.5s_ease_0.1s_forwards]">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">故事次序卷</p>
      <h1 className="mt-4 text-4xl">剧情时间线</h1>
      <p className="mt-6 max-w-2xl leading-8 text-[var(--fog)]">
        先沿人工编排的故事线阅读主角的目标、阻力与转折；也可切换查看完整事件。切换顶部剧情进度后，后续内容会从响应中完全省略。
      </p>
      <TimelineExplorer />
    </main>
  );
}
