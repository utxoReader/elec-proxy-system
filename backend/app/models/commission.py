"""Commission configuration model."""
from decimal import Decimal
from sqlalchemy import Integer, String, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, RegionMixin

class CommissionConfig(TimestampMixin, SoftDeleteMixin, RegionMixin, Base):
    __tablename__ = "elec_commission_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_month: Mapped[str | None] = mapped_column(String(7))
    effective_month: Mapped[str | None] = mapped_column(String(7))
    agent_commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    parent_commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    company_commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    status: Mapped[int | None] = mapped_column(Integer, default=1)
    remark: Mapped[str | None] = mapped_column(Text)
