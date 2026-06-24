import { priceApi } from '@/shared/api';
import PriceTable from './PriceTable';

export default function WholesalePricePage() {
  return (
    <PriceTable
      title="批发价"
      fetchFn={priceApi.wholesalePricePage}
      columns={[
        { key: 'price_date', label: '日期' },
        { key: 'hour_index', label: '时段', align: 'right' },
        { key: 'time_period', label: '时段类型' },
        { key: 'wholesale_price', label: '批发价(元/度)', align: 'right' },
        { key: 'status', label: '状态' },
      ]}
    />
  );
}
