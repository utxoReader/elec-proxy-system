/** API endpoint helpers for elec modules. */

import { api } from '@/api/client';
import type { PageResult } from '@/shared/types';

// ========== Profit API ==========

export const profitApi = {
  /** List hourly profit details for a day */
  dailyHourlyDetail: (customerId: number, profitDate: string) =>
    api.get('/elec/customer-hourly-profit/daily-detail', { customer_id: customerId, profit_date: profitDate }),

  /** List hourly profit details for a month */
  monthlyHourlyDetail: (customerId: number, profitMonth: string) =>
    api.get('/elec/customer-hourly-profit/monthly-detail', { customer_id: customerId, profit_month: profitMonth }),

  /** Time period summary (peak/flat/valley) */
  timePeriodSummary: (customerId: number, profitMonth: string) =>
    api.get('/elec/customer-hourly-profit/time-period-summary', { customer_id: customerId, profit_month: profitMonth }),

  /** Page query daily profits */
  dailyProfitPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/customer-daily-profit/page', params),

  /** Calculate daily profit from consumption data */
  calculateDailyProfit: (customerAccountId: number, date: string) =>
    api.post('/elec/customer-daily-profit/calculate-from-daily-data', { customer_account_id: customerAccountId, date }),

  /** Page query monthly profits */
  monthlyProfitPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/customer-monthly-profit/page', params),

  /** Get monthly profit summary */
  monthlyProfitSummary: (profitMonth: string, agentId?: number) =>
    api.get('/elec/customer-monthly-profit/summary', { profit_month: profitMonth, agent_id: agentId }),

  /** Generate monthly profit from daily data */
  generateMonthlyProfit: (customerId: number, profitMonth: string) =>
    api.post('/elec/customer-monthly-profit/generate-from-daily-data', { customer_id: customerId, profit_month: profitMonth }),

  /** Adjust monthly profit */
  adjustMonthlyProfit: (id: number, adjustmentConsumption: number, remark?: string) =>
    api.post('/elec/customer-monthly-profit/adjust', { id, adjustment_consumption: adjustmentConsumption, adjustment_remark: remark }),

  /** Confirm monthly profit */
  confirmMonthlyProfit: (ids: number[], remark?: string) =>
    api.post('/elec/customer-monthly-profit/confirm', { ids, confirm_remark: remark }),

  /** Settle monthly profit */
  settleMonthlyProfit: (id: number, remark?: string) =>
    api.post('/elec/customer-monthly-profit/settle', { id, settlement_remark: remark }),
};

// ========== Commission API ==========

export const commissionApi = {
  /** List commission configs */
  configPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/commission-config/page', params),

  /** Get current effective config */
  currentConfig: () =>
    api.get('/elec/commission-config/current'),

  /** Create commission config */
  createConfig: (data: Record<string, unknown>) =>
    api.post('/elec/commission-config/create', data),

  /** Validate effective month */
  validateMonth: (effectiveMonth: string, excludeId?: number) =>
    api.get('/elec/commission-config/validate-effective-month', { effective_month: effectiveMonth, exclude_id: excludeId }),

  /** Preview commission */
  previewCommission: (totalProfit: number) =>
    api.get('/elec/commission-config/preview-commission', { total_profit: totalProfit }),

  /** List agent fees */
  agentFeePage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/agent-fee/page', params),

  /** Get agent fee statistics */
  agentFeeStatistics: (agentId?: number) =>
    api.get('/elec/agent-fee/statistics', { agent_id: agentId }),

  /** Approve agent fee */
  approveAgentFee: (id: number, approveStatus: number, remark?: string) =>
    api.post('/elec/agent-fee/approve', { id, approve_status: approveStatus, approve_remark: remark }),

  /** Batch approve agent fees */
  batchApprove: (ids: number[], approveStatus: number, remark?: string) =>
    api.post('/elec/agent-fee/batch-approve', { ids, approve_status: approveStatus, approve_remark: remark }),

  /** Settle agent fee */
  settleAgentFee: (id: number, remark?: string) =>
    api.post('/elec/agent-fee/settle', { id, settlement_remark: remark }),

  /** Batch settle agent fees */
  batchSettle: (ids: number[], remark?: string) =>
    api.post('/elec/agent-fee/batch-settle', { ids, settlement_remark: remark }),
};

// ========== Agent API ==========

export const agentApi = {
  page: (params: Record<string, unknown>) =>
    api.get('/elec/agent/page', params),
  list: () =>
    api.get('/elec/agent/list'),
  tree: () =>
    api.get('/elec/agent/tree'),
  get: (id: number) =>
    api.get('/elec/agent/get', { id }),
  create: (data: Record<string, unknown>) =>
    api.post('/elec/agent/create', data),
  update: (data: Record<string, unknown>) =>
    api.put('/elec/agent/update', data),
  delete: (id: number) =>
    api.delete('/elec/agent/delete', { id }),
  updateStatus: (id: number, status: number) =>
    api.put('/elec/agent/update-status', { id, status }),
};

// ========== Price API ==========

export const priceApi = {
  basePricePage: (params: Record<string, unknown>) =>
    api.get('/elec/base-price/page', params),
  gridPricePage: (params: Record<string, unknown>) =>
    api.get('/elec/grid-price/page', params),
  wholesalePricePage: (params: Record<string, unknown>) =>
    api.get('/elec/wholesale-price/page', params),
  marketAllocationPage: (params: Record<string, unknown>) =>
    api.get('/elec/market-allocation/page', params),
  otherFeePage: (params: Record<string, unknown>) =>
    api.get('/elec/other-fee/page', params),
};

// ========== Customer API ==========

export const customerApi = {
  page: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/customer-account/page', params),
  get: (id: number) =>
    api.get('/elec/customer-account/get', { id }),
  simpleList: () =>
    api.get('/elec/customer-account/simple-list'),
  create: (data: Record<string, unknown>) =>
    api.post('/elec/customer-account/create', data),
  update: (data: Record<string, unknown>) =>
    api.put('/elec/customer-account/update', data),
  delete: (id: number) =>
    api.delete('/elec/customer-account/delete', { id }),
  updateStatus: (id: number, customerStatus: number) =>
    api.put('/elec/customer-account/update-status', { id, customer_status: customerStatus }),
  signContract: (id: number, data: Record<string, unknown>) =>
    api.put('/elec/customer-account/sign-contract', { id, ...data }),
  terminateContract: (id: number, reason: string, terminateDate: string) =>
    api.put('/elec/customer-account/terminate-contract', { id, reason, terminate_date: terminateDate }),
  updatePriceAndContract: (data: Record<string, unknown>) =>
    api.put('/elec/customer-account/update-price-and-contract', data),
  priceHistoryPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/customer-account/price-history/page', params),
};

// ========== Consumption API ==========

export const consumptionApi = {
  dailyPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/daily-consumption/page', params),
  dailyGet: (id: number) =>
    api.get(`/elec/daily-consumption/get/${id}`),
  dailyCreate: (data: Record<string, unknown>) =>
    api.post('/elec/daily-consumption/create', data),
  dailyUpdate: (data: Record<string, unknown>) =>
    api.put('/elec/daily-consumption/update', data),
  dailyDelete: (id: number) =>
    api.delete(`/elec/daily-consumption/delete/${id}`),
  dailyBatchCreate: (data: Record<string, unknown>[]) =>
    api.post('/elec/daily-consumption/batch-create', data),
  dailyStatistics: (customerAccountId?: number, dataMonth?: string) =>
    api.get('/elec/daily-consumption/statistics', { customer_account_id: customerAccountId, data_month: dataMonth }),
  hourlyPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/hourly-consumption/page', params),
  point96Page: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/point96/page', params),
  point96Import: (formData: FormData) =>
    fetch('/api/elec/point96/import', { method: 'POST', body: formData }),
  point96ConvertToDaily: (id: number) =>
    api.post(`/elec/point96/convert-to-daily/${id}`),
  conversionPoint96To24h: (point96Id: number) =>
    api.post('/elec/conversion/point96-to-24h', { point96_id: point96Id }),
  conversionPeakValleyTo24h: (data: Record<string, unknown>) =>
    api.post('/elec/conversion/peak-valley-to-24h', data),
  conversionFillMissing: (customerAccountId: number, month: string) =>
    api.post('/elec/conversion/fill-missing', { customer_account_id: customerAccountId, month }),
  conversionCopyData: (sourceCustomerId: number, targetCustomerId: number, month: string) =>
    api.post('/elec/conversion/copy-data', { source_customer_id: sourceCustomerId, target_customer_id: targetCustomerId, month }),
  usageCurveTemplatePage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/usage-curve-template/page', params),
  importTaskPage: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/import-task/page', params),
};

// ========== Inquiry API ==========

export const inquiryApi = {
  page: (params: Record<string, unknown>) =>
    api.get<PageResult<Record<string, unknown>>>('/elec/inquiry/page', params),
  get: (id: number) =>
    api.get(`/elec/inquiry/get/${id}`),
  create: (data: Record<string, unknown>) =>
    api.post('/elec/inquiry/create', data),
  update: (data: Record<string, unknown>) =>
    api.put('/elec/inquiry/update', data),
  delete: (id: number) =>
    api.delete(`/elec/inquiry/delete/${id}`),
  quote: (id: number, data: Record<string, unknown>) =>
    api.post(`/elec/inquiry/${id}/quote`, data),
  accept: (id: number) =>
    api.post(`/elec/inquiry/${id}/accept`),
  reject: (id: number, rejectReason: string) =>
    api.post(`/elec/inquiry/${id}/reject`, { reject_reason: rejectReason }),
  cooperate: (id: number, data: Record<string, unknown>) =>
    api.post(`/elec/inquiry/${id}/cooperate`, data),
  terminate: (id: number, terminateDate: string) =>
    api.post(`/elec/inquiry/${id}/terminate`, { terminate_date: terminateDate }),
  statistics: () =>
    api.get('/elec/inquiry/statistics'),
  export: () =>
    '/api/elec/inquiry/export',
  calculatePrice: (data: Record<string, unknown>) =>
    api.post('/elec/inquiry/calculate-price', data),
  uploadConsumptionData: (id: number, formData: FormData) =>
    fetch(`/api/elec/inquiry/${id}/upload-consumption-data`, { method: 'POST', body: formData }),
  consumptionData: (id: number) =>
    api.get(`/elec/inquiry/${id}/consumption-data`),
};

// ========== Dashboard API ==========

export const dashboardApi = {
  inquiryStatistics: () =>
    inquiryApi.statistics(),
  agentFeeStatistics: () =>
    commissionApi.agentFeeStatistics(),
  profitSummary: (profitMonth: string) =>
    profitApi.monthlyProfitSummary(profitMonth),
};
