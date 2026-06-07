export default function GraphPage() {
  return (
    <main className="mx-auto max-w-[1500px] px-5 py-10 lg:px-10">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">核心卷宗</p>
      <h1 className="mt-4 text-4xl">角色关系图谱</h1>
      <div className="mt-8 grid min-h-[68vh] place-items-center border border-[var(--line)] bg-[rgba(32,35,31,.48)] text-[var(--fog)]">
        图谱数据层已建立，交互画布将在 T03 接入。
      </div>
    </main>
  );
}

