const BASE_URL = import.meta.env.DEV ? '/api' : '/api';

const TOKEN_KEY = 'auth_token';

interface RequestOptions {
  method?: string;
  params?: Record<string, unknown>;
  body?: unknown;
  headers?: Record<string, string>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // ignore
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', params, body, headers } = options;

  let url = `${BASE_URL}${path}`;
  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') {
        searchParams.append(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const token = getToken();
  const isFormData = body instanceof FormData;

  const res = await fetch(url, {
    method,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(body ? { body: isFormData ? (body as FormData) : JSON.stringify(body) } : {}),
  });

  if (!res.ok) {
    // Global 401 handling: clear token and notify the app
    if (res.status === 401 && !path.includes('/auth/login')) {
      setToken(null);
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:expired', { detail: { message: '登录已过期' } }));
      }
    }
    const errBody = await res.json().catch(() => ({ message: res.statusText }));
    throw new ApiError(res.status, errBody.message || res.statusText);
  }

  return res.json() as Promise<T>;
}

// Convenience methods
export const api = {
  get: <T>(path: string, params?: Record<string, unknown>) =>
    request<T>(path, { method: 'GET', params }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body }),

  delete: <T>(path: string, params?: Record<string, unknown>) =>
    request<T>(path, { method: 'DELETE', params }),
};
