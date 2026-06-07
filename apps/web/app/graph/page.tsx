import { StoryGraph } from "@/components/graph/StoryGraph";

export default async function GraphPage({
  searchParams,
}: {
  searchParams: Promise<{ focus?: string }>;
}) {
  const { focus } = await searchParams;
  return (
    <main className="mx-auto max-w-[1500px] px-5 py-10 lg:px-10">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">核心卷宗</p>
      <h1 className="mt-4 text-4xl">角色关系图谱</h1>
      <p className="mt-5 max-w-2xl text-sm leading-7 text-[var(--fog)]">
        画布只接收当前剧情进度允许公开的角色与关系；切换进度会立即销毁旧数据视图。
      </p>
      <div className="relative mt-8 overflow-hidden border border-[var(--line)] bg-[rgba(32,35,31,.48)]">
        <StoryGraph focus={focus} />
      </div>
    </main>
  );
}
