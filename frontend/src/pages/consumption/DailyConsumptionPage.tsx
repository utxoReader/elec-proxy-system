import { useEffect, useState } from 'react';
import { consumptionApi, customerApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';
import { Button } from '@/shared/ui/Button';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { Modal } from '@/shared/ui/Modal';
import { DatePicker } from '@/shared/ui/DatePicker';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/Card';
import { cn } from '@/shared/utils';
import { AlertCircle, RotateCcw, Plus, Pencil, Trash2 } from 'lucide-react';

interface DailyConsumption {
  id: number;
  customer_account_id: number;
  customer_name: string;
  data_date: string;
  data_month: string;
  total_consumption: string | number | null;
  hour_1: string | number | null; hour_2: string | number | null; hour_3: string | number | null;
  hour_4: string | number | null; hour_5: string | number | null; hour_6: string | number | null;
  hour_7: string | number | null; hour_8: string | number | null; hour_9: string | number | null;
  hour_10: string | number | null; hour_11: string | number | null; hour_12: string | number | null;
  hour_13: string | number | null; hour_14: string | number | null; hour_15: string | number | null;
  hour_16: string | number | null; hour_17: string | number | null; hour_18: string | number | null;
  hour_19: string | number | null; hour_20: string | number | null; hour_21: string | number | null;
  hour_22: string | number | null; hour_23: string | number | null; hour_24: string | number | null;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

const HOUR_KEYS = Array.from({ length: 24 }, (_, i) => `hour_${i + 1}` as keyof DailyConsumption);

export default function DailyConsumptionPage() {
  const [data, setData] = useState<DailyConsumption[]>([]);
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
  const [showHours, setShowHours] = useState(false);
  const pageSize = 20;

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DailyConsumption | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});

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

  const resetForm = () => {
    const next: Record<string, string> = {
      customer_account_id: '',
      data_date: '',
      total_consumption: '',
    };
    HOUR_KEYS.forEach((k) => { next[k] = ''; });
    setForm(next);
  };

  const itemToForm = (item: DailyConsumption) => {
    const next: Record<string, string> = {
      customer_account_id: String(item.customer_account_id),
      data_date: item.data_date,
      total_consumption: item.total_consumption !== null ? String(item.total_consumption) : '',
    };
    HOUR_KEYS.forEach((k) => {
      const v = item[k];
      next[k] = v !== null ? String(v) : '';
    });
    setForm(next);
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
      const res = (await consumptionApi.dailyPage(params)) as unknown as {
        success: boolean;
        data?: PageResult<DailyConsumption>;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '加载失败');
      setData(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载日用电失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
    resetForm();
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

  const openCreate = () => {
    setEditing(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (item: DailyConsumption) => {
    setEditing(item);
    itemToForm(item);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.customer_account_id || !form.data_date) {
      showMessage('请填写客户和日期', 'error');
      return;
    }
    setActionLoading(true);
    try {
      const payload: Record<string, unknown> = {
        customer_account_id: Number(form.customer_account_id),
        data_date: form.data_date,
        total_consumption: form.total_consumption ? Number(form.total_consumption) : 0,
      };
      HOUR_KEYS.forEach((k) => {
        payload[k] = form[k] ? Number(form[k]) : 0;
      });
      if (editing) {
        const res = (await consumptionApi.dailyUpdate({ ...payload, id: editing.id })) as unknown as {
          success: boolean;
          message?: string;
        };
        if (!res.success) throw new Error(res.message || '更新失败');
        showMessage('日用电更新成功', 'success');
      } else {
        const res = (await consumptionApi.dailyCreate(payload)) as unknown as {
          success: boolean;
          message?: string;
        };
        if (!res.success) throw new Error(res.message || '创建失败');
        showMessage('日用电创建成功', 'success');
      }
      setModalOpen(false);
      resetForm();
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '操作失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const [deleteTarget, setDeleteTarget] = useState<DailyConsumption | null>(null);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setActionLoading(true);
    try {
      const res = (await consumptionApi.dailyDelete(deleteTarget.id)) as unknown as {
        success: boolean;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '删除失败');
      showMessage('日用电删除成功', 'success');
      setDeleteTarget(null);
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '删除失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>日用电数据</CardTitle>
          <Button size="sm" onClick={openCreate}>
            <Plus size={16} />
            新增
          </Button>
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
            <div className="w-48 space-y-1.5">
              <label className="text-sm font-medium text-foreground">客户</label>
              <Select value={customerId} options={customerOptions} onChange={(v) => { setCustomerId(v); setPage(1); }} searchable />
            </div>
            <DatePicker
              label="月份"
              mode="month"
              value={dataMonth}
              onChange={(v) => { setDataMonth(v); setPage(1); }}
              className="w-40"
            />
            <DatePicker
              label="日期"
              value={dataDate}
              onChange={(v) => { setDataDate(v); setPage(1); }}
              className="w-44"
            />
            <label className="flex items-center gap-2 text-sm text-foreground-secondary">
              <input
                type="checkbox"
                checked={showHours}
                onChange={(e) => setShowHours(e.target.checked)}
                className="rounded border-border bg-background-tertiary text-accent"
              />
              显示24小时明细
            </label>
            <Button onClick={handleSearch}>查询</Button>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>客户</th>
                  <th>日期</th>
                  <th>月份</th>
                  <th className="text-right">总电量</th>
                  {showHours && HOUR_KEYS.map((k) => <th key={k} className="text-right">{String(k).replace('hour_', 'H')}</th>)}
                  <th className="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={showHours ? 28 : 5} className="text-center py-8 text-foreground-muted">加载中...</td>
                  </tr>
                ) : data.length === 0 ? (
                  <tr>
                    <td colSpan={showHours ? 28 : 5} className="text-center py-8 text-foreground-muted">暂无数据</td>
                  </tr>
                ) : (
                  data.map((item) => (
                    <tr key={item.id} className="hover:bg-background-hover">
                      <td className="font-medium">{item.customer_name}</td>
                      <td>{item.data_date}</td>
                      <td>{item.data_month}</td>
                      <td className="text-right font-mono-num">{Number(item.total_consumption || 0).toFixed(2)}</td>
                      {showHours && HOUR_KEYS.map((k) => {
                        const v = item[k];
                        return (
                          <td key={k} className="text-right font-mono-num">
                            {v !== null ? Number(v).toFixed(2) : '-'}
                          </td>
                        );
                      })}
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="icon" onClick={() => openEdit(item)} title="编辑">
                            <Pencil size={16} />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(item)} title="删除">
                            <Trash2 size={16} className="text-danger" />
                          </Button>
                        </div>
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

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); resetForm(); }}
        title={editing ? '编辑日用电' : '新增日用电'}
        description="填写客户、日期、总电量和24小时明细"
        className="max-w-4xl"
        footer={
          <>
            <Button variant="ghost" onClick={() => { setModalOpen(false); resetForm(); }} disabled={actionLoading}>
              取消
            </Button>
            <Button onClick={handleSubmit} isLoading={actionLoading}>
              {editing ? '保存修改' : '创建'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">客户</label>
              <Select value={form.customer_account_id || ''} options={customerFormOptions} onChange={(v) => setForm((f) => ({ ...f, customer_account_id: v }))} searchable />
            </div>
            <DatePicker
              label="日期"
              value={form.data_date || ''}
              onChange={(v) => setForm((f) => ({ ...f, data_date: v }))}
            />
          </div>
          <Input
            label="总电量"
            type="number"
            step="0.01"
            value={form.total_consumption || ''}
            onChange={(e) => setForm((f) => ({ ...f, total_consumption: e.target.value }))}
          />
          <div>
            <label className="text-sm font-medium text-foreground mb-2 block">24小时电量</label>
            <div className="grid grid-cols-6 gap-2">
              {HOUR_KEYS.map((k) => (
                <Input
                  key={k}
                  label={String(k).replace('hour_', 'H')}
                  type="number"
                  step="0.01"
                  value={form[k] || ''}
                  onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))}
                  className="text-xs"
                />
              ))}
            </div>
          </div>
        </div>
      </Modal>

      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="确认删除"
        description={deleteTarget ? `确定删除 ${deleteTarget.customer_name} 在 ${deleteTarget.data_date} 的日用电数据？` : ''}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} disabled={actionLoading}>
              取消
            </Button>
            <Button variant="danger" onClick={handleDelete} isLoading={actionLoading}>
              删除
            </Button>
          </>
        }
      >
        <div />
      </Modal>
    </div>
  );
}
