"use client";

import { type FormEvent, useState } from "react";

import { apiFetch } from "@/lib/http";

type SubmissionType =
  | "relationship"
  | "event"
  | "interpretation"
  | "correction";

type Receipt = {
  id: string;
  status: "pending";
  message: string;
};

const TYPE_LABELS: Record<SubmissionType, string> = {
  relationship: "新增角色关系",
  event: "补充剧情事件",
  interpretation: "补充角色解读",
  correction: "纠错",
};

export function SubmissionForm() {
  const [type, setType] = useState<SubmissionType>("relationship");
  const [state, setState] = useState<
    | { kind: "idle" }
    | { kind: "submitting" }
    | { kind: "success"; message: string }
    | { kind: "error"; message: string }
  >({ kind: "idle" });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setState({ kind: "submitting" });
    try {
      const response = await apiFetch<Receipt>("/submissions", {
        method: "POST",
        body: JSON.stringify({
          submission_type: type,
          payload: {
            title: form.get("title"),
            summary: form.get("summary"),
            source_character_slug: form.get("source_character_slug") || null,
            target_character_slug: form.get("target_character_slug") || null,
            character_slug: form.get("character_slug") || null,
            chapter_slug: form.get("chapter_slug") || null,
            relation_type:
              type === "relationship" ? form.get("relation_type") : null,
            spoiler_level: Number(form.get("spoiler_level")),
          },
          source_note: form.get("source_note"),
          contact: form.get("contact") || null,
          website: form.get("website"),
        }),
      });
      formElement.reset();
      setState({
        kind: "success",
        message: response.data?.message ?? "投稿已进入审核。",
      });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "投稿失败。",
      });
    }
  }

  const fieldClass =
    "mt-2 w-full border border-[var(--line)] bg-[rgba(19,21,18,.72)] px-4 py-3 text-[var(--paper-light)] outline-none transition focus:border-[var(--cinnabar-bright)]";

  return (
    <form
      onSubmit={submit}
      className="mt-10 grid gap-6 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-6 md:p-10"
    >
      <label className="text-sm text-[var(--paper)]">
        投稿类型
        <select
          value={type}
          onChange={(event) => setType(event.target.value as SubmissionType)}
          className={fieldClass}
        >
          {Object.entries(TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>

      <div className="grid gap-5 md:grid-cols-2">
        <label className="text-sm text-[var(--paper)]">
          线索标题
          <input name="title" required maxLength={160} className={fieldClass} />
        </label>
        <label className="text-sm text-[var(--paper)]">
          涉及章节 slug
          <input name="chapter_slug" maxLength={80} className={fieldClass} />
        </label>
      </div>

      {type === "relationship" && (
        <div className="grid gap-5 md:grid-cols-3">
          <label className="text-sm text-[var(--paper)]">
            起点角色 slug
            <input
              name="source_character_slug"
              required
              maxLength={100}
              className={fieldClass}
            />
          </label>
          <label className="text-sm text-[var(--paper)]">
            终点角色 slug
            <input
              name="target_character_slug"
              required
              maxLength={100}
              className={fieldClass}
            />
          </label>
          <label className="text-sm text-[var(--paper)]">
            关系类型
            <select name="relation_type" className={fieldClass}>
              <option value="ally">合作</option>
              <option value="enemy">敌对</option>
              <option value="old_acquaintance">旧识</option>
              <option value="mentor">师徒</option>
              <option value="family">亲属</option>
              <option value="hidden">隐藏关系</option>
            </select>
          </label>
        </div>
      )}

      {(type === "interpretation" || type === "correction") && (
        <label className="text-sm text-[var(--paper)]">
          角色 slug
          <input name="character_slug" maxLength={100} className={fieldClass} />
        </label>
      )}

      <label className="text-sm text-[var(--paper)]">
        内容摘要
        <textarea
          name="summary"
          required
          minLength={10}
          maxLength={4000}
          rows={5}
          className={fieldClass}
        />
      </label>

      <label className="text-sm text-[var(--paper)]">
        来源与判断依据
        <textarea
          name="source_note"
          required
          minLength={10}
          maxLength={4000}
          rows={4}
          className={fieldClass}
        />
      </label>

      <div className="grid gap-5 md:grid-cols-2">
        <label className="text-sm text-[var(--paper)]">
          剧透等级
          <select name="spoiler_level" className={fieldClass}>
            <option value="0">0 · 无剧透</option>
            <option value="1">1 · 轻微</option>
            <option value="2">2 · 中度</option>
            <option value="3">3 · 重大</option>
          </select>
        </label>
        <label className="text-sm text-[var(--paper)]">
          联系方式（可选）
          <input name="contact" maxLength={200} className={fieldClass} />
        </label>
      </div>

      <label className="hidden" aria-hidden="true">
        Website
        <input name="website" tabIndex={-1} autoComplete="off" />
      </label>

      {state.kind === "success" && (
        <p role="status" className="border-l-2 border-emerald-600 pl-4 text-sm text-emerald-300">
          {state.message}
        </p>
      )}
      {state.kind === "error" && (
        <p role="alert" className="border-l-2 border-[var(--cinnabar)] pl-4 text-sm text-red-300">
          {state.message}
        </p>
      )}

      <button
        type="submit"
        disabled={state.kind === "submitting"}
        className="justify-self-start bg-[var(--cinnabar)] px-7 py-4 text-sm tracking-[0.16em] disabled:cursor-wait disabled:opacity-60"
      >
        {state.kind === "submitting" ? "正在封存线索…" : "提交人工审核"}
      </button>
    </form>
  );
}
