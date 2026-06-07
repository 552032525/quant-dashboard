from fastapi import APIRouter, HTTPException
from app.adapters import get_adapter
from datetime import datetime
import requests, re, logging
from app.schemas.monitor import AlertRule, AlertEvent, WatchItem, MonitorSummary, PositionRiskAlert

logger = logging.getLogger(__name__)
SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}
router = APIRouter(prefix="/monitor")

# 简易内存存储（生产环境应用数据库）
_alerts: list[dict] = []
_watchlist: list[str] = []


def _sina_quote(code: str) -> dict:
    prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers=SINA_HEADERS, timeout=5)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if m:
            parts = m.group(1).split(",")
            if len(parts) >= 4:
                price = float(parts[3]) if parts[3] else 0
                prev = float(parts[2]) if parts[2] else 0
                chg = (price - prev) / prev * 100 if prev > 0 else 0
                return {"name": parts[0], "price": price, "change_pct": round(chg, 2)}
    except Exception:
        logger.warning(f"新浪行情获取失败: {code}")
    return {"name": code, "price": 0, "change_pct": 0}


@router.get("/watchlist", response_model=list[WatchItem])
async def get_watchlist():
    items = []
    for code in _watchlist:
        q = _sina_quote(code)
        alert_cnt = sum(1 for a in _alerts if a["code"] == code and a["enabled"])
        items.append(WatchItem(
            code=code, name=q["name"], price=q["price"],
            change_pct=q["change_pct"], alert_count=alert_cnt,
            sort_order=_watchlist.index(code),
        ))
    return items


@router.post("/watchlist/{code}")
async def add_to_watchlist(code: str):
    if code in _watchlist:
        return {"ok": True, "code": code, "added": False, "message": f"股票 {code} 已在自选列表中"}
    _watchlist.append(code)
    return {"ok": True, "code": code, "added": True, "message": f"股票 {code} 已添加到自选列表"}


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str):
    if code in _watchlist:
        _watchlist.remove(code)
        return {"ok": True, "code": code, "removed": True, "message": f"股票 {code} 已从自选列表移除"}
    return {"ok": True, "code": code, "removed": False, "message": f"股票 {code} 不在自选列表中"}


@router.get("/alerts", response_model=list[AlertRule])
async def get_alerts():
    return [AlertRule(**a) for a in _alerts]


@router.post("/alerts", response_model=AlertRule)
async def create_alert(rule: AlertRule):
    q = _sina_quote(rule.code)
    alert = {
        "id": len(_alerts) + 1,
        "code": rule.code,
        "name": q["name"],
        "type": rule.type,
        "threshold": rule.threshold,
        "direction": rule.direction,
        "enabled": rule.enabled,
    }
    _alerts.append(alert)
    return AlertRule(**alert)


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int):
    global _alerts
    _alerts = [a for a in _alerts if a["id"] != alert_id]
    return {"ok": True}


@router.get("/check", response_model=list[AlertEvent])
async def check_alerts():
    """检查所有提醒触发条件"""
    events = []
    now = datetime.now().strftime("%H:%M:%S")
    for alert in _alerts:
        if not alert["enabled"]:
            continue
        q = _sina_quote(alert["code"])
        triggered = False
        message = ""

        if alert["type"] == "price_break":
            if alert["direction"] == "above" and q["price"] >= alert["threshold"]:
                triggered = True
                message = f"{alert['name']} 突破 {alert['threshold']}，现价 {q['price']}"
            elif alert["direction"] == "below" and q["price"] <= alert["threshold"]:
                triggered = True
                message = f"{alert['name']} 跌破 {alert['threshold']}，现价 {q['price']}"
        elif alert["type"] == "change_pct":
            if abs(q["change_pct"]) >= alert["threshold"]:
                triggered = True
                direction = "上涨" if q["change_pct"] > 0 else "下跌"
                message = f"{alert['name']} {direction}{abs(q['change_pct'])}%"

        if triggered:
            events.append(AlertEvent(
                code=alert["code"], name=alert["name"],
                type=alert["type"], message=message,
                time=now, current_value=q["price"],
            ))

    return events


@router.get("/summary", response_model=MonitorSummary)
async def get_summary():
    events = await check_alerts()
    return MonitorSummary(
        active_alerts=sum(1 for a in _alerts if a["enabled"]),
        triggered_today=len(events),
        watchlist_count=len(_watchlist),
        recent_events=events,
    )
# ── 仓位风险检查 ──────────────────────────────────────────
@router.get("/position-risk", response_model=list[PositionRiskAlert])
async def check_position_risk():
    """检查持仓占比是否超限"""
    from app.schemas.monitor import PositionRiskAlert
    alerts: list[PositionRiskAlert] = []
    try:
        # 从 portfolio 接口获取所有持仓
        from app.api.portfolio import list_positions, get_summary
        from app.core.database import async_session
        from sqlalchemy import select
        from app.models.position import Position
        from app.models.symbol import Symbol

        async with async_session() as db:
            result = await db.execute(select(Position))
            positions = result.scalars().all()
            if not positions:
                return alerts

            total_market_value = 0.0
            position_values = []

            for p in positions:
                sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
                symbol = sym_result.scalar_one_or_none()
                code = symbol.code if symbol else ""
                name = symbol.name if symbol else code

                # 尝试获取实时价格
                try:
                    adapter = get_adapter()
                    quote = await adapter.get_realtime_quote(code)
                    price = float(quote.get("price", 0))
                except Exception:
                    price = p.cost_price  # 回退到成本价

                market_value = price * p.quantity
                total_market_value += market_value
                position_values.append({
                    "code": code, "name": name,
                    "market_value": market_value, "price": price,
                })

            if total_market_value <= 0:
                return alerts

            for pv in position_values:
                weight = round(pv["market_value"] / total_market_value * 100, 2)
                risk_level = "low"
                message = ""

                if weight > 40:
                    risk_level = "high"
                    message = f"⚠ 单票占比 {weight}%，严重超标！建议降至 30% 以下"
                elif weight > 30:
                    risk_level = "medium"
                    message = f"⚡ 单票占比 {weight}%，超过 30% 警戒线"
                elif weight > 20:
                    risk_level = "low"
                    message = f"单票占比 {weight}%，适度关注"

                if message:
                    alerts.append(PositionRiskAlert(
                        code=pv["code"], name=pv["name"],
                        weight_pct=weight, message=message,
                        risk_level=risk_level,
                    ))

            # 排序：高风险优先
            alerts.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a.risk_level])
    except Exception as e:
        logger.error(f"仓位风险检查失败: {e}", exc_info=True)

    return alerts

