# 桐叶售电代理系统 — 后端

基于 **FastAPI + SQLAlchemy 2.0 + Pydantic v2 + PostgreSQL** 重建的桐叶售电代理后端。

## 环境要求

- Python 3.12（请勿使用系统 Python 3.14 alpha，pydantic_core 会 segfault）
- PostgreSQL 16（推荐通过 Docker Compose 启动）
- Docker & Docker Compose（可选）

## 快速开始

### 1. 创建并激活虚拟环境

```bash
cd /Users/wo/ProjectCat/projects/售电/桐叶/elec-proxy-system/backend
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 PostgreSQL

```bash
docker compose up -d
```

PostgreSQL 将运行在 `localhost:5432`，数据库/用户名/密码均为 `tongye`。

### 4. 配置环境变量

项目已包含默认 `.env`，可直接用于本地开发。生产环境请复制 `.env.example` 并替换敏感配置：

```bash
cp .env.example .env.production
# 编辑 .env.production 中的 SECRET_KEY 与 DATABASE_URL
```

### 5. 执行数据库迁移

Phase 1 将接入 Alembic / SQLAlchemy 迁移。当前占位脚本：

```bash
# TODO: alembic upgrade head
psql postgresql://tongye:tongye@localhost:5432/tongye -f migrations/001_init.sql
```

### 6. 运行应用

```bash
bash scripts/start.sh
# 或直接
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

- API: <http://localhost:8000/api/health>
- 文档: <http://localhost:8000/api/docs>

### 7. 运行测试

```bash
pytest
```

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy engine / session / base
│   ├── dependencies.py      # 通用依赖（get_db / get_current_user）
│   ├── exceptions.py        # 全局异常处理 + 统一响应封装
│   ├── logging.py           # 日志配置
│   ├── routers/             # API 路由
│   ├── models/              # ORM 模型
│   ├── schemas/             # Pydantic 模型
│   ├── services/            # 业务逻辑
│   └── core/                # 安全 / 常量等工具
├── migrations/              # 数据库迁移
├── tests/                   # pytest 测试
├── scripts/                 # 启动脚本
├── docker-compose.yml       # PostgreSQL 16 服务
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 注意事项

- 业务模型已由 #6 设计完成，位于 `app/models/`。
- 认证相关接口（`POST /api/auth/login`、`POST /api/auth/register`）为占位实现，后续 Phase 会补充真实逻辑。
- 生产环境务必将 `SECRET_KEY` 替换为强随机字符串。
