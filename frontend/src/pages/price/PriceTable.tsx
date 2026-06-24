import { useEffect, useState } from 'react';

interface PriceTableProps {
  title: string;
  fetchFn: (params: Record<string, unknown>) => Promise<unknown>;
  columns: { key: string; label: string; align?: 'right' }[];
  filterBar?: React.ReactNode;
}

export default function PriceTable({ title, fetchFn, columns, filterBar }: PriceTableProps) {
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetchFn({ page, page_size: pageSize });
      const result = res as unknown as { data: { items: Record<string, unknown>[]; total: number } };
      setData(result.data?.items || []);
      setTotal(result.data?.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">{title}</h1>
      </div>

      {filterBar && <div className="flex gap-3 items-center">{filterBar}</div>}

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="data-table">
          <thead className="bg-background-secondary">
            <tr>
              {columns.map(col => (
                <th key={col.key} className={col.align === 'right' ? 'text-right' : ''}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={columns.length} className="text-center py-8 text-foreground-muted">加载中...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={columns.length} className="text-center py-8 text-foreground-muted">暂无数据</td></tr>
            ) : data.map((item, i) => (
              <tr key={item.id as string || i} className="hover:bg-background-hover">
                {columns.map(col => (
                  <td key={col.key} className={col.align === 'right' ? 'text-right font-mono-num' : ''}>
                    {String(item[col.key] ?? '-')}
                  </td>
                ))}
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
