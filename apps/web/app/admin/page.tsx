import { AdminConsole } from "@/components/admin/AdminConsole";

export default function AdminPage() {
  return (
    <main className="mx-auto max-w-7xl px-5 py-16">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">
        内部校订
      </p>
      <h1 className="mt-4 text-4xl">投稿审核台</h1>
      <p className="mt-6 text-sm leading-7 text-[var(--fog)]">
        审核通过会在同一数据库事务中写入正式内容。纠错类投稿必须人工处理。
      </p>
      <AdminConsole />
    </main>
  );
}
