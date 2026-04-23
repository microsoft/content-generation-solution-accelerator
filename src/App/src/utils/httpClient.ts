/**
 * HTTP Client utility for making API requests
 * Centralizes fetch logic with consistent error handling and request interceptors
 */

const API_BASE = '/api';

type RequestInterceptor = (config: RequestInit) => RequestInit;

class HttpClient {
  private baseUrl: string;
  private requestInterceptors: RequestInterceptor[] = [];

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  /** Register a request interceptor to modify every outgoing request */
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  private applyInterceptors(config: RequestInit): RequestInit {
    return this.requestInterceptors.reduce((cfg, fn) => fn(cfg), config);
  }

  private async request<T>(method: string, path: string, options: RequestInit = {}): Promise<T> {
    const config = this.applyInterceptors({ ...options, method });
    const response = await fetch(`${this.baseUrl}${path}`, config);
    if (!response.ok) {
      throw new Error(`${method} ${path} failed: ${response.statusText}`);
    }
    return response.json();
  }

  async get<T>(path: string, signal?: AbortSignal): Promise<T> {
    return this.request<T>('GET', path, { signal });
  }

  async post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    return this.request<T>('POST', path, {
      signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  async delete(path: string, signal?: AbortSignal): Promise<void> {
    const config = this.applyInterceptors({ method: 'DELETE', signal });
    const response = await fetch(`${this.baseUrl}${path}`, config);
    if (!response.ok) {
      throw new Error(`DELETE ${path} failed: ${response.statusText}`);
    }
  }

  async put<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    return this.request<T>('PUT', path, {
      signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  /** Fetch without base URL prefix, for non-API endpoints like /.auth/me */
  async fetchExternal<T>(url: string, options?: RequestInit): Promise<T> {
    const config = this.applyInterceptors(options || {});
    const response = await fetch(url, config);
    if (!response.ok) {
      throw new Error(`${config.method || 'GET'} ${url} failed: ${response.statusText}`);
    }
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`${config.method || 'GET'} ${url} returned non-JSON response (${contentType})`);
    }
    return response.json();
  }
}

export const httpClient = new HttpClient();
