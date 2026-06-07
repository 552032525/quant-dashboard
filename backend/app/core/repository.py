"""Repository 模式 — 数据访问抽象层

提供通用 CRUD 操作的泛型基类，封装 SQLAlchemy 查询逻辑。
调用方通过依赖注入获取 AsyncSession，Repository 仅做 flush 不 commit，
事务边界由调用方控制。

使用示例（供后续迁移参考）:

    # 在 API 路由中使用
    from app.core.repository import BaseRepository
    from app.models.symbol import Symbol

    @router.get("/symbols")
    async def list_symbols(db: AsyncSession = Depends(get_db)):
        repo = BaseRepository(Symbol, db)
        symbols = await repo.get_all(limit=50)
        return symbols

    # 按条件查找
    symbol = await repo.find_one_by(code="600519")
"""

from typing import TypeVar, Generic, Optional, Sequence, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """通用 Repository 基类，封装模型级别的 CRUD 操作。

    泛型参数 T 必须是 Base 的子类。
    """

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[T]:
        """按主键 id 查询单条记录。"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """分页获取所有记录。"""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def count(self, **filters: Any) -> int:
        """按过滤条件统计记录数。"""
        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create(self, **kwargs: Any) -> T:
        """创建一条新记录，flush 但不 commit。"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: T, **kwargs: Any) -> T:
        """更新实例字段，None 值会被跳过。"""
        for key, value in kwargs.items():
            if value is not None and hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        """删除一条记录，flush 但不 commit。"""
        await self.session.delete(instance)
        await self.session.flush()

    async def delete_by_id(self, id: int) -> bool:
        """按 id 删除记录，返回是否成功。"""
        instance = await self.get_by_id(id)
        if instance:
            await self.delete(instance)
            return True
        return False

    async def find_by(self, **filters: Any) -> Sequence[T]:
        """按字段等值过滤，返回所有匹配记录。"""
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_one_by(self, **filters: Any) -> Optional[T]:
        """按字段等值过滤，返回第一条匹配记录或 None。"""
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
