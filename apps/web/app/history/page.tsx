import { HistoryArchive } from "@/components/history/HistoryArchive";

export default function HistoryPage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-16 opacity-0 [animation:text-fade-in_0.5s_ease_0.1s_forwards]">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">史事考据卷</p>
      <h1 className="mt-4 text-4xl">历史背景</h1>
      <p className="mt-6 max-w-2xl leading-8 text-[var(--fog)]">
        故事发生在真实的历史土壤上。这里收录可核对的史实卡片：它们帮助理解剧情，
        也明确标注作品与史实之间的边界——史籍可证的，与作品虚构的，分开陈述。
      </p>
      <HistoryArchive />
    </main>
  );
}
