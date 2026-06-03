from sqlalchemy import BigInteger, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class WatchlistItem(Base, TimestampMixin):
    __tablename__ = "watchlist"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
