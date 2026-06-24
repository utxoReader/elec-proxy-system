import { useEffect, useState } from 'react';
import { dashboardApi } from '@/shared/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';

export default function DashboardPage() {
  const [inquiryStats, setInquiryStats] = useState<Record<string, unknown>>({});
  const [agentFeeStats, setAgentFeeStats] = useState<Record<string, unknown>>({});
  const [profitSummary, setProfitSummary] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);

  const currentMonth = new Date().toISOString().slice(0, 7);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [iRes, aRes, pRes] = await Promise.all([
          dashboardApi.inquiryStatistics(),
          dashboardApi.agentFeeStatistics(),
          dashboardApi.profitSummary(currentMonth),
        ]);
        setInquiryStats((iRes as unknown as { data: Record<string, unknown> }).data || {});
        setAgentFeeStats((aRes as unknown as { data: Record<string, unknown> }).data || {});
        setProfitSummary((pRes as unknown as { data: Record<string, unknown> }).data || {});
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const formatNum = (v: unknown) => {
    const n = Number(v);
    return Number.isFinite(n) ? n.toFixed(2) : '-';
  };

  const inquiryChartData = Object.entries(inquiryStats).map(([k, v]) => ({ name: k, value: Number(v) || 0 }));
  const profitChartData = [
    { name: '总用电量', value: Number(profitSummary.total_consumption) || 0 },
    { name: '总利润', value: Number(profitSummary.total_profit) || 0 },
    { name: '调平后利润', value: Number(profitSummary.adjusted_total_profit) || 0 },
  ];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">首页看板</h1>

      {loading ? (
        <div className="text-foreground-muted">加载中...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg border border-border bg-background-secondary">
              <div className="text-sm text-foreground-secondary">询价总数</div>
              <div className="text-2xl font-bold text-foreground mt-1">{formatNum(inquiryStats.total)}</div>
            </div>
            <div className="p-4 rounded-lg border border-border bg-background-secondary">
              <div className="text-sm text-foreground-secondary">待处理询价</div>
              <div className="text-2xl font-bold text-warning mt-1">{formatNum(inquiryStats.pending)}</div>
            </div>
            <div className="p-4 rounded-lg border border-border bg-background-secondary">
              <div className="text-sm text-foreground-secondary">分润金额</div>
              <div className="text-2xl font-bold text-accent mt-1">{formatNum(agentFeeStats.total_commission)}</div>
            </div>
            <div className="p-4 rounded-lg border border-border bg-background-secondary">
              <div className="text-sm text-foreground-secondary">{currentMonth} 总利润</div>
              <div className="text-2xl font-bold text-success mt-1">{formatNum(profitSummary.total_profit)}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg border border-border bg-background-secondary">
              <h2 className="text-sm font-semibold text-foreground mb-4">询价状态分布</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={inquiryChartData.length > 0 ? inquiryChartData : [{ name: '无', value: 0 }]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="var(--accent-primary)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="p-4 rounded-lg border border-border bg-background-secondary">
              <h2 className="text-sm font-semibold text-foreground mb-4">{currentMonth} 利润概览</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={profitChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="var(--accent-primary)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
