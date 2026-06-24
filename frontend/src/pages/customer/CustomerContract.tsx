import { useEffect, useState } from 'react';
import { customerApi } from '@/shared/api';
import { getToken } from '@/api/client';
import type { PageResult } from '@/shared/types';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Modal } from '@/shared/ui/Modal';
import { DatePicker } from '@/shared/ui/DatePicker';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface CustomerContractItem {
  id: number;
  customer_name: string;
  customer_status: number;
  contract_start_date: string | null;
  contract_end_date: string | null;
  price_difference: string | number | null;
  agent_name: string | null;
}

const STATUS_MAP: Record<number, { label: string; color: string }> = {
  1: { label: '待注册', color: 'bg-warning/10 text-warning' },
  2: { label: '待签约', color: 'bg-accent/10 text-accent' },
  3: { label: '已签约', color: 'bg-success/10 text-success' },
  4: { label: '已终止', color: 'bg-danger/10 text-danger' },
  5: { label: '已终止', color: 'bg-danger/10 text-danger' },
};

async function terminateContractApi(id: number, reason: string, terminateDate: string) {
  const token = getToken();
  const params = new URLSearchParams({
    id: String(id),
    reason,
    terminate_date: terminateDate,
  });
  const res = await fetch(`/api/elec/customer-account/terminate-contract?${params.toString()}`, {
    method: 'PUT',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const body = await res.json().catch(() => ({ message: res.statusText }));
  if (!res.ok) throw new Error(body.message || res.statusText);
  return body;
}

export default function CustomerContract() {
  const [data, setData] = useState<CustomerContractItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [customerName, setCustomerName] = useState('');
  const pageSize = 20;

  const [terminateModal, setTerminateModal] = useState<{ open: boolean; id: number | null; name: string }>({
    open: false,
    id: null,
    name: '',
  });
  const [terminateDate, setTerminateDate] = useState('');
  const [terminateReason, setTerminateReason] = useState('');

  const [renewModal, setRenewModal] = useState<{ open: boolean; id: number | null; name: string }>({
    open: false,
    id: null,
    name: '',
  });
  const [renewStart, setRenewStart] = useState('');
  const [renewEnd, setRenewEnd] = useState('');

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

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize };
      if (customerName.trim()) params.customer_name = customerName.trim();
      const res = (await customerApi.page(params)) as unknown as {
        success: boolean;
        data?: PageResult<CustomerContractItem>;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '加载失败');
      setData(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载合同列表失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page]);

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  const handleTerminate = async () => {
    if (!terminateModal.id || !terminateDate) return;
    setActionLoading(true);
    try {
      await terminateContractApi(terminateModal.id, terminateReason || '合同终止', terminateDate);
      showMessage('合同终止成功', 'success');
      setTerminateModal({ open: false, id: null, name: '' });
      setTerminateDate('');
      setTerminateReason('');
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '终止失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRenew = async () => {
    if (!renewModal.id || !renewStart || !renewEnd) return;
    setActionLoading(true);
    try {
      const res = (await customerApi.updatePriceAndContract({
        customer_account_id: renewModal.id,
        new_price_difference: 0,
        effective_date: renewStart,
        change_reason: '合同续签',
        new_contract_start_date: renewStart,
        new_contract_end_date: renewEnd,
      })) as unknown as { success: boolean; message?: string };
      if (!res.success) throw new Error(res.message || '续签失败');
      showMessage('合同续签成功', 'success');
      setRenewModal({ open: false, id: null, name: '' });
      setRenewStart('');
      setRenewEnd('');
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '续签失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>合同管理</CardTitle>
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

          <div className="flex flex-wrap gap-3 items-end">
            <Input
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="客户名称"
              className="w-64"
            />
            <Button onClick={handleSearch}>查询</Button>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>客户名称</th>
                  <th>状态</th>
                  <th>代理</th>
                  <th>合同开始</th>
                  <th>合同结束</th>
                  <th>价差</th>
                  <th className="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-foreground-muted">加载中...</td>
                  </tr>
                ) : data.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-foreground-muted">暂无数据</td>
                  </tr>
                ) : (
                  data.map((item) => {
                    const statusMeta = STATUS_MAP[item.customer_status] || { label: '未知', color: 'bg-foreground/10 text-foreground' };
                    const isTerminated = item.customer_status === 4 || item.customer_status === 5;
                    return (
                      <tr key={item.id} className="hover:bg-background-hover">
                        <td className="font-medium">{item.customer_name}</td>
                        <td>
                          <span className={cn('px-2 py-0.5 rounded text-xs', statusMeta.color)}>{statusMeta.label}</span>
                        </td>
                        <td>{item.agent_name || '-'}</td>
                        <td>{item.contract_start_date || '-'}</td>
                        <td>{item.contract_end_date || '-'}</td>
                        <td className="text-right font-mono-num">{item.price_difference ?? '-'}</td>
                        <td className="text-right">
                          {!isTerminated && (
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setRenewModal({ open: true, id: item.id, name: item.customer_name })}
                              >
                                续签
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setTerminateModal({ open: true, id: item.id, name: item.customer_name })}
                                className="text-danger hover:text-danger"
                              >
                                终止
                              </Button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })
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

      <Modal
        open={terminateModal.open}
        onClose={() => setTerminateModal({ open: false, id: null, name: '' })}
        title="终止合同"
        description={`客户：${terminateModal.name}`}
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setTerminateModal({ open: false, id: null, name: '' })}
              disabled={actionLoading}
            >
              取消
            </Button>
            <Button variant="danger" onClick={handleTerminate} isLoading={actionLoading}>
              确认终止
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <DatePicker
            label="终止日期"
            value={terminateDate}
            onChange={(v) => setTerminateDate(v)}
          />
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">终止原因</label>
            <textarea
              value={terminateReason}
              onChange={(e) => setTerminateReason(e.target.value)}
              rows={3}
              className={cn(
                'flex w-full rounded-lg border px-3 py-2 text-sm',
                'bg-background-tertiary text-foreground',
                'border-transparent placeholder:text-foreground-tertiary',
                'transition-all duration-200 focus:outline-none focus:border-foreground'
              )}
              placeholder="可选"
            />
          </div>
        </div>
      </Modal>

      <Modal
        open={renewModal.open}
        onClose={() => setRenewModal({ open: false, id: null, name: '' })}
        title="续签合同"
        description={`客户：${renewModal.name}`}
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setRenewModal({ open: false, id: null, name: '' })}
              disabled={actionLoading}
            >
              取消
            </Button>
            <Button onClick={handleRenew} isLoading={actionLoading}>
              确认续签
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <DatePicker
            label="新合同开始"
            value={renewStart}
            onChange={(v) => setRenewStart(v)}
          />
          <DatePicker
            label="新合同结束"
            value={renewEnd}
            onChange={(v) => setRenewEnd(v)}
          />
        </div>
      </Modal>
    </div>
  );
}
