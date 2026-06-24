import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { inquiryApi, customerApi, agentApi } from '@/shared/api';
import type { PackageType } from '@/shared/types';

interface CustomerOption {
  id: number;
  customer_name: string;
}

interface AgentOption {
  id: number;
  agent_name: string;
}

const HOUR_KEYS = Array.from({ length: 24 }, (_, i) => `hour_${i + 1}`);

export default function InquiryCreate() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState<Record<string, unknown>>({
    customer_id: '',
    agent_id: '',
    usage_month: '',
    package_type: 'flat_rate',
    estimated_monthly_consumption: '',
    contact_name: '',
    contact_phone: '',
    remark: '',
    peak_consumption: '',
    high_consumption: '',
    normal_consumption: '',
    valley_consumption: '',
  });
  const [hours, setHours] = useState<Record<string, string>>({});
  const [consumptionDataType, setConsumptionDataType] = useState<'peak_valley' | '24h' | 'file'>('peak_valley');

  useEffect(() => {
    const fetchBase = async () => {
      try {
        const cRes = await customerApi.simpleList();
        setCustomers(((cRes as unknown as { data: CustomerOption[] }).data) || []);
        const aRes = await agentApi.list();
        setAgents(((aRes as unknown as { data: AgentOption[] }).data) || []);
      } catch {
        setCustomers([]);
        setAgents([]);
      }
    };
    fetchBase();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Record<string, unknown> = { ...form };
    if (payload.estimated_monthly_consumption) payload.estimated_monthly_consumption = Number(payload.estimated_monthly_consumption);
    if (payload.customer_id) payload.customer_id = Number(payload.customer_id);
    if (payload.agent_id) payload.agent_id = Number(payload.agent_id);

    if (consumptionDataType === '24h') {
      payload.hourly_consumption = HOUR_KEYS.map(k => Number(hours[k] || 0));
    } else if (consumptionDataType === 'peak_valley') {
      payload.peak_consumption = Number(payload.peak_consumption);
      payload.high_consumption = Number(payload.high_consumption);
      payload.normal_consumption = Number(payload.normal_consumption);
      payload.valley_consumption = Number(payload.valley_consumption);
    }

    try {
      const res = await inquiryApi.create(payload);
      const newId = (res as unknown as { data: { id: number } }).data?.id;
      if (consumptionDataType === 'file' && newId && fileRef.current?.files?.[0]) {
        const fd = new FormData();
        fd.append('file', fileRef.current.files[0]);
        await inquiryApi.uploadConsumptionData(newId, fd);
      }
      navigate('/inquiries');
    } catch (err) {
      alert(err instanceof Error ? err.message : '创建失败');
    }
  };

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <h1 className="text-xl font-bold text-foreground">新建询价</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">客户</label>
            <select required value={String(form.customer_id || '')} onChange={e => setForm({ ...form, customer_id: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
              <option value="">请选择</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">代理</label>
            <select value={String(form.agent_id || '')} onChange={e => setForm({ ...form, agent_id: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
              <option value="">请选择</option>
              {agents.map(a => <option key={a.id} value={a.id}>{a.agent_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">用电月份</label>
            <input required type="month" value={String(form.usage_month || '')} onChange={e => setForm({ ...form, usage_month: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">套餐类型</label>
            <select value={String(form.package_type || 'flat_rate')} onChange={e => setForm({ ...form, package_type: e.target.value as PackageType })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
              <option value="flat_rate">固定电价</option>
              <option value="time_of_use">分时电价</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">预估用电量</label>
            <input required type="number" step="0.01" value={String(form.estimated_monthly_consumption || '')} onChange={e => setForm({ ...form, estimated_monthly_consumption: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">联系人</label>
            <input value={String(form.contact_name || '')} onChange={e => setForm({ ...form, contact_name: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">联系电话</label>
            <input value={String(form.contact_phone || '')} onChange={e => setForm({ ...form, contact_phone: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
        </div>

        <div>
          <label className="block text-sm text-foreground-secondary mb-1">备注</label>
          <textarea value={String(form.remark || '')} onChange={e => setForm({ ...form, remark: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" rows={2} />
        </div>

        <div className="space-y-3">
          <label className="block text-sm text-foreground-secondary">用电数据</label>
          <div className="flex gap-4 text-sm text-foreground">
            <label className="flex items-center gap-1"><input type="radio" checked={consumptionDataType === 'peak_valley'} onChange={() => setConsumptionDataType('peak_valley')} /> 峰平谷</label>
            <label className="flex items-center gap-1"><input type="radio" checked={consumptionDataType === '24h'} onChange={() => setConsumptionDataType('24h')} /> 24小时</label>
            <label className="flex items-center gap-1"><input type="radio" checked={consumptionDataType === 'file'} onChange={() => setConsumptionDataType('file')} /> 上传文件</label>
          </div>

          {consumptionDataType === 'peak_valley' && (
            <div className="grid grid-cols-4 gap-3">
              <input type="number" step="0.01" placeholder="峰电量" value={String(form.peak_consumption || '')} onChange={e => setForm({ ...form, peak_consumption: e.target.value })} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
              <input type="number" step="0.01" placeholder="尖电量" value={String(form.high_consumption || '')} onChange={e => setForm({ ...form, high_consumption: e.target.value })} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
              <input type="number" step="0.01" placeholder="平电量" value={String(form.normal_consumption || '')} onChange={e => setForm({ ...form, normal_consumption: e.target.value })} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
              <input type="number" step="0.01" placeholder="谷电量" value={String(form.valley_consumption || '')} onChange={e => setForm({ ...form, valley_consumption: e.target.value })} className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
            </div>
          )}

          {consumptionDataType === '24h' && (
            <div className="grid grid-cols-6 gap-2">
              {HOUR_KEYS.map(k => (
                <input key={k} type="number" step="0.01" placeholder={k.replace('hour_', 'H')} value={hours[k] || ''} onChange={e => setHours({ ...hours, [k]: e.target.value })} className="px-2 py-1 rounded-md bg-background-secondary border border-border text-xs text-foreground" />
              ))}
            </div>
          )}

          {consumptionDataType === 'file' && (
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" className="text-sm text-foreground" />
          )}
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={() => navigate('/inquiries')} className="px-4 py-1.5 rounded-md border border-border text-sm text-foreground-secondary">取消</button>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">创建</button>
        </div>
      </form>
    </div>
  );
}
