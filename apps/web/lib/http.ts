export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

export type ApiEnvelope<T> = {
  data: T | null;
  error: { code: string; message: string } | null;
  meta: { request_id?: string; next_cursor?: string };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  const body = (await response.json()) as
    | ApiEnvelope<T>
    | { detail?: string | { msg?: string }[] };
  if (!response.ok) {
    const detail = "detail" in body ? body.detail : undefined;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg ?? "输入无效").join("；")
          : "请求失败，请稍后再试。";
    throw new ApiError(message, response.status);
  }
  const envelope = body as ApiEnvelope<T>;
  if (envelope.error) {
    throw new ApiError(envelope.error.message, response.status);
  }
  return envelope;
}
