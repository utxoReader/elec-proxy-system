import { useState } from 'react';
import { profitApi } from '@/shared/api';

export default function ProfitSummary() {
  const [month, setMonth] = useState('');
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSummary = async () => {
    if (!month) return;
    setLoading(true);
    try {
      const res = await profitApi.monthlyProfitSummary(month);
      const result = res as unknown as { data: Record<string, unknown> };
      setSummary(result.data);
    } finally {
      setLoading(false);
    }
  };

  const summaryCards = summary ? [
    { label: '客户数', value: `${summary.customer_count}`, color: '' },
    { label: '总用电量', value: `${Number(summary.total_consumption || 0).toFixed(2)} kWh`, color: '' },
    { label: '总零售电费', value: `${Number(summary.total_retail_fee || 0).toFixed(2)} 元`, color: '' },
    { label: '总利润', value: `${Number(summary.total_profit || 0).toFixed(2)} 元`, color: 'text-success' },
    { label: '公司利润', value: `${Number(summary.company_profit || 0).toFixed(2)} 元`, color: '' },
    { label: '代理商利润', value: `${Number(summary.agent_profit || 0).toFixed(2)} 元`, color: '' },
  ] : [];

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">利润统计</h1>

      <div className="flex gap-3 items-center">
        <input
          type="month"
          value={month}
          onChange={e => setMonth(e.target.value)}
          className="px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground"
        />
        <button onClick={fetchSummary} disabled={loading || !month} className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover disabled:opacity-50">
          {loading ? '加载中...' : '查询'}
        </button>
      </div>

      {summary && (
        <div className="grid grid-cols-3 gap-4">
          {summaryCards.map(card => (
            <div key={card.label} className="rounded-lg border border-border bg-background-secondary p-4">
              <div className="text-sm text-foreground-secondary">{card.label}</div>
              <div className={`text-xl font-bold font-mono-num mt-1 ${card.color}`}>{card.value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
