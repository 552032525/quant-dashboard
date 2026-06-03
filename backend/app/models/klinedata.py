from sqlalchemy import BigInteger, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.models.base import Base, TimestampMixin

class KLineData(Base, TimestampMixin):
    __tablename__ = "klinedata"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
