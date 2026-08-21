import { SubmissionForm } from "@/components/forms/SubmissionForm";

export default function SubmitPage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16 opacity-0 [animation:text-fade-in_0.5s_ease_0.1s_forwards]">
      <p className="text-xs tracking-[0.3em] text-[var(--cinnabar-bright)]">共校入口</p>
      <h1 className="mt-4 text-4xl">补充线索</h1>
      <p className="mt-6 leading-8 text-[var(--fog)]">
        投稿不会直接公开。请只提交自己的剧情摘要与关系分析，并写明判断依据。
      </p>
      <SubmissionForm />
    </main>
  );
}

