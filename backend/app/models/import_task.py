"""Import task model."""
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin

class ImportTask(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_import_task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str | None] = mapped_column(String(50))
    original_filename: Mapped[str | None] = mapped_column(String(200))
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    task_status: Mapped[int | None] = mapped_column(Integer, default=0)
    progress: Mapped[int | None] = mapped_column(Integer, default=0)
    total_rows: Mapped[int | None] = mapped_column(Integer)
    success_rows: Mapped[int | None] = mapped_column(Integer)
    failed_rows: Mapped[int | None] = mapped_column(Integer)
    skipped_rows: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    progress_message: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
