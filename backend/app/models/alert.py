from sqlalchemy import BigInteger, Float, Boolean, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
