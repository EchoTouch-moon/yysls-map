import type { ChangeEvent } from "react";

export type ResourceKey =
  | "chapters"
  | "factions"
  | "characters"
  | "events"
  | "relationships";

export type AdminItem = {
  id: string;
  status: "draft" | "published" | "archived";
  [key: string]: unknown;
};

export type AdminBootstrap = Record<ResourceKey, AdminItem[]>;
export type FormValue = string | boolean | string[];
export type FormState = Record<string, FormValue>;

type FieldKind =
  | "text"
  | "textarea"
  | "number"
  | "checkbox"
  | "select"
  | "reference"
  | "multi-reference"
  | "tags";

type FieldOption = { value: string; label: string };

export type FieldDefinition = {
  key: string;
  label: string;
  kind: FieldKind;
  required?: boolean;
  nullable?: boolean;
  reference?: ResourceKey;
  options?: FieldOption[];
  min?: number;
  max?: number;
  step?: number;
};

const STATUS_OPTIONS: FieldOption[] = [
  { value: "draft", label: "草稿" },
  { value: "published", label: "已发布" },
  { value: "archived", label: "已归档" },
];
const PROGRESS_OPTIONS: FieldOption[] = [
  { value: "start", label: "初入江湖" },
  { value: "qinghe", label: "清河" },
  { value: "kaifeng", label: "开封" },
  { value: "current", label: "当前进度" },
  { value: "unrestricted", label: "无限制" },
];
const RELATION_OPTIONS: FieldOption[] = [
  ["mentor", "师承"],
  ["family", "亲族"],
  ["enemy", "敌对"],
  ["ally", "同盟"],
  ["old_acquaintance", "故交"],
  ["exploitation", "利用"],
  ["hierarchy", "上下级"],
  ["same_sect", "同门"],
  ["interest", "利益"],
  ["hidden", "隐秘"],
].map(([value, label]) => ({ value, label }));
const STATUS_FIELD: FieldDefinition = {
  key: "status",
  label: "内容状态",
  kind: "select",
  options: STATUS_OPTIONS,
  required: true,
};
const SPOILER_FIELD: FieldDefinition = {
  key: "spoiler_level",
  label: "剧透等级",
  kind: "number",
  required: true,
  min: 0,
  max: 3,
};
const VISIBLE_FIELD: FieldDefinition = {
  key: "visible_after_chapter_id",
  label: "可见章节",
  kind: "reference",
  reference: "chapters",
  nullable: true,
};

export const RESOURCE_LABELS: Record<ResourceKey, string> = {
  chapters: "章节",
  factions: "势力",
  characters: "角色",
  events: "事件",
  relationships: "关系",
};

export const RESOURCE_FIELDS: Record<ResourceKey, FieldDefinition[]> = {
  chapters: [
    { key: "slug", label: "Slug", kind: "text", required: true },
    { key: "title", label: "章节标题", kind: "text", required: true },
    { key: "region", label: "区域", kind: "text", nullable: true },
    { key: "sort_order", label: "排序", kind: "number", required: true, min: 0 },
    {
      key: "progress_key",
      label: "进度档",
      kind: "select",
      options: PROGRESS_OPTIONS,
      required: true,
    },
    {
      key: "progress_rank",
      label: "进度值",
      kind: "number",
      required: true,
      min: 0,
      max: 100,
    },
    STATUS_FIELD,
  ],
  factions: [
    { key: "slug", label: "Slug", kind: "text", required: true },
    { key: "name", label: "势力名称", kind: "text", required: true },
    { key: "faction_type", label: "势力类型", kind: "text", required: true },
    { key: "summary", label: "摘要", kind: "textarea", required: true },
    SPOILER_FIELD,
    VISIBLE_FIELD,
    STATUS_FIELD,
  ],
  characters: [
    { key: "slug", label: "Slug", kind: "text", required: true },
    { key: "name", label: "角色名称", kind: "text", required: true },
    { key: "summary", label: "摘要", kind: "textarea", required: true },
    { key: "interpretation", label: "解读", kind: "textarea", nullable: true },
    { key: "identity_tags", label: "身份标签", kind: "tags" },
    {
      key: "faction_id",
      label: "所属势力",
      kind: "reference",
      reference: "factions",
      nullable: true,
    },
    {
      key: "importance",
      label: "重要度",
      kind: "number",
      required: true,
      min: 1,
      max: 5,
    },
    SPOILER_FIELD,
    {
      key: "first_appear_chapter_id",
      label: "首次登场章节",
      kind: "reference",
      reference: "chapters",
      nullable: true,
    },
    VISIBLE_FIELD,
    STATUS_FIELD,
  ],
  events: [
    { key: "slug", label: "Slug", kind: "text", required: true },
    { key: "title", label: "事件标题", kind: "text", required: true },
    { key: "summary", label: "摘要", kind: "textarea", required: true },
    { key: "impact", label: "影响", kind: "textarea", nullable: true },
    {
      key: "chapter_id",
      label: "所属章节",
      kind: "reference",
      reference: "chapters",
      required: true,
    },
    { key: "sort_order", label: "排序", kind: "number", required: true, min: 0 },
    SPOILER_FIELD,
    VISIBLE_FIELD,
    STATUS_FIELD,
    {
      key: "character_ids",
      label: "关联角色",
      kind: "multi-reference",
      reference: "characters",
    },
    {
      key: "faction_ids",
      label: "关联势力",
      kind: "multi-reference",
      reference: "factions",
    },
  ],
  relationships: [
    {
      key: "source_character_id",
      label: "起点角色",
      kind: "reference",
      reference: "characters",
      required: true,
    },
    {
      key: "target_character_id",
      label: "终点角色",
      kind: "reference",
      reference: "characters",
      required: true,
    },
    {
      key: "relation_type",
      label: "关系类型",
      kind: "select",
      options: RELATION_OPTIONS,
      required: true,
    },
    { key: "label", label: "关系名称", kind: "text", required: true },
    { key: "summary", label: "关系摘要", kind: "textarea", required: true },
    { key: "stage", label: "阶段", kind: "text", nullable: true },
    {
      key: "is_directional",
      label: "有方向",
      kind: "checkbox",
      required: true,
    },
    {
      key: "chapter_id",
      label: "所属章节",
      kind: "reference",
      reference: "chapters",
      nullable: true,
    },
    VISIBLE_FIELD,
    SPOILER_FIELD,
    {
      key: "confidence",
      label: "置信度",
      kind: "number",
      required: true,
      min: 0,
      max: 1,
      step: 0.01,
    },
    STATUS_FIELD,
    {
      key: "event_ids",
      label: "关联事件",
      kind: "multi-reference",
      reference: "events",
    },
  ],
};

const DEFAULTS: Record<ResourceKey, FormState> = {
  chapters: {
    slug: "",
    title: "",
    region: "",
    sort_order: "0",
    progress_key: "start",
    progress_rank: "0",
    status: "draft",
  },
  factions: {
    slug: "",
    name: "",
    faction_type: "",
    summary: "",
    spoiler_level: "0",
    visible_after_chapter_id: "",
    status: "draft",
  },
  characters: {
    slug: "",
    name: "",
    summary: "",
    interpretation: "",
    identity_tags: "",
    faction_id: "",
    importance: "1",
    spoiler_level: "0",
    first_appear_chapter_id: "",
    visible_after_chapter_id: "",
    status: "draft",
  },
  events: {
    slug: "",
    title: "",
    summary: "",
    impact: "",
    chapter_id: "",
    sort_order: "0",
    spoiler_level: "0",
    visible_after_chapter_id: "",
    status: "draft",
    character_ids: [],
    faction_ids: [],
  },
  relationships: {
    source_character_id: "",
    target_character_id: "",
    relation_type: "ally",
    label: "",
    summary: "",
    stage: "",
    is_directional: true,
    chapter_id: "",
    visible_after_chapter_id: "",
    spoiler_level: "0",
    confidence: "1",
    status: "draft",
    event_ids: [],
  },
};

export function emptyForm(resource: ResourceKey): FormState {
  return structuredClone(DEFAULTS[resource]);
}

export function itemToForm(
  resource: ResourceKey,
  item: AdminItem,
): FormState {
  const result = emptyForm(resource);
  for (const field of RESOURCE_FIELDS[resource]) {
    const value = item[field.key];
    if (Array.isArray(value)) {
      result[field.key] = value.filter(
        (entry): entry is string => typeof entry === "string",
      );
    } else if (typeof value === "boolean") {
      result[field.key] = value;
    } else {
      result[field.key] = value == null ? "" : String(value);
    }
  }
  return result;
}

export function formToPayload(
  resource: ResourceKey,
  form: FormState,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  for (const field of RESOURCE_FIELDS[resource]) {
    const value = form[field.key];
    if (field.kind === "number") {
      payload[field.key] = value === "" ? null : Number(value);
    } else if (field.kind === "checkbox") {
      payload[field.key] = Boolean(value);
    } else if (field.kind === "multi-reference") {
      payload[field.key] = Array.isArray(value) ? value : [];
    } else if (field.kind === "tags") {
      payload[field.key] =
        typeof value === "string"
          ? value
              .split(",")
              .map((tag) => tag.trim())
              .filter(Boolean)
          : [];
    } else {
      payload[field.key] =
        value === "" && field.nullable ? null : String(value ?? "");
    }
  }
  return payload;
}

function itemLabel(resource: ResourceKey, item: AdminItem): string {
  const key =
    resource === "chapters" || resource === "events"
      ? "title"
      : resource === "relationships"
        ? "label"
        : "name";
  return typeof item[key] === "string" ? item[key] : item.id;
}

function referenceOptions(
  field: FieldDefinition,
  data: AdminBootstrap,
): FieldOption[] {
  if (!field.reference) return [];
  return data[field.reference].map((item) => ({
    value: item.id,
    label: itemLabel(field.reference as ResourceKey, item),
  }));
}

export function ContentFormFields({
  fields,
  form,
  data,
  onChange,
}: {
  fields: FieldDefinition[];
  form: FormState;
  data: AdminBootstrap;
  onChange: (key: string, value: FormValue) => void;
}) {
  const inputClass =
    "mt-2 w-full border border-[var(--line)] bg-[var(--ink)] px-3 py-2 outline-none focus:border-[var(--cinnabar-bright)]";

  return fields.map((field) => {
    const value = form[field.key];
    const options =
      field.kind === "reference" || field.kind === "multi-reference"
        ? referenceOptions(field, data)
        : (field.options ?? []);

    if (field.kind === "checkbox") {
      return (
        <label key={field.key} className="flex items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => onChange(field.key, event.target.checked)}
          />
          {field.label}
        </label>
      );
    }
    if (field.kind === "textarea") {
      return (
        <label key={field.key} className="text-sm">
          {field.label}
          <textarea
            value={typeof value === "string" ? value : ""}
            required={field.required}
            onChange={(event) => onChange(field.key, event.target.value)}
            className={`${inputClass} min-h-24`}
          />
        </label>
      );
    }
    if (field.kind === "select" || field.kind === "reference") {
      return (
        <label key={field.key} className="text-sm">
          {field.label}
          <select
            value={typeof value === "string" ? value : ""}
            required={field.required}
            onChange={(event) => onChange(field.key, event.target.value)}
            className={inputClass}
          >
            {field.nullable && <option value="">无</option>}
            {field.required && field.kind === "reference" && (
              <option value="" disabled>
                请选择
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      );
    }
    if (field.kind === "multi-reference") {
      return (
        <label key={field.key} className="text-sm">
          {field.label}
          <select
            multiple
            value={Array.isArray(value) ? value : []}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              onChange(
                field.key,
                Array.from(event.target.selectedOptions, (option) => option.value),
              )
            }
            className={`${inputClass} min-h-28`}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      );
    }
    return (
      <label key={field.key} className="text-sm">
        {field.label}
        <input
          type={field.kind === "number" ? "number" : "text"}
          value={typeof value === "string" ? value : ""}
          required={field.required}
          min={field.min}
          max={field.max}
          step={field.step}
          onChange={(event) => onChange(field.key, event.target.value)}
          className={inputClass}
        />
      </label>
    );
  });
}
