import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@/shared/useTheme';
import { AuthProvider, useAuth } from '@/shared/auth/useAuth';
import { MainLayout } from '@/shared/MainLayout';
import { AuthPage } from '@/components/auth/AuthPage';

// Profit pages
import ProfitLayout from '@/pages/profit/ProfitLayout';
import MonthlyProfitList from '@/pages/profit/MonthlyProfitList';
import ProfitSummary from '@/pages/profit/ProfitSummary';

// Commission pages
import CommissionLayout from '@/pages/commission/CommissionLayout';
import CommissionConfig from '@/pages/commission/CommissionConfig';
import AgentFeeList from '@/pages/commission/AgentFeeList';

// Agent pages
import AgentList from '@/pages/agent/AgentList';

// Price pages
import PriceLayout from '@/pages/price/PriceLayout';
import BasePricePage from '@/pages/price/BasePricePage';
import GridPricePage from '@/pages/price/GridPricePage';
import WholesalePricePage from '@/pages/price/WholesalePricePage';
import MarketAllocationPricePage from '@/pages/price/MarketAllocationPricePage';
import OtherFeePage from '@/pages/price/OtherFeePage';

// Customer pages
import CustomerLayout from '@/pages/customer/CustomerLayout';
import CustomerList from '@/pages/customer/CustomerList';
import CustomerPriceChange from '@/pages/customer/CustomerPriceChange';
import CustomerContract from '@/pages/customer/CustomerContract';

// Consumption pages
import ConsumptionLayout from '@/pages/consumption/ConsumptionLayout';
import DailyConsumptionPage from '@/pages/consumption/DailyConsumptionPage';
import HourlyConsumptionPage from '@/pages/consumption/HourlyConsumptionPage';
import Point96Page from '@/pages/consumption/Point96Page';
import ConversionPage from '@/pages/consumption/ConversionPage';
import UsageCurveTemplatePage from '@/pages/consumption/UsageCurveTemplatePage';
import ImportTaskPage from '@/pages/consumption/ImportTaskPage';

// Inquiry pages
import InquiryLayout from '@/pages/inquiry/InquiryLayout';
import InquiryList from '@/pages/inquiry/InquiryList';
import InquiryDetail from '@/pages/inquiry/InquiryDetail';
import InquiryCreate from '@/pages/inquiry/InquiryCreate';
import PriceCalculator from '@/pages/inquiry/PriceCalculator';

// Dashboard
import DashboardPage from '@/pages/dashboard/DashboardPage';

function AuthGate() {
  const { isHydrated, isLoggedIn } = useAuth();

  if (!isHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-accent" />
          <span className="text-sm text-foreground-secondary">加载中…</span>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return <AuthPage />;
  }

  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />

        {/* Agents */}
        <Route path="agents" element={<AgentList />} />

        {/* Customers with tabs */}
        <Route path="customers" element={<CustomerLayout />}>
          <Route index element={<Navigate to="/customers/list" replace />} />
          <Route path="list" element={<CustomerList />} />
          <Route path="price-change" element={<CustomerPriceChange />} />
          <Route path="contract" element={<CustomerContract />} />
        </Route>

        {/* Prices with tabs */}
        <Route path="prices" element={<PriceLayout />}>
          <Route index element={<Navigate to="/prices/base" replace />} />
          <Route path="base" element={<BasePricePage />} />
          <Route path="grid" element={<GridPricePage />} />
          <Route path="wholesale" element={<WholesalePricePage />} />
          <Route path="allocation" element={<MarketAllocationPricePage />} />
          <Route path="other" element={<OtherFeePage />} />
        </Route>

        {/* Consumption with tabs */}
        <Route path="consumption" element={<ConsumptionLayout />}>
          <Route index element={<Navigate to="/consumption/daily" replace />} />
          <Route path="daily" element={<DailyConsumptionPage />} />
          <Route path="hourly" element={<HourlyConsumptionPage />} />
          <Route path="point96" element={<Point96Page />} />
          <Route path="conversion" element={<ConversionPage />} />
          <Route path="template" element={<UsageCurveTemplatePage />} />
          <Route path="import-task" element={<ImportTaskPage />} />
        </Route>

        {/* Inquiry routes */}
        <Route path="inquiries" element={<InquiryLayout />}>
          <Route index element={<InquiryList />} />
          <Route path="create" element={<InquiryCreate />} />
          <Route path="calculator" element={<PriceCalculator />} />
          <Route path=":id" element={<InquiryDetail />} />
        </Route>

        {/* Profits with tabs */}
        <Route path="profits" element={<ProfitLayout />}>
          <Route index element={<Navigate to="/profits/monthly" replace />} />
          <Route path="monthly" element={<MonthlyProfitList />} />
          <Route path="summary" element={<ProfitSummary />} />
        </Route>

        {/* Commissions with tabs */}
        <Route path="commissions" element={<CommissionLayout />}>
          <Route index element={<Navigate to="/commissions/config" replace />} />
          <Route path="config" element={<CommissionConfig />} />
          <Route path="fees" element={<AgentFeeList />} />
          <Route path="approval" element={<div className="p-6"><h1 className="text-xl font-bold">审批管理</h1></div>} />
        </Route>
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AuthGate />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
