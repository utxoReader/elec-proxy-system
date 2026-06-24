"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.scheduler import shutdown_scheduler, start_scheduler
from app.exceptions import add_exception_handlers
from app.logging import configure_logging
from app.routers import agent, auth, commission, consumption, customer, health, import_task, inquiry, price, profit, scheduled_jobs, usage_curve_template

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="桐叶售电代理系统后端 API",
    docs_url="/api/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/api/redoc" if settings.APP_ENV == "development" else None,
    openapi_url="/api/openapi.json" if settings.APP_ENV == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_exception_handlers(app)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(price.router, prefix="/api", tags=["Elec-Price"])
app.include_router(agent.router, prefix="/api", tags=["Elec-Agent"])
app.include_router(customer.router, prefix="/api", tags=["Elec-Customer"])
app.include_router(profit.router, prefix="/api", tags=["Elec-Profit"])
app.include_router(commission.router, prefix="/api", tags=["Elec-Commission"])
app.include_router(consumption.router, prefix="/api", tags=["Elec-Consumption"])
app.include_router(usage_curve_template.router, prefix="/api", tags=["Elec-UsageCurve"])
app.include_router(import_task.router, prefix="/api", tags=["Elec-ImportTask"])
app.include_router(inquiry.router, prefix="/api", tags=["Elec-Inquiry"])
app.include_router(scheduled_jobs.router, prefix="/api", tags=["Elec-Jobs"])
