/**
 * Centralized HTTP client with interceptors.
 *
 * - Singleton — use the default `httpClient` export everywhere.
 * - Request interceptors automatically attach auth headers
 *   (X-Ms-Client-Principal-Id) so callers never need to remember.
 * - Response interceptors provide uniform error handling.
 * - Built-in query-param serialization, configurable timeout, and base URL.
 */

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

/** Options accepted by every request method. */
export interface RequestOptions extends Omit<RequestInit, 'method' | 'body'> {
  /** Query parameters – appended to the URL automatically. */
  params?: Record<string, string | number | boolean | undefined>;
  /** Per-request timeout in ms (default: client-level `timeout`). */
  timeout?: number;
}

type RequestInterceptor = (url: string, init: RequestInit) => RequestInit | Promise<RequestInit>;
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;

/* ------------------------------------------------------------------ */
/*  HttpClient                                                        */
/* ------------------------------------------------------------------ */

export class HttpClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  constructor(baseUrl = '', timeout = 60_000) {
    this.baseUrl = baseUrl;
    this.defaultTimeout = timeout;
  }

  /* ---------- interceptor registration ---------- */

  onRequest(fn: RequestInterceptor): void {
    this.requestInterceptors.push(fn);
  }

  onResponse(fn: ResponseInterceptor): void {
    this.responseInterceptors.push(fn);
  }

  /* ---------- public request helpers ---------- */

  async get<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
    const res = await this.request(path, { ...opts, method: 'GET' });
    return res.json() as Promise<T>;
  }

  async post<T = unknown>(path: string, body?: unknown, opts: RequestOptions = {}): Promise<T> {
    const res = await this.request(path, {
      ...opts,
      method: 'POST',
      body: body != null ? JSON.stringify(body) : undefined,
      headers: {
        ...(body != null ? { 'Content-Type': 'application/json' } : {}),
        ...opts.headers,
      },
    });
    return res.json() as Promise<T>;
  }

  async put<T = unknown>(path: string, body?: unknown, opts: RequestOptions = {}): Promise<T> {
    const res = await this.request(path, {
      ...opts,
      method: 'PUT',
      body: body != null ? JSON.stringify(body) : undefined,
      headers: {
        ...(body != null ? { 'Content-Type': 'application/json' } : {}),
        ...opts.headers,
      },
    });
    return res.json() as Promise<T>;
  }

  async delete<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
    const res = await this.request(path, { ...opts, method: 'DELETE' });
    return res.json() as Promise<T>;
  }

  /**
   * Low-level request that returns the raw `Response`.
   * Useful for streaming (SSE) endpoints where the caller needs `response.body`.
   */
  async raw(path: string, opts: RequestOptions & { method?: string; body?: BodyInit | null } = {}): Promise<Response> {
    return this.request(path, opts);
  }

  /* ---------- internal plumbing ---------- */

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = `${this.baseUrl}${path}`;
    if (!params) return url;

    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        qs.set(key, String(value));
      }
    }
    const queryString = qs.toString();
    return queryString ? `${url}?${queryString}` : url;
  }

  private async request(path: string, opts: RequestOptions & { method?: string; body?: BodyInit | null } = {}): Promise<Response> {
    const { params, timeout, ...fetchOpts } = opts;
    const url = this.buildUrl(path, params);
    const effectiveTimeout = timeout ?? this.defaultTimeout;

    // Build the init object
    let init: RequestInit = { ...fetchOpts };

    // Run request interceptors
    for (const interceptor of this.requestInterceptors) {
      init = await interceptor(url, init);
    }

    // Timeout via AbortController (merged with caller-supplied signal)
    const timeoutCtrl = new AbortController();
    const callerSignal = init.signal;

    // If caller already passed a signal, listen for its abort
    if (callerSignal) {
      if (callerSignal.aborted) {
        timeoutCtrl.abort(callerSignal.reason);
      } else {
        callerSignal.addEventListener('abort', () => timeoutCtrl.abort(callerSignal.reason), { once: true });
      }
    }

    const timer = effectiveTimeout > 0
      ? setTimeout(() => timeoutCtrl.abort(new DOMException('Request timed out', 'TimeoutError')), effectiveTimeout)
      : undefined;

    init.signal = timeoutCtrl.signal;

    try {
      let response = await fetch(url, init);

      // Run response interceptors
      for (const interceptor of this.responseInterceptors) {
        response = await interceptor(response);
      }

      return response;
    } finally {
      if (timer !== undefined) clearTimeout(timer);
    }
  }
}

/* ------------------------------------------------------------------ */
/*  Singleton instance with default interceptors                      */
/* ------------------------------------------------------------------ */

const httpClient = new HttpClient('/api');

/**
 * Client for Azure platform endpoints (/.auth/me, etc.) — no base URL prefix.
 * Shares the same interceptor pattern but targets the host root.
 */
export const platformClient = new HttpClient('', 10_000);

// ---- request interceptor: auth headers ----
httpClient.onRequest(async (_url, init) => {
  const headers = new Headers(init.headers);

  // Attach userId from Redux store (lazy import to avoid circular deps).
  // Falls back to 'anonymous' if store isn't ready yet.
  try {
    const { store } = await import('../store/store');
    const state = store?.getState?.();
    const userId: string = state?.app?.userId ?? 'anonymous';
    headers.set('X-Ms-Client-Principal-Id', userId);
  } catch {
    headers.set('X-Ms-Client-Principal-Id', 'anonymous');
  }

  return { ...init, headers };
});

// ---- response interceptor: uniform error handling ----
httpClient.onResponse((response) => {
  if (!response.ok) {
    // Don't throw for streaming endpoints — callers handle those manually.
    // Clone so the body remains readable for callers that want custom handling.
    const cloned = response.clone();
    console.error(
      `[httpClient] ${response.status} ${response.statusText} – ${cloned.url}`,
    );
  }
  return response;
});

export default httpClient;
