import { useEffect, useRef, useState } from 'react';
import { consumptionApi, customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';
import { Button } from '@/shared/ui/Button';
import { Select } from '@/shared/ui/Select';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface Point96 {
  id: number;
  customer_account_id: number;
  customer_name: string;
  data_date: string;
  data_month: string;
  file_name: string;
  status: string;
  created_at: string;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

export default function Point96Page() {
  const [data, setData] = useState<Point96[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [customerId, setCustomerId] = useState('');
  const [dataMonth, setDataMonth] = useState('');
  const [dataDate, setDataDate] = useState('');
  const [importCustomerId, setImportCustomerId] = useState('');
  const [importDate, setImportDate] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const pageSize = 20;

  const showMessage = (message: string, type: 'success' | 'error') => {
    if (type === 'success') {
      setSuccess(message);
      setError(null);
    } else {
      setError(message);
      setSuccess(null);
    }
    setTimeout(() => {
      setSuccess(null);
      setError(null);
    }, 4000);
  };

  const fetchCustomers = async () => {
    try {
      const res = (await customerApi.simpleList()) as unknown as { success: boolean; data?: CustomerOption[] };
      setCustomers(res.data || []);
    } catch {
      setCustomers([]);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerId) params.customer_account_id = Number(customerId);
      if (dataMonth) params.data_month = dataMonth;
      if (dataDate) params.data_date = dataDate;
      const res = (await consumptionApi.point96Page(params)) as unknown as {
        success: boolean;
        data?: PageResult<Point96>;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '加载失败');
      setData(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载96点数据失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    fetchData();
  }, [page]);

  const customerOptions = [
    { value: '', label: '全部客户' },
    ...customers.map((c) => ({ value: String(c.id), label: c.customer_name })),
  ];
  const customerFormOptions = [
    { value: '', label: '请选择客户' },
    ...customers.map((c) => ({ value: String(c.id), label: c.customer_name })),
  ];

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file || !importCustomerId || !importDate) {
      showMessage('请选择客户、日期和文件', 'error');
      return;
    }
    setActionLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('customer_account_id', importCustomerId);
      formData.append('data_date', importDate);
      const res = await consumptionApi.point96Import(formData);
      if (!res.ok) {
        const body = await res.json().catch(() => ({ message: '导入失败' }));
        throw new Error(body.message || '导入失败');
      }
      showMessage('导入成功', 'success');
      setImportCustomerId('');
      setImportDate('');
      if (fileRef.current) fileRef.current.value = '';
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '导入失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConvert = async (id: number) => {
    setActionLoading(true);
    try {
      const res = (await consumptionApi.point96ConvertToDaily(id)) as unknown as {
        success: boolean;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '转换失败');
      showMessage('转换成功', 'success');
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '转换失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>96点数据</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 rounded-lg border border-success/20 bg-success/10 px-4 py-3 text-sm text-success">
              <RotateCcw size={16} />
              {success}
            </div>
          )}

          <form
            onSubmit={handleImport}
            className="p-4 rounded-lg border border-border bg-background-tertiary/50 space-y-4"
          >
            <h2 className="text-sm font-semibold text-foreground">导入96点数据</h2>
            <div className="flex flex-wrap gap-4 items-end">
              <div className="w-48 space-y-1.5">
                <label className="text-sm font-medium text-foreground">客户</label>
                <Select value={importCustomerId} options={customerFormOptions} onChange={(v) => setImportCustomerId(v)} searchable />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">日期</label>
                <input
                  type="date"
                  value={importDate}
                  onChange={(e) => setImportDate(e.target.value)}
                  className={cn(
                    'flex h-10 w-44 rounded-lg border px-3 py-2 text-sm',
                    'bg-background-tertiary text-foreground',
                    'border-transparent placeholder:text-foreground-tertiary',
                    'transition-all duration-200 focus:outline-none focus:border-foreground'
                  )}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">文件</label>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  className="block text-sm text-foreground file:mr-3 file:rounded-md file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-xs file:text-white hover:file:bg-accent-hover"
                />
              </div>
              <Button type="submit" isLoading={actionLoading}>导入</Button>
            </div>
          </form>

          <div className="flex flex-wrap gap-3 items-end">
            <div className="w-48 space-y-1.5">
              <label className="text-sm font-medium text-foreground">客户</label>
              <Select value={customerId} options={customerOptions} onChange={(v) => { setCustomerId(v); setPage(1); }} searchable />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">月份</label>
              <input
                type="month"
                value={dataMonth}
                onChange={(e) => { setDataMonth(e.target.value); setPage(1); }}
                className={cn(
                  'flex h-10 w-40 rounded-lg border px-3 py-2 text-sm',
                  'bg-background-tertiary text-foreground',
                  'border-transparent placeholder:text-foreground-tertiary',
                  'transition-all duration-200 focus:outline-none focus:border-foreground'
                )}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">日期</label>
              <input
                type="date"
                value={dataDate}
                onChange={(e) => { setDataDate(e.target.value); setPage(1); }}
                className={cn(
                  'flex h-10 w-44 rounded-lg border px-3 py-2 text-sm',
                  'bg-background-tertiary text-foreground',
                  'border-transparent placeholder:text-foreground-tertiary',
                  'transition-all duration-200 focus:outline-none focus:border-foreground'
                )}
              />
            </div>
            <Button onClick={handleSearch}>查询</Button>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>客户</th>
                  <th>日期</th>
                  <th>月份</th>
                  <th>文件名</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th className="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={7} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
                ) : data.length === 0 ? (
                  <tr><td colSpan={7} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
                ) : (
                  data.map((item) => (
                    <tr key={item.id} className="hover:bg-background-hover">
                      <td className="font-medium">{item.customer_name}</td>
                      <td>{item.data_date}</td>
                      <td>{item.data_month}</td>
                      <td>{item.file_name || '-'}</td>
                      <td>{item.status || '-'}</td>
                      <td>{item.created_at || '-'}</td>
                      <td className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => handleConvert(item.id)}>
                          转日用电
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center text-sm text-foreground-secondary">
            <span>共 {total} 条</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 rounded border border-border disabled:opacity-40"
              >
                上一页
              </button>
              <span className="px-3 py-1">第 {page} 页</span>
              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 rounded border border-border disabled:opacity-40"
              >
                下一页
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
