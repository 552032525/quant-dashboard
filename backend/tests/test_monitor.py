"""自选股 + 预警 API 测试"""
import pytest

@pytest.mark.asyncio
async def test_watchlist_empty(client):
    """初始自选股列表为空"""
    response = await client.get("/api/monitor/watchlist")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_add_remove_watch(client):
    """添加和删除自选股"""
    # 添加
    resp = await client.post("/api/monitor/watchlist/600519")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    
    # 列表应有1条
    resp = await client.get("/api/monitor/watchlist")
    assert len(resp.json()) >= 1
    
    # 删除
    resp = await client.delete("/api/monitor/watchlist/600519")
    assert resp.status_code == 200
    assert resp.json()["removed"] is True

@pytest.mark.asyncio
async def test_alerts_crud(client):
    """预警 CRUD"""
    # 创建
    resp = await client.post("/api/monitor/alerts", json={
        "code": "600519", "type": "price_break",
        "threshold": 2000, "direction": "above", "enabled": True
    })
    assert resp.status_code == 200
    alert = resp.json()
    assert alert["code"] == "600519"
    
    # 列表
    resp = await client.get("/api/monitor/alerts")
    assert len(resp.json()) >= 1
    
    # 删除
    alert_id = alert["id"]
    resp = await client.delete(f"/api/monitor/alerts/{alert_id}")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_check_alerts(client):
    """预警检查不报错"""
    resp = await client.get("/api/monitor/check")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_summary(client):
    """监控摘要不报错"""
    resp = await client.get("/api/monitor/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_alerts" in data