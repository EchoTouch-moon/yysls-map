import Link from "next/link";

import { FactionProfile } from "@/components/factions/FactionProfile";

export default async function FactionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <main className="mx-auto max-w-5xl px-5 py-16">
      <Link href="/search" className="text-xs text-[var(--fog)] hover:text-white">
        ← 返回搜索
      </Link>
      <FactionProfile slug={slug} />
    </main>
  );
}
