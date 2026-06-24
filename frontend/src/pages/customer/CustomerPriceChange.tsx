import { useEffect, useState } from 'react';
import { customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { DatePicker } from '@/shared/ui/DatePicker';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface PriceHistoryItem {
  id: number;
  customer_account_id: number;
  customer_name: string;
  old_price_difference: string | number | null;
  new_price_difference: string | number | null;
  effective_date: string;
  change_reason: string | null;
  created_at: string;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

export default function CustomerPriceChange() {
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [customerId, setCustomerId] = useState('');
  const [newPriceDifference, setNewPriceDifference] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [changeReason, setChangeReason] = useState('');
  const [newContractStartDate, setNewContractStartDate] = useState('');
  const [newContractEndDate, setNewContractEndDate] = useState('');

  const [history, setHistory] = useState<PriceHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
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
      const res = (await customerApi.simpleList()) as unknown as {
        success: boolean;
        data?: CustomerOption[];
      };
      setCustomers(res.data || []);
    } catch {
      setCustomers([]);
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerId) params.customer_account_id = Number(customerId);
      const res = (await customerApi.priceHistoryPage(params)) as unknown as {
        success: boolean;
        data?: PageResult<PriceHistoryItem>;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '加载失败');
      setHistory(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载变更历史失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [page]);

  const customerOptions = [
    { value: '', label: '全部客户' },
    ...customers.map((c) => ({ value: String(c.id), label: c.customer_name })),
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || !newPriceDifference || !effectiveDate) {
      showMessage('请填写必填项', 'error');
      return;
    }
    setActionLoading(true);
    try {
      const res = (await customerApi.updatePriceAndContract({
        customer_account_id: Number(customerId),
        new_price_difference: Number(newPriceDifference),
        effective_date: effectiveDate,
        change_reason: changeReason,
        new_contract_start_date: newContractStartDate || undefined,
        new_contract_end_date: newContractEndDate || undefined,
      })) as unknown as { success: boolean; message?: string };
      if (!res.success) throw new Error(res.message || '价格变更失败');
      showMessage('价格变更提交成功', 'success');
      setNewPriceDifference('');
      setEffectiveDate('');
      setChangeReason('');
      setNewContractStartDate('');
      setNewContractEndDate('');
      await fetchHistory();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '价格变更失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>价格变更</CardTitle>
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

          <form onSubmit={handleSubmit} className="p-4 rounded-lg border border-border bg-background-tertiary/50 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">
                  客户 <span className="text-danger">*</span>
                </label>
                <Select
                  value={customerId}
                  options={customerOptions}
                  onChange={(v) => setCustomerId(v)}
                  searchable
                />
              </div>
              <Input
                label="新价差"
                type="number"
                step="0.0001"
                required
                value={newPriceDifference}
                onChange={(e) => setNewPriceDifference(e.target.value)}
                placeholder="元/度"
              />
              <DatePicker
                label="生效日期"
                value={effectiveDate}
                onChange={(v) => setEffectiveDate(v)}
              />
              <DatePicker
                label="新合同开始"
                value={newContractStartDate}
                onChange={(v) => setNewContractStartDate(v)}
              />
              <DatePicker
                label="新合同结束"
                value={newContractEndDate}
                onChange={(v) => setNewContractEndDate(v)}
              />
              <Input
                label="变更原因"
                value={changeReason}
                onChange={(e) => setChangeReason(e.target.value)}
                placeholder="可选"
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" isLoading={actionLoading}>
                提交变更
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>变更历史</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>客户</th>
                  <th className="text-right">原价差</th>
                  <th className="text-right">新价差</th>
                  <th>生效日期</th>
                  <th>变更原因</th>
                  <th>操作时间</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-foreground-muted">加载中...</td>
                  </tr>
                ) : history.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-foreground-muted">暂无数据</td>
                  </tr>
                ) : (
                  history.map((item) => (
                    <tr key={item.id} className="hover:bg-background-hover">
                      <td>{item.customer_name}</td>
                      <td className="text-right font-mono-num">{item.old_price_difference ?? '-'}</td>
                      <td className="text-right font-mono-num">{item.new_price_difference ?? '-'}</td>
                      <td>{item.effective_date}</td>
                      <td>{item.change_reason || '-'}</td>
                      <td>{item.created_at}</td>
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
