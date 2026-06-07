export type ApiEnvelope<T> = {
  data: T | null;
  error: {
    code: string;
    message: string;
    fields?: Record<string, string[]>;
  } | null;
  meta: {
    request_id?: string;
    next_cursor?: string;
  };
};

