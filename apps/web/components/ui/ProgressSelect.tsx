"use client";

import { useId, useSyncExternalStore, type ChangeEvent } from "react";

/** Progress milestones exposed by the current public content release. */
export type ProgressKey = "start" | "qinghe" | "unrestricted";

interface ProgressOption {
  key: ProgressKey;
  label: string;
  description: string;
}

const PROGRESS_OPTIONS: readonly ProgressOption[] = [
  {
    key: "start",
    label: "清河篇未通关",
    description: "仅显示开篇即可获知的线索",
  },
  {
    key: "qinghe",
    label: "清河篇已通关",
    description: "包含清河主线结局与隐藏线索",
  },
  {
    key: "unrestricted",
    label: "不防剧透",
    description: "显示全部已录入内容，可能严重剧透",
  },
] as const;

const STORAGE_KEY = "yysls-progress";
const CHANGE_EVENT = "yysls-progress-change";
const DEFAULT_PROGRESS: ProgressKey = "start";

/**
 * Read the stored progress key from localStorage.
 * Returns `null` during SSR or when the key is absent / invalid.
 */
function readStoredProgress(): ProgressKey | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (
      typeof raw === "string" &&
      PROGRESS_OPTIONS.some((opt) => opt.key === raw)
    ) {
      return raw as ProgressKey;
    }
  } catch {
    // localStorage may be unavailable (private browsing, quota).
  }
  return null;
}

function writeStoredProgress(key: ProgressKey): void {
  try {
    localStorage.setItem(STORAGE_KEY, key);
    window.dispatchEvent(new Event(CHANGE_EVENT));
  } catch {
    // Silently ignore — the selection still works for the session.
  }
}

function subscribeProgress(callback: () => void): () => void {
  window.addEventListener("storage", callback);
  window.addEventListener(CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(CHANGE_EVENT, callback);
  };
}

function getProgressSnapshot(): ProgressKey {
  return readStoredProgress() ?? DEFAULT_PROGRESS;
}

export function useProgress(): ProgressKey {
  return useSyncExternalStore(
    subscribeProgress,
    getProgressSnapshot,
    () => DEFAULT_PROGRESS,
  );
}

interface ProgressSelectProps {
  /** Additional class names on the outer wrapper. */
  className?: string;
  /**
   * Visual variant.
   * - `"compact"` — single-line select suitable for the header bar.
   * - `"card"` — expanded card with descriptions, suitable for the hero.
   */
  variant?: "compact" | "card";
}

/**
 * Progress milestone selector.
 *
 * Reads the stored value from localStorage **after hydration** to avoid
 * server/client mismatch. Until hydrated the component renders with the
 * default (`"start"`), then syncs to the stored value on mount.
 *
 * Selection is persisted to localStorage on every change.
 */
export function ProgressSelect({
  className = "",
  variant = "compact",
}: ProgressSelectProps) {
  const selectId = useId();
  const progress = useProgress();

  const handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const next = e.target.value as ProgressKey;
    writeStoredProgress(next);
  };

  if (variant === "card") {
    return (
      <div className={className}>
        <p
          id={`${selectId}-label`}
          className="mb-3 block text-xs tracking-[0.2em] text-[var(--fog)]"
        >
          已完成的剧情进度
        </p>
        <p className="mb-4 text-xs leading-5 text-[var(--fog)]">
          进行中的章节请选择上一档，避免提前看到本章结局。
        </p>
        <div
          role="group"
          aria-labelledby={`${selectId}-label`}
          className="grid gap-2"
        >
          {PROGRESS_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => writeStoredProgress(opt.key)}
              className={`flex items-center justify-between border px-4 py-3 text-left text-sm transition ${
                progress === opt.key
                  ? "border-[var(--cinnabar)] bg-[rgba(157,46,37,.12)] text-[var(--paper-light)]"
                  : "border-[var(--line)] text-[var(--fog)] hover:border-[var(--paper)] hover:text-[var(--paper)]"
              }`}
              aria-pressed={progress === opt.key}
            >
              <span>
                <span className="block tracking-wide">{opt.label}</span>
                <span className="mt-0.5 block text-xs opacity-70">{opt.description}</span>
              </span>
              {progress === opt.key && (
                <span className="text-[var(--cinnabar-bright)]" aria-hidden="true">
                  ●
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Compact variant — single <select> for header / narrow layouts.
  return (
    <div className={className}>
      <label htmlFor={selectId} className="sr-only">
        已完成的剧情进度
      </label>
      <select
        id={selectId}
        value={progress}
        onChange={handleChange}
        className="cursor-pointer border border-[var(--line)] bg-[var(--ink)] px-3 py-1.5 text-xs tracking-wide text-[var(--paper)] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[var(--cinnabar-bright)]"
      >
        {PROGRESS_OPTIONS.map((opt) => (
          <option key={opt.key} value={opt.key}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
