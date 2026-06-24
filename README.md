# 桐叶售电代理系统

售电代理业务管理系统，支持代理商管理、客户管理、电价配置、用电数据、询价报价、利润计算、分润结算等核心业务功能。

## 技术栈

| 层 | 技术选型 |
|---|---|
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.x + Pydantic v2 |
| 数据库 | PostgreSQL 16（Alembic 迁移） |
| 多租户 | PostgreSQL RLS + `app.current_region` 会话变量 |
| 前端 | React 19 + TypeScript + Vite 6 + TailwindCSS v4 + HeroUI v3 |
| 移动端 | uni-app（已适配新 API） |

## 项目结构

```
elec-proxy-system/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py            # 应用入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── db_region_guard.py # RLS 区域隔离
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑层
│   │   ├── routers/           # FastAPI 路由
│   │   └── core/              # 核心工具/常量
│   ├── alembic/               # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React + TypeScript 前端
│   ├── src/
│   │   ├── api/               # API 调用层
│   │   ├── pages/             # 页面组件（按模块分组）
│   │   ├── shared/            # 共享组件/hooks/工具
│   │   └── components/        # 通用组件
│   ├── docker/                # Nginx 配置
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml          # 一键部署编排
├── README.md
└── README.deploy.md            # 部署文档
```

## 快速开始

### 后端
```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 编辑数据库配置
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 认证
所有 API 使用 JWT Bearer Token 认证，在请求头中添加：
```
Authorization: Bearer <token>
```

### 统一响应格式
```json
{
  "success": true,
  "message": "ok",
  "data": {},
  "error": null
}
```
分页响应：
```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 端点到模块映射

| 模块 | 端点前缀 | 数量 |
|---|---|---|
| 健康检查 | `GET /api/health` | 1 |
| 认证 | `/api/auth/*` | 2 |
| 代理管理 | `/api/elec/agent/*` | 7 |
| 客户管理 | `/api/elec/customer-account/*` | 10 |
| 基准电价 | `/api/elec/base-price/*` | 5 |
| 电网电价 | `/api/elec/grid-price/*` | 5 |
| 批发价 | `/api/elec/wholesale-price/*` | 5 |
| 市场分摊价 | `/api/elec/market-allocation/*` | 6 |
| 其他费用 | `/api/elec/other-fee/*` | 6 |
| 日用电数据 | `/api/elec/daily-consumption/*` | 7 |
| 小时用电数据 | `/api/elec/hourly-consumption/*` | 6 |
| 96点数据 | `/api/elec/point96/*` | 7 |
| 数据转换 | `/api/elec/conversion/*` | 4 |
| 用电曲线模板 | `/api/elec/usage-curve-template/*` | 5 |
| 导入任务 | `/api/elec/import-task/*` | 2 |
| 询价报价 | `/api/elec/inquiry/*` | 12 |
| 小时利润 | `/api/elec/customer-hourly-profit/*` | 4 |
| 日利润 | `/api/elec/customer-daily-profit/*` | 5 |
| 月利润 | `/api/elec/customer-monthly-profit/*` | 8 |
| 分润配置 | `/api/elec/commission-config/*` | 8 |
| 代理费 | `/api/elec/agent-fee/*` | 10 |
| 定时任务 | `/api/elec/jobs/*` | 5 |

### 核心业务端点详情

#### 代理管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/elec/agent/page` | 分页查询代理商 |
| GET | `/api/elec/agent/list` | 全部代理商列表 |
| GET | `/api/elec/agent/tree` | 代理层级树 |
| GET | `/api/elec/agent/get/{id}` | 代理商详情 |
| POST | `/api/elec/agent/create` | 创建代理商 |
| PUT | `/api/elec/agent/update` | 更新代理商 |
| DELETE | `/api/elec/agent/delete/{id}` | 删除代理商 |
| PUT | `/api/elec/agent/update-status` | 启用/禁用 |

#### 客户管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/elec/customer-account/page` | 分页查询客户 |
| GET | `/api/elec/customer-account/get/{id}` | 客户详情 |
| POST | `/api/elec/customer-account/create` | 创建客户 |
| PUT | `/api/elec/customer-account/update` | 更新客户 |
| DELETE | `/api/elec/customer-account/delete/{id}` | 删除客户 |
| PUT | `/api/elec/customer-account/update-status` | 状态变更 |
| PUT | `/api/elec/customer-account/update-price-and-contract` | 价格+合同更新 |
| GET | `/api/elec/customer-account/contracted-customers` | 已签约客户列表 |
| GET | `/api/elec/customer-account/simple-list` | 简化列表 |
| GET | `/api/elec/customer-account/price-history/page` | 价格变更历史 |

#### 电价管理
每个电价表类型支持标准 CRUD：
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/{entity}/page` | 分页查询 |
| GET | `/{entity}/get/{id}` | 详情 |
| POST | `/{entity}/create` | 创建 |
| PUT | `/{entity}/update` | 更新 |
| DELETE | `/{entity}/delete/{id}` | 删除 |

支持的电价类型：`base-price`、`grid-price`、`wholesale-price`、`market-allocation`、`other-fee`

#### 用电数据
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/elec/point96/import` | 导入 96 点 Excel |
| POST | `/api/elec/point96/convert-to-daily/{id}` | 96 点转日用电 |
| POST | `/api/elec/conversion/point96-to-24h` | 96 点转 24 时段 |
| POST | `/api/elec/conversion/peak-valley-to-24h` | 峰谷转 24 时段 |
| POST | `/api/elec/conversion/fill-missing` | 缺失数据补全 |
| POST | `/api/elec/conversion/copy-data` | 跨客户复制数据 |

#### 询价报价
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/elec/inquiry/page` | 分页查询 |
| POST | `/api/elec/inquiry/create` | 创建询价 |
| POST | `/api/elec/inquiry/{id}/quote` | 提交报价 |
| POST | `/api/elec/inquiry/{id}/accept` | 接受报价 |
| POST | `/api/elec/inquiry/{id}/reject` | 拒绝报价 |
| POST | `/api/elec/inquiry/{id}/cooperate` | 确认合作 |
| POST | `/api/elec/inquiry/{id}/terminate` | 终止合作 |
| POST | `/api/elec/inquiry/calculate-price` | 报价测算 |
| GET | `/api/elec/inquiry/statistics` | 统计 |
| GET | `/api/elec/inquiry/export` | 导出 |
| POST | `/api/elec/inquiry/{id}/upload-consumption-data` | 上传用电数据 |
| GET | `/api/elec/inquiry/{id}/consumption-data` | 获取用电数据 |

#### 利润管理（三级）
**小时利润**：按小时粒度查询利润明细、时段汇总
**日利润**：按日查询、从用电量计算
**月利润**：从日利润聚合、调平、确认、结算、汇总统计

#### 分润结算
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/elec/commission-config/page` | 分页查询分润配置 |
| GET | `/api/elec/commission-config/current` | 当前生效配置 |
| POST | `/api/elec/commission-config/validate-effective-month` | 校验生效月份 |
| GET | `/api/elec/commission-config/preview-commission` | 分润预览 |
| GET | `/api/elec/agent-fee/page` | 分页查询代理费 |
| GET | `/api/elec/agent-fee/statistics` | 统计 |
| POST | `/api/elec/agent-fee/approve` | 审批通过/驳回 |
| POST | `/api/elec/agent-fee/batch-approve` | 批量审批 |
| POST | `/api/elec/agent-fee/settle` | 结算 |
| POST | `/api/elec/agent-fee/batch-settle` | 批量结算 |

#### 定时任务
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/elec/jobs/daily-profit/run` | 日利润计算 |
| POST | `/api/elec/jobs/monthly-profit/run` | 月利润聚合 |
| POST | `/api/elec/jobs/monthly-commission/run` | 月佣金结算 |
| POST | `/api/elec/jobs/price-effective/run` | 价格生效处理 |
| POST | `/api/elec/jobs/contract-expiry/run` | 合同到期提醒 |
