from sqlalchemy import BigInteger, Float, String, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class Trade(Base, TimestampMixin):
    __tablename__ = "trades"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False)
    trade_type: Mapped[str] = mapped_column(String(10), nullable=False)  # buy / sell
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    trade_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    note: Mapped[str] = mapped_column(String(200), default="")
