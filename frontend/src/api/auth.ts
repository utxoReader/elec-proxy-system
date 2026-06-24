import { api, setToken } from './client';

export interface LoginResult {
  success: boolean;
  token?: string;
  error?: string;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function loginApi(username: string, password: string): Promise<LoginResult> {
  try {
    const res = await api.post<{ success: boolean; message?: string; data?: TokenData; error?: string }>(
      '/auth/login',
      { username, password }
    );
    if (res.success && res.data?.access_token) {
      setToken(res.data.access_token);
      return { success: true, token: res.data.access_token };
    }
    return { success: false, error: res.message || res.error || '登录失败' };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : '登录失败',
    };
  }
}

export async function registerApi(username: string, password: string): Promise<LoginResult> {
  try {
    const res = await api.post<{ success: boolean; message?: string; data?: TokenData; error?: string }>(
      '/auth/register',
      { username, password }
    );
    if (res.success && res.data?.access_token) {
      setToken(res.data.access_token);
      return { success: true, token: res.data.access_token };
    }
    return { success: false, error: res.message || res.error || '注册失败' };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : '注册失败',
    };
  }
}

export function logoutApi(): void {
  setToken(null);
}
