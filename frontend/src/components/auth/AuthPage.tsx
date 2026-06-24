import { useState } from 'react';
import { useAuth } from '@/shared/auth/useAuth';
import { useTheme } from '@/shared/useTheme';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Card, CardContent } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { Moon, Sun, Eye, EyeOff } from 'lucide-react';

function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'fixed top-4 right-4 z-50 flex h-9 w-9 items-center justify-center rounded-full',
        'border border-border bg-background-secondary text-foreground-secondary',
        'transition-colors hover:border-foreground hover:text-foreground'
      )}
      aria-label={isDark ? '切换到浅色模式' : '切换到深色模式'}
    >
      {isDark ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const { login, register, isLoading, authExpired } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password) {
      setError('请输入用户名和密码');
      return;
    }
    const result = mode === 'login'
      ? await login(username.trim(), password)
      : await register(username.trim(), password);
    if (!result.success) {
      setError(result.error || '操作失败');
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background px-4">
      <ThemeToggle />

      <div className="w-full max-w-[420px]">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-foreground">桐叶售电</h1>
          <p className="mt-2 text-sm text-foreground-secondary">代理管理系统</p>
        </div>

        {authExpired && (
          <div className="mb-4 rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning">
            会话已过期，请重新登录
          </div>
        )}

        <Card>
          <CardContent className="pt-6">
            <div className="mb-6 flex rounded-lg bg-background-secondary p-1">
              <button
                type="button"
                onClick={() => { setMode('login'); setError(''); }}
                className={cn(
                  'flex-1 rounded-md py-2 text-sm font-medium transition-colors',
                  mode === 'login'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-foreground-muted hover:text-foreground-secondary'
                )}
              >
                登录
              </button>
              <button
                type="button"
                onClick={() => { setMode('register'); setError(''); }}
                className={cn(
                  'flex-1 rounded-md py-2 text-sm font-medium transition-colors',
                  mode === 'register'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-foreground-muted hover:text-foreground-secondary'
                )}
              >
                注册
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {error && (
                <div className="rounded-lg bg-danger-light px-3 py-2 text-xs text-danger">
                  {error}
                </div>
              )}

              <Input
                type="text"
                label="用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                data-testid="auth-username"
              />

              <Input
                type={showPassword ? 'text' : 'password'}
                label="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                data-testid="auth-password"
                rightElement={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="hover:text-foreground-secondary"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                }
              />

              <Button type="submit" size="lg" isLoading={isLoading} className="mt-2" data-testid="auth-submit">
                {mode === 'login' ? '登录' : '注册'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
