from sqlalchemy import BigInteger, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class Position(Base, TimestampMixin):
    __tablename__ = "positions"
    __table_args__ = (
        Index("idx_positions_symbol_id", "symbol_id"),
        Index("idx_positions_created_at", "created_at"),
    )
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
