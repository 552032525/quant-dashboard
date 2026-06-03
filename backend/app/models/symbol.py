from sqlalchemy import String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum
from app.models.base import Base, TimestampMixin

class Market(str, enum.Enum):
    SH = "SH"
    SZ = "SZ"

class SymbolType(str, enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"

class Symbol(Base, TimestampMixin):
    __tablename__ = "symbols"
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[Market] = mapped_column(SqlEnum(Market), nullable=False)
    type: Mapped[SymbolType] = mapped_column(SqlEnum(SymbolType), default=SymbolType.STOCK)
