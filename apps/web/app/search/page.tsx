import { DiscoveryWorkbench } from "@/components/discovery/DiscoveryWorkbench";

export default function SearchPage() {
  return (
    <main className="mx-auto max-w-6xl px-5 py-16">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">
        线索检索卷
      </p>
      <h1 className="mt-4 text-4xl">搜索与关系路径</h1>
      <p className="mt-6 max-w-2xl leading-8 text-[var(--fog)]">
        搜索、模糊匹配与路径计算共用同一剧情进度，未来实体不会进入响应。
      </p>
      <DiscoveryWorkbench />
    </main>
  );
}
