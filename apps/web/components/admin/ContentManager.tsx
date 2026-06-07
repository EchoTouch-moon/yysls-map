"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  type AdminBootstrap,
  type AdminItem,
  ContentFormFields,
  type FormState,
  type FormValue,
  RESOURCE_FIELDS,
  RESOURCE_LABELS,
  type ResourceKey,
  emptyForm,
  formToPayload,
  itemToForm,
} from "@/components/admin/content-manager-fields";
import { apiFetch } from "@/lib/http";

const TABS = Object.entries(RESOURCE_LABELS) as [ResourceKey, string][];
const EMPTY_DATA: AdminBootstrap = {
  chapters: [],
  factions: [],
  characters: [],
  events: [],
  relationships: [],
};

function textValue(item: AdminItem, key: string): string | null {
  return typeof item[key] === "string" ? item[key] : null;
}

function findName(
  data: AdminBootstrap,
  resource: "characters" | "factions" | "chapters",
  id: unknown,
): string {
  if (typeof id !== "string") return "未指定";
  const item = data[resource].find((candidate) => candidate.id === id);
  if (!item) return id;
  return textValue(item, resource === "chapters" ? "title" : "name") ?? id;
}

function itemPresentation(
  resource: ResourceKey,
  item: AdminItem,
  data: AdminBootstrap,
): { title: string; detail: string } {
  if (resource === "relationships") {
    return {
      title: textValue(item, "label") ?? item.id,
      detail: `${findName(data, "characters", item.source_character_id)} → ${findName(
        data,
        "characters",
        item.target_character_id,
      )}`,
    };
  }
  const titleKey =
    resource === "chapters" || resource === "events" ? "title" : "name";
  const slug = textValue(item, "slug");
  return {
    title: textValue(item, titleKey) ?? item.id,
    detail: slug ? `${slug} · ${item.status}` : item.status,
  };
}

export function ContentManager({ csrf }: { csrf: string }) {
  const [resource, setResource] = useState<ResourceKey>("chapters");
  const [data, setData] = useState<AdminBootstrap>(EMPTY_DATA);
  const [form, setForm] = useState<FormState>(() => emptyForm("chapters"));
  const [editingId, setEditingId] = useState<string | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<AdminItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch<AdminBootstrap>(
        "/admin/content/bootstrap",
      );
      setData(response.data ?? EMPTY_DATA);
      setError("");
    } catch (loadError) {
      setError(
        loadError instanceof Error ? loadError.message : "内容读取失败。",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    apiFetch<AdminBootstrap>("/admin/content/bootstrap")
      .then((response) => {
        if (active) {
          setData(response.data ?? EMPTY_DATA);
          setError("");
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(
            loadError instanceof Error ? loadError.message : "内容读取失败。",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const items = useMemo(() => data[resource], [data, resource]);

  function switchResource(nextResource: ResourceKey) {
    setResource(nextResource);
    setEditingId(null);
    setForm(emptyForm(nextResource));
    setMessage("");
    setError("");
  }

  function edit(item: AdminItem) {
    setEditingId(item.id);
    setForm(itemToForm(resource, item));
    setMessage("");
    setError("");
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm(resource));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const path = editingId
        ? `/admin/content/${resource}/${editingId}`
        : `/admin/content/${resource}`;
      await apiFetch(path, {
        method: editingId ? "PATCH" : "POST",
        headers: { "X-CSRF-Token": csrf },
        body: JSON.stringify(formToPayload(resource, form)),
      });
      setMessage(
        `${RESOURCE_LABELS[resource]}${editingId ? "已更新" : "已创建"}。`,
      );
      resetForm();
      await load();
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "内容保存失败。",
      );
    } finally {
      setSaving(false);
    }
  }

  async function archive() {
    if (!archiveTarget) return;
    setSaving(true);
    setError("");
    try {
      await apiFetch(`/admin/content/${resource}/${archiveTarget.id}`, {
        method: "DELETE",
        headers: { "X-CSRF-Token": csrf },
      });
      setMessage(`${RESOURCE_LABELS[resource]}已归档。`);
      setArchiveTarget(null);
      await load();
    } catch (archiveError) {
      setError(
        archiveError instanceof Error ? archiveError.message : "归档失败。",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="mt-12 border-t border-[var(--line)] pt-10">
      <p className="text-xs tracking-[0.24em] text-[var(--cinnabar-bright)]">
        正式内容
      </p>
      <h2 className="mt-3 text-2xl">内容管理</h2>
      <p className="mt-3 text-sm leading-7 text-[var(--fog)]">
        新内容默认保存为草稿；归档只停止公开展示，不会物理删除历史关联。
      </p>

      <div
        role="tablist"
        aria-label="内容类型"
        className="mt-6 flex flex-wrap gap-2"
      >
        {TABS.map(([key, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={resource === key}
            onClick={() => switchResource(key)}
            className={`border px-4 py-2 text-sm ${
              resource === key
                ? "border-[var(--cinnabar-bright)] bg-[var(--cinnabar)] text-white"
                : "border-[var(--line)] text-[var(--fog)]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-5 text-sm text-red-300">
          {error}
        </p>
      )}
      {message && (
        <p role="status" className="mt-5 text-sm text-emerald-300">
          {message}
        </p>
      )}

      <div className="mt-6 grid gap-8 xl:grid-cols-[minmax(0,1fr)_minmax(22rem,.8fr)]">
        <div role="tabpanel" aria-label={`${RESOURCE_LABELS[resource]}列表`}>
          {loading ? (
            <p className="text-sm text-[var(--fog)]">正在读取内容…</p>
          ) : (
            <ul className="grid gap-3">
              {items.map((item) => {
                const presentation = itemPresentation(resource, item, data);
                return (
                  <li
                    key={item.id}
                    className="flex flex-wrap items-center justify-between gap-4 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-4"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">
                        {presentation.title}
                      </p>
                      <p className="mt-1 truncate text-xs text-[var(--fog)]">
                        {presentation.detail}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => edit(item)}
                        className="border border-[var(--line)] px-3 py-1 text-xs"
                      >
                        编辑
                      </button>
                      {item.status !== "archived" && (
                        <button
                          type="button"
                          onClick={() => setArchiveTarget(item)}
                          className="border border-[var(--cinnabar)] px-3 py-1 text-xs text-[var(--cinnabar-bright)]"
                        >
                          归档
                        </button>
                      )}
                    </div>
                  </li>
                );
              })}
              {items.length === 0 && (
                <li className="border border-dashed border-[var(--line)] p-8 text-center text-sm text-[var(--fog)]">
                  暂无{RESOURCE_LABELS[resource]}。
                </li>
              )}
            </ul>
          )}
        </div>

        <form
          aria-label={`${editingId ? "编辑" : "新建"}${RESOURCE_LABELS[resource]}`}
          onSubmit={(event) => void submit(event)}
          className="grid content-start gap-4 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-5"
        >
          <h3 className="text-lg">
            {editingId ? "编辑" : "新建"}
            {RESOURCE_LABELS[resource]}
          </h3>
          <ContentFormFields
            fields={RESOURCE_FIELDS[resource]}
            form={form}
            data={data}
            onChange={(key: string, value: FormValue) =>
              setForm((current) => ({ ...current, [key]: value }))
            }
          />
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-[var(--cinnabar)] px-5 py-2 text-sm disabled:opacity-50"
            >
              {saving ? "保存中…" : editingId ? "更新" : "创建"}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="border border-[var(--line)] px-5 py-2 text-sm"
              >
                取消
              </button>
            )}
          </div>
        </form>
      </div>

      {archiveTarget && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="确认归档"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-5"
        >
          <div className="w-full max-w-sm border border-[var(--line)] bg-[var(--ink)] p-6">
            <p className="text-sm leading-7">
              确认归档
              {itemPresentation(resource, archiveTarget, data).title}？
            </p>
            <div className="mt-5 flex gap-3">
              <button
                type="button"
                disabled={saving}
                onClick={() => void archive()}
                className="bg-[var(--cinnabar)] px-4 py-2 text-sm"
              >
                确认归档
              </button>
              <button
                type="button"
                onClick={() => setArchiveTarget(null)}
                className="border border-[var(--line)] px-4 py-2 text-sm"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
