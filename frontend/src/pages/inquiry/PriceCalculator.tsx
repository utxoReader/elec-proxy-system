import { useState } from 'react';
import { inquiryApi } from '@/shared/api';
import type { PackageType } from '@/shared/types';

export default function PriceCalculator() {
  const [form, setForm] = useState({
    package_type: 'flat_rate' as PackageType,
    estimated_monthly_consumption: '',
    price_difference: '',
    base_price: '',
    grid_price: '',
    transmission_fee: '',
    distribution_fee: '',
    government_fund: '',
    other_fee: '',
  });
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await inquiryApi.calculatePrice({
        package_type: form.package_type,
        estimated_monthly_consumption: Number(form.estimated_monthly_consumption),
        price_difference: Number(form.price_difference),
        base_price: form.base_price ? Number(form.base_price) : undefined,
        grid_price: form.grid_price ? Number(form.grid_price) : undefined,
        transmission_fee: form.transmission_fee ? Number(form.transmission_fee) : undefined,
        distribution_fee: form.distribution_fee ? Number(form.distribution_fee) : undefined,
        government_fund: form.government_fund ? Number(form.government_fund) : undefined,
        other_fee: form.other_fee ? Number(form.other_fee) : undefined,
      });
      setResult((res as unknown as { data: Record<string, unknown> }).data || null);
    } catch (err) {
      alert(err instanceof Error ? err.message : '计算失败');
    }
  };

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <h1 className="text-xl font-bold text-foreground">价格测算</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">套餐类型</label>
            <select value={form.package_type} onChange={e => setForm({ ...form, package_type: e.target.value as PackageType })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground">
              <option value="flat_rate">固定电价</option>
              <option value="time_of_use">分时电价</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">预估用电量</label>
            <input required type="number" step="0.01" value={form.estimated_monthly_consumption} onChange={e => setForm({ ...form, estimated_monthly_consumption: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">价差</label>
            <input required type="number" step="0.0001" value={form.price_difference} onChange={e => setForm({ ...form, price_difference: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">基础电价</label>
            <input type="number" step="0.0001" value={form.base_price} onChange={e => setForm({ ...form, base_price: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">电网电价</label>
            <input type="number" step="0.0001" value={form.grid_price} onChange={e => setForm({ ...form, grid_price: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">输配电费</label>
            <input type="number" step="0.0001" value={form.transmission_fee} onChange={e => setForm({ ...form, transmission_fee: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">配电费</label>
            <input type="number" step="0.0001" value={form.distribution_fee} onChange={e => setForm({ ...form, distribution_fee: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">政府性基金</label>
            <input type="number" step="0.0001" value={form.government_fund} onChange={e => setForm({ ...form, government_fund: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
          <div>
            <label className="block text-sm text-foreground-secondary mb-1">其他费用</label>
            <input type="number" step="0.0001" value={form.other_fee} onChange={e => setForm({ ...form, other_fee: e.target.value })} className="w-full px-3 py-1.5 rounded-md bg-background-secondary border border-border text-sm text-foreground" />
          </div>
        </div>
        <button type="submit" className="px-4 py-1.5 rounded-md bg-accent text-white text-sm hover:bg-accent-hover">计算</button>
      </form>

      {result && (
        <div className="p-4 rounded-lg border border-border bg-background-secondary space-y-2 text-sm">
          <h2 className="font-semibold text-foreground">测算结果</h2>
          {Object.entries(result).map(([k, v]) => (
            <div key={k} className="flex justify-between border-b border-border last:border-0 py-1">
              <span className="text-foreground-secondary">{k}</span>
              <span className="font-mono-num">{typeof v === 'number' ? v.toFixed(4) : String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
