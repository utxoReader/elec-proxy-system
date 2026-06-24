"""APScheduler background job configuration.

The scheduler is exposed as a module-level singleton and is only started when
``settings.SCHEDULER_ENABLED`` is True.  Job wrappers create their own database
session, bypass the region guard (jobs run as the system user) and ensure the
session is closed cleanly.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.db_region_guard import admin_bypass_context
from app.services.scheduled_jobs import (
    run_contract_expiry_reminder,
    run_daily_profit_calculation,
    run_monthly_commission_settlement,
    run_price_effective_job,
)

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _with_db_session(job_func: Callable[[object], None]) -> Callable[[], None]:
    """Wrap a job function so it receives a fresh DB session and bypasses RLS."""

    @wraps(job_func)
    def wrapper() -> None:
        with admin_bypass_context():
            db = SessionLocal()
            try:
                job_func(db)
            except Exception:
                logger.exception("Scheduled job %s failed", job_func.__name__)
                db.rollback()
                raise
            finally:
                db.close()

    return wrapper


def get_scheduler() -> BackgroundScheduler:
    """Return the module-level scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the background scheduler if enabled in settings."""
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled by configuration (SCHEDULER_ENABLED=false).")
        return

    scheduler = get_scheduler()
    tz = "Asia/Shanghai"

    scheduler.add_job(
        _with_db_session(run_daily_profit_calculation),
        trigger=CronTrigger(hour=3, minute=0, timezone=tz),
        id="daily_profit_job",
        name="Daily profit calculation",
        replace_existing=True,
    )
    scheduler.add_job(
        _with_db_session(run_monthly_commission_settlement),
        trigger=CronTrigger(hour=2, minute=0, timezone=tz),
        id="monthly_commission_job",
        name="Monthly commission settlement",
        replace_existing=True,
    )
    scheduler.add_job(
        _with_db_session(run_price_effective_job),
        trigger=CronTrigger(hour=0, minute=5, timezone=tz),
        id="price_effective_job",
        name="Price effective job",
        replace_existing=True,
    )
    scheduler.add_job(
        _with_db_session(run_contract_expiry_reminder),
        trigger=CronTrigger(hour=9, minute=0, timezone=tz),
        id="contract_expiry_job",
        name="Contract expiry reminder",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with %s jobs.", len(scheduler.get_jobs()))


def shutdown_scheduler() -> None:
    """Shut down the background scheduler if it is running."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")
