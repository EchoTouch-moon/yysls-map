import Link from "next/link";

import { CharacterProfile } from "@/components/characters/CharacterProfile";

export default async function CharacterPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <main className="mx-auto max-w-5xl px-5 py-16">
      <Link href="/characters" className="text-xs text-[var(--fog)] hover:text-white">
        ← 返回人物卷宗
      </Link>
      <CharacterProfile slug={slug} />
    </main>
  );
}
