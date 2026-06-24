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
import { AlertCircle, RotateCcw, Upload, Split } from 'lucide-react';

interface HourlyConsumption {
  id: number;
  customer_account_id: number;
  customer_name: string;
  data_date: string;
  data_month: string;
  hour_index: number;
  consumption_value: string | number | null;
  time_period: string | null;
}

interface CustomerOption {
  id: number;
  customer_name: string;
}

const TIME_PERIOD_MAP: Record<string, string> = {
  '1': '尖峰',
  '2': '高峰',
  '3': '平时',
  '4': '低谷',
};

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) => ({
  value: String(i),
  label: `H${String(i).padStart(2, '0')}`,
}));

export default function HourlyConsumptionPage() {
  const [data, setData] = useState<HourlyConsumption[]>([]);
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
  const pageSize = 20;

  const [submitOpen, setSubmitOpen] = useState(false);
  const [splitOpen, setSplitOpen] = useState(false);

  const [submitCustomerId, setSubmitCustomerId] = useState('');
  const [submitDate, setSubmitDate] = useState('');
  const [submitHours, setSubmitHours] = useState<string[]>(Array(24).fill(''));

  const [splitCustomerId, setSplitCustomerId] = useState('');
  const [splitDate, setSplitDate] = useState('');
  const [splitValues, setSplitValues] = useState({ peak: '', high: '', normal: '', valley: '' });

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
      const res = (await consumptionApi.hourlyPage(params)) as unknown as {
        success: boolean;
        data?: PageResult<HourlyConsumption>;
        message?: string;
      };
      if (!res.success) throw new Error(res.message || '加载失败');
      setData(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '加载小时用电失败', 'error');
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

  const resetSubmit = () => {
    setSubmitCustomerId('');
    setSubmitDate('');
    setSubmitHours(Array(24).fill(''));
  };

  const handleSubmit24h = async () => {
    if (!submitCustomerId || !submitDate) {
      showMessage('请选择客户和日期', 'error');
      return;
    }
    setActionLoading(true);
    try {
      const hours = submitHours.map((v) => (v === '' ? 0 : Number(v)));
      const res = (await consumptionApi.hourlySubmit24h({
        customer_account_id: Number(submitCustomerId),
        data_date: submitDate,
        hours,
      })) as unknown as { success: boolean; message?: string };
      if (!res.success) throw new Error(res.message || '提交失败');
      showMessage('24小时数据提交成功', 'success');
      setSubmitOpen(false);
      resetSubmit();
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '提交失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSplit = async () => {
    if (!splitCustomerId || !splitDate) {
      showMessage('请选择客户和日期', 'error');
      return;
    }
    setActionLoading(true);
    try {
      const res = (await consumptionApi.hourlySplitFromTOU({
        customer_account_id: Number(splitCustomerId),
        data_date: splitDate,
        peak: Number(splitValues.peak || 0),
        high: Number(splitValues.high || 0),
        normal: Number(splitValues.normal || 0),
        valley: Number(splitValues.valley || 0),
      })) as unknown as { success: boolean; message?: string };
      if (!res.success) throw new Error(res.message || '拆分失败');
      showMessage('峰谷拆分成功', 'success');
      setSplitOpen(false);
      setSplitCustomerId('');
      setSplitDate('');
      setSplitValues({ peak: '', high: '', normal: '', valley: '' });
      await fetchData();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : '拆分失败', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>小时用电数据</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={() => { resetSubmit(); setSubmitOpen(true); }}>
              <Upload size={16} />
              提交24h数据
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setSplitOpen(true)}>
              <Split size={16} />
              峰谷拆分
            </Button>
          </div>
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
            <Button onClick={handleSearch}>查询</Button>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="data-table">
              <thead className="bg-background-tertiary">
                <tr>
                  <th>客户</th>
                  <th>日期</th>
                  <th>月份</th>
                  <th>小时</th>
                  <th className="text-right">用电量</th>
                  <th>峰平谷</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
                ) : data.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
                ) : (
                  data.map((item) => (
                    <tr key={item.id} className="hover:bg-background-hover">
                      <td className="font-medium">{item.customer_name}</td>
                      <td>{item.data_date}</td>
                      <td>{item.data_month}</td>
                      <td>H{String(item.hour_index).padStart(2, '0')}</td>
                      <td className="text-right font-mono-num">{Number(item.consumption_value || 0).toFixed(2)}</td>
                      <td>{TIME_PERIOD_MAP[String(item.time_period)] || item.time_period || '-'}</td>
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

      {/* Submit 24h Modal */}
      <Modal
        open={submitOpen}
        onClose={() => { setSubmitOpen(false); resetSubmit(); }}
        title="提交24小时用电数据"
        description="选择客户和日期，填写每小时用电量"
        footer={
          <>
            <Button variant="ghost" onClick={() => { setSubmitOpen(false); resetSubmit(); }} disabled={actionLoading}>
              取消
            </Button>
            <Button onClick={handleSubmit24h} isLoading={actionLoading}>
              提交
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">客户</label>
              <Select value={submitCustomerId} options={customerFormOptions} onChange={(v) => setSubmitCustomerId(v)} searchable />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">日期</label>
              <input
                type="date"
                value={submitDate}
                onChange={(e) => setSubmitDate(e.target.value)}
                className={cn(
                  'flex h-10 w-full rounded-lg border px-3 py-2 text-sm',
                  'bg-background-tertiary text-foreground',
                  'border-transparent placeholder:text-foreground-tertiary',
                  'transition-all duration-200 focus:outline-none focus:border-foreground'
                )}
              />
            </div>
          </div>
          <div className="grid grid-cols-6 gap-2">
            {submitHours.map((v, i) => (
              <Input
                key={i}
                label={`H${String(i).padStart(2, '0')}`}
                type="number"
                step="0.01"
                value={v}
                onChange={(e) => {
                  const next = [...submitHours];
                  next[i] = e.target.value;
                  setSubmitHours(next);
                }}
                className="text-xs"
              />
            ))}
          </div>
        </div>
      </Modal>

      {/* Split TOU Modal */}
      <Modal
        open={splitOpen}
        onClose={() => { setSplitOpen(false); setSplitCustomerId(''); setSplitDate(''); setSplitValues({ peak: '', high: '', normal: '', valley: '' }); }}
        title="峰谷平拆分"
        description="输入各时段总电量，系统自动拆分到24小时"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => { setSplitOpen(false); setSplitCustomerId(''); setSplitDate(''); setSplitValues({ peak: '', high: '', normal: '', valley: '' }); }}
              disabled={actionLoading}
            >
              取消
            </Button>
            <Button onClick={handleSplit} isLoading={actionLoading}>
              拆分
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">客户</label>
              <Select value={splitCustomerId} options={customerFormOptions} onChange={(v) => setSplitCustomerId(v)} searchable />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">日期</label>
              <input
                type="date"
                value={splitDate}
                onChange={(e) => setSplitDate(e.target.value)}
                className={cn(
                  'flex h-10 w-full rounded-lg border px-3 py-2 text-sm',
                  'bg-background-tertiary text-foreground',
                  'border-transparent placeholder:text-foreground-tertiary',
                  'transition-all duration-200 focus:outline-none focus:border-foreground'
                )}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="尖峰电量"
              type="number"
              step="0.01"
              value={splitValues.peak}
              onChange={(e) => setSplitValues((s) => ({ ...s, peak: e.target.value }))}
            />
            <Input
              label="高峰电量"
              type="number"
              step="0.01"
              value={splitValues.high}
              onChange={(e) => setSplitValues((s) => ({ ...s, high: e.target.value }))}
            />
            <Input
              label="平时电量"
              type="number"
              step="0.01"
              value={splitValues.normal}
              onChange={(e) => setSplitValues((s) => ({ ...s, normal: e.target.value }))}
            />
            <Input
              label="低谷电量"
              type="number"
              step="0.01"
              value={splitValues.valley}
              onChange={(e) => setSplitValues((s) => ({ ...s, valley: e.target.value }))}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
