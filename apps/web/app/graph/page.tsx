import { StoryGraph } from "@/components/graph/StoryGraph";

export default async function GraphPage({
  searchParams,
}: {
  searchParams: Promise<{ focus?: string }>;
}) {
  const { focus } = await searchParams;
  return (
    <main className="archive-page mx-auto max-w-[1600px] px-5 py-10 lg:px-10">
      <p className="archive-kicker">核心卷宗 · 人物牵系</p>
      <h1 className="mt-4 text-4xl tracking-[0.12em]">角色关系图谱</h1>
      <p className="mt-5 max-w-2xl text-sm leading-7 text-[var(--fog)]">
        以一人为卷心，沿关系线索翻阅其身边之人。点击人物牌即可翻页换卷；画布始终只呈现当前剧情进度允许公开的内容。
      </p>
      <div className="archive-frame relative mt-8 overflow-hidden">
        <StoryGraph focus={focus ?? "protagonist"} />
      </div>
    </main>
  );
}
