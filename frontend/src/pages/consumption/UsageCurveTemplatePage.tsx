import { useEffect, useState } from 'react';
import { consumptionApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface UsageCurveTemplate {
  id: number;
  template_name: string;
  description: string;
  is_peak_month: boolean;
  created_at: string;
}

export default function UsageCurveTemplatePage() {
  const [data, setData] = useState<UsageCurveTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await consumptionApi.usageCurveTemplatePage({ page, page_size: pageSize });
      const result = res as unknown as { data: PageResult<UsageCurveTemplate> };
      setData(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page]);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">曲线模板</h1>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>模板名称</th>
              <th>描述</th>
              <th>是否峰月</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={4} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.template_name}</td>
                <td>{item.description || '-'}</td>
                <td>{item.is_peak_month ? '是' : '否'}</td>
                <td>{item.created_at || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center text-sm text-foreground-secondary">
        <span>共 {total} 条</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded border border-border disabled:opacity-40">上一页</button>
          <span className="px-3 py-1">第 {page} 页</span>
          <button disabled={page * pageSize >= total} onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded border border-border disabled:opacity-40">下一页</button>
        </div>
      </div>
    </div>
  );
}
