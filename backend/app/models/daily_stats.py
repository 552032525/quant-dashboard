from datetime import date
from sqlalchemy import Date, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class DailyStats(Base, TimestampMixin):
    __tablename__ = "daily_stats"

    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    total_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_market_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    available_cash: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    daily_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    daily_profit_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cumulative_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
