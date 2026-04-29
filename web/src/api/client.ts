import { ApiError } from "@/api/errors";

const defaultHeaders = {
  Accept: "application/json",
};

export async function fetchJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const hasBody = init?.body !== undefined && init?.body !== null;
  const headers = new Headers(init?.headers ?? defaultHeaders);
  if (hasBody && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const response = await fetch(input, { ...init, headers });
    if (!response.ok) {
      const message = (await response.text()).trim() || response.statusText || `HTTP ${response.status}`;
      throw new ApiError(response.status, message, response.status >= 500);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, error instanceof Error ? error.message : "Network error", true, error);
  }
}

export async function postJson<T>(input: RequestInfo | URL, body?: unknown, init?: RequestInit): Promise<T> {
  return fetchJson<T>(input, {
    ...init,
    method: init?.method ?? "POST",
    body: body === undefined ? init?.body : JSON.stringify(body),
  });
}
