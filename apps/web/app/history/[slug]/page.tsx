import Link from "next/link";

import { HistoryDetailCard } from "@/components/history/HistoryDetailCard";

export default async function HistoryDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <main className="mx-auto max-w-5xl px-5 py-16">
      <Link href="/history" className="text-xs text-[var(--fog)] hover:text-white">
        ← 返回历史背景
      </Link>
      <HistoryDetailCard slug={slug} />
    </main>
  );
}
