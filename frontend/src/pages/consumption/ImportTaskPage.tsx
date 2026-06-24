import { useEffect, useState } from 'react';
import { consumptionApi } from '@/shared/api';
import type { PageResult } from '@/shared/types';

interface ImportTask {
  id: number;
  task_type: string;
  file_name: string;
  status: string;
  total_count: number;
  success_count: number;
  fail_count: number;
  remark: string;
  created_at: string;
}

export default function ImportTaskPage() {
  const [data, setData] = useState<ImportTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await consumptionApi.importTaskPage({ page, page_size: pageSize });
      const result = res as unknown as { data: PageResult<ImportTask> };
      setData(result.data.items || []);
      setTotal(result.data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page]);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-foreground">导入任务</h1>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              <th>任务类型</th>
              <th>文件名</th>
              <th>状态</th>
              <th className="text-right">总数</th>
              <th className="text-right">成功</th>
              <th className="text-right">失败</th>
              <th>备注</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map(item => (
              <tr key={item.id} className="hover:bg-background-hover">
                <td className="font-medium">{item.task_type}</td>
                <td>{item.file_name || '-'}</td>
                <td>
                  <span className={`px-2 py-0.5 rounded text-xs ${item.status === 'success' ? 'bg-success/10 text-success' : item.status === 'failed' ? 'bg-danger/10 text-danger' : 'bg-warning/10 text-warning'}`}>
                    {item.status || '-'}
                  </span>
                </td>
                <td className="text-right font-mono-num">{item.total_count ?? '-'}</td>
                <td className="text-right font-mono-num">{item.success_count ?? '-'}</td>
                <td className="text-right font-mono-num">{item.fail_count ?? '-'}</td>
                <td>{item.remark || '-'}</td>
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
