import { useEffect, useState } from 'react';
import { consumptionApi, customerApi } from '@/shared/api';

interface CustomerOption {
  id: number;
  customer_name: string;
}

interface Point96Option {
  id: number;
  file_name: string;
}

interface TemplateOption {
  id: number;
  template_name: string;
}

export default function ConversionPage() {
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [point96List, setPoint96List] = useState<Point96Option[]>([]);
  const [templates, setTemplates] = useState<TemplateOption[]>([]);

  const [point96Id, setPoint96Id] = useState('');

  const [templateId, setTemplateId] = useState('');
  const [peak, setPeak] = useState('');
  const [high, setHigh] = useState('');
  const [normal, setNormal] = useState('');
  const [valley, setValley] = useState('');
  const [isPeakMonth, setIsPeakMonth] = useState(true);

  const [fillCustomerId, setFillCustomerId] = useState('');
  const [fillMonth, setFillMonth] = useState('');

  const [copySourceId, setCopySourceId] = useState('');
  const [copyTargetId, setCopyTargetId] = useState('');
  const [copyMonth, setCopyMonth] = useState('');

  useEffect(() => {
    const fetchBase = async () => {
      try {
        const customerRes = await customerApi.simpleList();
        setCustomers(((customerRes as unknown as { data: CustomerOption[] }).data) || []);
        const pointRes = await consumptionApi.point96Page({ page: 1, page_size: 100 });
        setPoint96List((((pointRes as unknown as { data: { items: Point96Option[] } }).data?.items) || []));
        const templateRes = await consumptionApi.usageCurveTemplatePage({ page: 1, page_size: 100 });
        setTemplates((((templateRes as unknown as { data: { items: TemplateOption[] } }).data?.items) || []));
      } catch {
        setCustomers([]);
      }
    };
    fetchBase();
  }, []);

  const handlePoint96To24h = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!point96Id) return;
    try {
      await consumptionApi.conversionPoint96To24h(Number(point96Id));
      alert('转换成功');
    } catch (err) {
      alert(err instanceof Error ? err.message : '转换失败');
    }
  };

  const handlePeakValleyTo24h = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await consumptionApi.conversionPeakValleyTo24h({
        template_id: Number(templateId),
        peak: Number(peak),
        high: Number(high),
        normal: Number(normal),
        valley: Number(valley),
        is_peak_month: isPeakMonth,
      });
      alert('转换成功');
    } catch (err) {
      alert(err instanceof Error ? err.message : '转换失败');
    }
  };

  const handleFillMissing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fillCustomerId || !fillMonth) return;
    try {
      await consumptionApi.conversionFillMissing(Number(fillCustomerId), fillMonth);
      alert('补全成功');
    } catch (err) {
      alert(err instanceof Error ? err.message : '补全失败');
    }
  };

  const handleCopyData = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!copySourceId || !copyTargetId || !copyMonth) return;
    try {
      await consumptionApi.conversionCopyData(Number(copySourceId), Number(copyTargetId), copyMonth);
      alert('复制成功');
    } catch (err) {
      alert(err instanceof Error ? err.message : '复制失败');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-bold text-foreground">数据转换</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <form onSubmit={handlePoint96To24h} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">96点转24小时</h2>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">96点数据</label>
            <select required value={point96Id} onChange={e => setPoint96Id(e.target.value)} className="w-full px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">请选择</option>
              {point96List.map(p => <option key={p.id} value={p.id}>{p.id} - {p.file_name}</option>)}
            </select>
          </div>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">转换</button>
        </form>

        <form onSubmit={handlePeakValleyTo24h} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">峰平谷转24小时</h2>
          <div className="grid grid-cols-2 gap-3">
            <select value={templateId} onChange={e => setTemplateId(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">曲线模板</option>
              {templates.map(t => <option key={t.id} value={t.id}>{t.template_name}</option>)}
            </select>
            <select value={String(isPeakMonth)} onChange={e => setIsPeakMonth(e.target.value === 'true')} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="true">夏季/冬季峰</option>
              <option value="false">其他</option>
            </select>
            <input type="number" step="0.01" placeholder="峰电量" value={peak} onChange={e => setPeak(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="number" step="0.01" placeholder="尖电量" value={high} onChange={e => setHigh(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="number" step="0.01" placeholder="平电量" value={normal} onChange={e => setNormal(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
            <input type="number" step="0.01" placeholder="谷电量" value={valley} onChange={e => setValley(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">转换</button>
        </form>

        <form onSubmit={handleFillMissing} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">缺失数据补全</h2>
          <div className="flex gap-3">
            <select required value={fillCustomerId} onChange={e => setFillCustomerId(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">客户</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
            </select>
            <input required type="month" value={fillMonth} onChange={e => setFillMonth(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">补全</button>
        </form>

        <form onSubmit={handleCopyData} className="p-4 rounded-lg border border-border bg-background-secondary space-y-3">
          <h2 className="text-sm font-semibold text-foreground">复制用电数据</h2>
          <div className="grid grid-cols-3 gap-3">
            <select required value={copySourceId} onChange={e => setCopySourceId(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">源客户</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
            </select>
            <select required value={copyTargetId} onChange={e => setCopyTargetId(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground">
              <option value="">目标客户</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.customer_name}</option>)}
            </select>
            <input required type="month" value={copyMonth} onChange={e => setCopyMonth(e.target.value)} className="px-3 py-1.5 rounded-md bg-background border border-border text-sm text-foreground" />
          </div>
          <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">复制</button>
        </form>
      </div>
    </div>
  );
}
