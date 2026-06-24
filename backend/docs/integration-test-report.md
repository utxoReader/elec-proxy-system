# 桐叶售电代理系统 — 端到端集成测试报告

## 1. 测试范围

本次端到端集成测试覆盖 桐叶售电代理系统 后端核心业务链路，验证以下模块在 SQLite 测试环境及 PostgreSQL 生产/预发环境中的协同工作能力：

- 代理商管理（Agent）
- 客户账户生命周期（CustomerAccount）
- 价差/合同变更生效（Price Effective Job）
- 电价数据管理（Base / Grid / Wholesale / MarketAllocation）
- 用电量数据采集（Daily / Hourly / Point96）
- 日电润/月利润计算（Profit）
- 代理费结算（Commission / AgentFee）
- 询价报价流程（Inquiry）
- 定时任务（Contract Expiry Reminder）

## 2. 测试环境

| 环境 | 数据库 | 用途 |
|---|---|---|
| 开发/CI | SQLite `:memory:` | `pytest` 自动化集成测试 |
| 生产/预发 | PostgreSQL 14+ | `scripts/integration_test.py` 迁移后验证 |

后端技术栈：

- Python 3.12
- FastAPI + Pydantic v2
- SQLAlchemy 2.x（同步）
- pytest

## 3. 测试数据准备

### 3.1 SQLite 测试环境（`tests/test_integration.py`）

由 `tests/conftest.py` 在每次测试用例开始时创建全新的内存数据库并初始化所有表结构。测试函数内部按以下顺序创建业务数据：

1. 代理商 `Integration Agent`
2. 当月分润配置（代理商 50%，上级 5%，公司 45%）
3. 基础电价、电网电价、批发电价、市场分摊电价
4. 用电曲线模板（24 小时均分）
5. 客户账户、待生效价差历史记录
6. 日用电量、96 点用电量、小时用电量
7. 询价单

### 3.2 PostgreSQL 迁移后环境（`scripts/integration_test.py`）

脚本读取 `DATABASE_URL`（默认来自 `.env`）连接已迁移的 PostgreSQL 数据库，直接检查真实数据量。若选中日期缺少必要电价数据，脚本会自动创建 sample 价格记录以保证利润计算可执行。

## 4. 测试用例

### TC-01 基础数据创建

- 创建代理商并校验返回 ID
- 创建分润配置并校验生效月份
- 创建基础电价、电网电价、批发电价、市场分摊电价并校验字段
- 创建用电曲线模板并校验 ID

### TC-02 客户生命周期

- 创建客户账户，初始状态为 `待签约（2）`
- 调用 `update_customer_status` 将状态改为 `已签约（3）`
- 创建待生效价差历史记录（生效日期 = 明天）
- 执行 `run_price_effective_job(target_date=明天)`
- 校验客户 `price_difference` 已更新为新价差

### TC-03 用电量数据

- 创建日用电量记录，包含 24 小时曲线及峰/高/平/谷合计
- 创建 96 点用电量数据并调用 `convert_to_daily` 转为 24 小时曲线
- 创建 24 条小时用电量记录

### TC-04 利润计算

- 调用 `calculate_daily_profit(customer_id, profit_date)`
- 校验 `CustomerDailyProfit` 记录生成且总利润非空
- 调用 `generate_monthly_profit(customer_id, profit_month)`
- 校验 `CustomerMonthlyProfit` 记录生成且汇总值正确

### TC-05 代理费结算

- 调用 `generate_agent_fee_from_monthly_profit(monthly_profit_id)`
- 校验 `AgentFee` 记录生成，结算状态为 `待结算（1）`
- 调用 `approve_agent_fee(..., approve_status=2)` 审批通过
- 调用 `settle_agent_fee(...)` 完成结算
- 校验状态变为 `已结算（2）` 且结算日期非空

### TC-06 询价流程

- 调用 `create_inquiry` 创建询价单，状态为 `待处理（1）`
- 调用 `quote_inquiry` 提交报价，状态变为 `已报价（2）`
- 调用 `accept_inquiry` 接受报价，状态变为 `已接受（3）`
- 调用 `cooperate_inquiry` 转为合作，状态变为 `已合作（6）`

### TC-07 定时任务

- 创建合同 5 天后到期的客户
- 执行 `run_contract_expiry_reminder(days_before=7)`
- 校验提醒列表包含该客户

## 5. 预期结果

| 步骤 | 预期结果 |
|---|---|
| 基础数据创建 | 所有记录成功插入并返回有效 ID |
| 客户状态变更 | `customer_status` 变为 3（已签约） |
| 价差生效 | `run_price_effective_job` 返回 `applied_count=1`，客户 `price_difference` 更新 |
| 用电量 | 日用电量 24 小时字段齐全；96 点转 24 小时聚合正确；小时记录 24 条 |
| 日利润 | `CustomerDailyProfit` 记录存在，总用电量 = 1000 kWh，利润字段非空 |
| 月利润 | `CustomerMonthlyProfit` 汇总日利润，数据完整率 > 0 |
| 代理费 | `AgentFee` 生成，审批后 `approval_status=2`，结算后 `settlement_status=2` |
| 询价 | 状态依次变化：`1 -> 2 -> 3 -> 6` |
| 到期提醒 | 提醒数量 ≥ 1，且包含即将到期客户 |

## 6. 如何运行测试

### 6.1 运行 SQLite 集成测试

```bash
cd /Users/wo/ProjectCat/projects/售电/桐叶/elec-proxy-system/backend
source .venv/bin/activate
pytest tests/test_integration.py -v
```

### 6.2 运行全部测试

```bash
pytest -v
```

### 6.3 运行 PostgreSQL 迁移后集成脚本

```bash
cd /Users/wo/ProjectCat/projects/售电/桐叶/elec-proxy-system/backend
source .venv/bin/activate
export DATABASE_URL="postgresql+psycopg2://tongye:tongye@localhost:5432/tongye"
python scripts/integration_test.py
```

脚本退出码：

- `0`：所有检查及流程均通过
- `1`：存在检查失败或异常

## 7. 测试文件清单

| 文件 | 说明 |
|---|---|
| `tests/test_integration.py` | pytest 端到端集成测试 |
| `scripts/integration_test.py` | PostgreSQL 迁移后独立验证脚本 |
| `docs/integration-test-report.md` | 本报告 |
