"""持仓 API 测试"""
import pytest

@pytest.mark.asyncio
async def test_portfolio_list_empty(client):
    """空持仓列表"""
    resp = await client.get("/api/portfolio")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_portfolio_summary(client):
    """持仓摘要（空持仓时有默认值）"""
    resp = await client.get("/api/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_assets" in data
    assert "total_profit_loss" in data

@pytest.mark.asyncio
async def test_stats_latest(client):
    """收益统计（无数据时404）"""
    resp = await client.get("/api/stats/latest")
    assert resp.status_code in [200, 404]

@pytest.mark.asyncio
async def test_stats_daily(client):
    """每日统计列表"""
    resp = await client.get("/api/stats/daily")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)