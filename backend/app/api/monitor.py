from fastapi import APIRouter, HTTPException
from datetime import datetime
import requests, re
from app.schemas.monitor import AlertRule, AlertEvent, WatchItem, MonitorSummary

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
        pass
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
    if code not in _watchlist:
        _watchlist.append(code)
    return {"ok": True, "code": code}


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str):
    if code in _watchlist:
        _watchlist.remove(code)
    return {"ok": True}


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
