# 桐叶售电系统 — 部署文档

## 快速启动（开发环境）

### 前置要求
- Python 3.12+
- Node.js 22+
- PostgreSQL 16+
- Redis（可选，用于会话缓存）

### 1. 后端

```bash
cd backend

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库连接等配置

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（代理 → localhost:8000）
npm run dev
```

### 3. 访问
- 前端: http://localhost:5173
- API 文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/api/health

---

## 生产部署（Docker Compose）

### 前置要求
- Docker Engine 24+
- Docker Compose v2+

### 一键部署

```bash
# 克隆项目
cd elec-proxy-system

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 服务端口
| 服务 | 端口 | 说明 |
|---|---|---|
| Nginx (前端) | 80 | 管理后台 |
| FastAPI (后端) | 8000 | REST API |
| PostgreSQL | 5432 | 数据库 |

### 生产环境变量
编辑 `docker-compose.yml` 或传入 `.env` 文件覆盖以下关键变量：
- `SECRET_KEY` — JWT 签名密钥（必须修改）
- `CORS_ORIGINS` — 允许的跨域来源

---

## 数据库管理

### 迁移

```bash
cd backend
source .venv/bin/activate

# 生成新迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 查看状态
alembic current
```

### 初始化数据
首次部署时运行：

```bash
# 方式一：Alembic 迁移自动建表
alembic upgrade head

# 方式二：直接执行 SQL
psql -U tongye -d tongye -f migrations/001_init.sql
```

---

## 环境变量说明

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://tongye:tongye@localhost:5432/tongye` | 数据库连接串 |
| `SECRET_KEY` | `auto‑generated`（自动生成随机密钥） | JWT 签名密钥；重启后 token 失效 |
| `APP_ENV` | `development` | 运行环境 |
| `APP_NAME` | 桐叶售电代理系统 | 应用名称 |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | 跨域来源；生产环境限制为具体前端域名 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | Token 有效期(分钟)，默认 24 小时 |
