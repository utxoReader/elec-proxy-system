import { priceApi } from '@/shared/api';
import PriceTable from './PriceTable';

export default function GridPricePage() {
  return (
    <PriceTable
      title="电网电价"
      fetchFn={priceApi.gridPricePage}
      columns={[
        { key: 'year_month', label: '年月' },
        { key: 'time_period', label: '时段' },
        { key: 'base_price', label: '基准价(元/度)', align: 'right' },
        { key: 'price', label: '价格(元/度)', align: 'right' },
        { key: 'status', label: '状态' },
      ]}
    />
  );
}
