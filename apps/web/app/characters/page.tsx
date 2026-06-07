import { CharacterDirectory } from "@/components/characters/CharacterDirectory";

export default function CharactersPage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-16">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">人物索引卷</p>
      <h1 className="mt-4 text-4xl">人物卷宗</h1>
      <p className="mt-6 max-w-2xl leading-8 text-[var(--fog)]">
        浏览当前进度可见的角色，或在角色、势力与事件摘要中检索线索。
      </p>
      <CharacterDirectory />
    </main>
  );
}
