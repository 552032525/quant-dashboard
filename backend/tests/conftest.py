"""pytest 共享 fixtures"""
import os
import pytest
import asyncio

# 必须在导入 app 之前设置，因为 settings 在模块加载时初始化
os.environ["database_url"] = "sqlite+aiosqlite:///./test_quant_dashboard.db"

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine
from app.models import Base

@pytest.fixture(scope="session")
def event_loop():
    """创建 session 级事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def init_db():
    """初始化测试数据库表（session 级，整个测试会话执行一次）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 清理：测试结束后删除测试数据库文件
    test_db = "test_quant_dashboard.db"
    if os.path.exists(test_db):
        os.remove(test_db)

@pytest.fixture
async def client(init_db):
    """异步 HTTP 测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac