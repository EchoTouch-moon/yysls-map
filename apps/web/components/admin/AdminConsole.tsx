"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
} from "react";

import { AIDraftWorkbench } from "@/components/admin/AIDraftWorkbench";
import { ContentManager } from "@/components/admin/ContentManager";
import { ApiError, apiFetch } from "@/lib/http";

type SessionData = {
  username: string;
  csrf_token: string;
  expires_in_minutes: number;
};

type Submission = {
  id: string;
  submission_type: string;
  payload: Record<string, unknown>;
  source_note: string;
  contact: string | null;
  status: "pending" | "approved" | "rejected";
  review_note: string | null;
  created_at: string;
};

const CSRF_KEY = "yysls-admin-csrf";
const CSRF_EVENT = "yysls-admin-session";

function getCsrfSnapshot() {
  return sessionStorage.getItem(CSRF_KEY);
}

function subscribeToCsrf(callback: () => void) {
  window.addEventListener(CSRF_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(CSRF_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

function updateCsrf(token: string | null) {
  if (token) {
    sessionStorage.setItem(CSRF_KEY, token);
  } else {
    sessionStorage.removeItem(CSRF_KEY);
  }
  window.dispatchEvent(new Event(CSRF_EVENT));
}

export function AdminConsole() {
  const storedCsrf = useSyncExternalStore(
    subscribeToCsrf,
    getCsrfSnapshot,
    () => null,
  );
  const [activeCsrf, setActiveCsrf] = useState<string | null>(null);
  const csrf = activeCsrf ?? storedCsrf;
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const endSession = useCallback(() => {
    updateCsrf(null);
    setActiveCsrf(null);
  }, []);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    try {
      const response = await apiFetch<SessionData>("/admin/session", {
        method: "POST",
        body: JSON.stringify({
          username: form.get("username"),
          password: form.get("password"),
        }),
      });
      const token = response.data?.csrf_token;
      if (!token) throw new Error("服务器未返回 CSRF Token。");
      updateCsrf(token);
      setActiveCsrf(token);
      setMessage("管理员会话已建立。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "登录失败。");
    } finally {
      setLoading(false);
    }
  }

  const inputClass =
    "w-full border border-[var(--line)] bg-[var(--ink)] px-4 py-3 outline-none focus:border-[var(--cinnabar-bright)]";

  if (!csrf) {
    return (
      <form
        onSubmit={login}
        className="mt-10 grid max-w-md gap-5 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-8"
      >
        <label className="text-sm">
          管理员账号
          <input name="username" required className={`mt-2 ${inputClass}`} />
        </label>
        <label className="text-sm">
          密码
          <input
            name="password"
            type="password"
            required
            className={`mt-2 ${inputClass}`}
          />
        </label>
        {message && <p role="alert" className="text-sm text-red-300">{message}</p>}
        <button
          disabled={loading}
          className="bg-[var(--cinnabar)] px-5 py-3 text-sm"
          type="submit"
        >
          {loading ? "校验中…" : "进入审核台"}
        </button>
      </form>
    );
  }

  return (
    <ReviewDashboard
      csrf={csrf}
      initialMessage={message}
      onSessionEnd={endSession}
    />
  );
}

function ReviewDashboard({
  csrf,
  initialMessage,
  onSessionEnd,
}: {
  csrf: string;
  initialMessage: string;
  onSessionEnd: () => void;
}) {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [message, setMessage] = useState(initialMessage);
  const [loading, setLoading] = useState(true);

  const loadSubmissions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch<Submission[]>(
        "/admin/submissions?status=pending",
      );
      setSubmissions(response.data ?? []);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "读取投稿失败。");
      if (error instanceof ApiError && error.status === 401) {
        onSessionEnd();
      }
    } finally {
      setLoading(false);
    }
  }, [onSessionEnd]);

  useEffect(() => {
    let active = true;
    apiFetch<Submission[]>("/admin/submissions?status=pending")
      .then((response) => {
        if (active) {
          setSubmissions(response.data ?? []);
          setMessage("");
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        setMessage(error instanceof Error ? error.message : "读取投稿失败。");
        if (error instanceof ApiError && error.status === 401) {
          onSessionEnd();
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [onSessionEnd]);

  async function review(
    submission: Submission,
    action: "approve" | "reject",
    reviewNote: string,
  ) {
    setLoading(true);
    try {
      await apiFetch(`/admin/submissions/${submission.id}`, {
        method: "PATCH",
        headers: { "X-CSRF-Token": csrf },
        body: JSON.stringify({ action, review_note: reviewNote }),
      });
      setSubmissions((items) => items.filter((item) => item.id !== submission.id));
      setMessage(action === "approve" ? "投稿已批准并写入正式内容。" : "投稿已拒绝。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "审核失败。");
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await apiFetch("/admin/session", {
      method: "DELETE",
      headers: { "X-CSRF-Token": csrf },
    });
    onSessionEnd();
  }

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-[var(--fog)]">
          {loading ? "正在读取待审线索…" : `待审核 ${submissions.length} 条`}
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => void loadSubmissions()}
            className="border border-[var(--line)] px-4 py-2 text-sm"
          >
            刷新
          </button>
          <button type="button" onClick={() => void logout()} className="px-4 py-2 text-sm">
            退出
          </button>
        </div>
      </div>
      {message && <p role="status" className="mt-4 text-sm text-[var(--fog)]">{message}</p>}
      <div className="mt-6 grid gap-5">
        {submissions.map((submission) => (
          <ReviewCard key={submission.id} submission={submission} onReview={review} />
        ))}
        {!loading && submissions.length === 0 && (
          <div className="border border-dashed border-[var(--line)] p-10 text-center text-[var(--fog)]">
            暂无待审核线索。
          </div>
        )}
      </div>
      <ContentManager csrf={csrf} />
      <AIDraftWorkbench csrf={csrf} />
    </section>
  );
}

function ReviewCard({
  submission,
  onReview,
}: {
  submission: Submission;
  onReview: (
    submission: Submission,
    action: "approve" | "reject",
    reviewNote: string,
  ) => Promise<void>;
}) {
  const [note, setNote] = useState("");
  return (
    <article className="border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-6">
      <div className="flex justify-between gap-4">
        <h2 className="text-xl">{String(submission.payload.title ?? "未命名线索")}</h2>
        <span className="text-xs text-[var(--cinnabar-bright)]">
          {submission.submission_type}
        </span>
      </div>
      <pre className="mt-5 overflow-x-auto whitespace-pre-wrap text-sm leading-7 text-[var(--fog)]">
        {JSON.stringify(submission.payload, null, 2)}
      </pre>
      <p className="mt-4 border-l border-[var(--line)] pl-4 text-sm leading-7">
        {submission.source_note}
      </p>
      <textarea
        value={note}
        onChange={(event) => setNote(event.target.value)}
        placeholder="填写审核说明（至少 2 个字）"
        className="mt-5 min-h-24 w-full border border-[var(--line)] bg-[var(--ink)] p-3 outline-none focus:border-[var(--cinnabar-bright)]"
      />
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          disabled={
            note.trim().length < 2 ||
            submission.submission_type === "correction"
          }
          onClick={() => void onReview(submission, "approve", note)}
          className="bg-emerald-800 px-5 py-2 text-sm disabled:opacity-40"
        >
          {submission.submission_type === "correction"
            ? "纠错需手工处理"
            : "批准并发布"}
        </button>
        <button
          type="button"
          disabled={note.trim().length < 2}
          onClick={() => void onReview(submission, "reject", note)}
          className="border border-[var(--cinnabar)] px-5 py-2 text-sm disabled:opacity-40"
        >
          拒绝
        </button>
      </div>
    </article>
  );
}
