from fastapi import APIRouter, HTTPException, Depends
from app.adapters import get_adapter
from datetime import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.watchlist import WatchlistItem
from app.models.alert import Alert
from app.models.symbol import Symbol, Market, SymbolType
from app.schemas.monitor import AlertRule, AlertEvent, WatchItem, MonitorSummary, PositionRiskAlert
from app.core.sina_utils import sina_quote

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitor")



def _code_market(code: str) -> Market:
    """根据代码前缀判断交易所"""
    return Market.SH if code.startswith(("6", "9")) else Market.SZ


async def _get_or_create_symbol(db: AsyncSession, code: str, name: str = "") -> Symbol:
    """查找或创建 Symbol 记录"""
    result = await db.execute(select(Symbol).where(Symbol.code == code))
    symbol = result.scalar_one_or_none()
    if not symbol:
        symbol = Symbol(
            code=code,
            name=name or code,
            market=_code_market(code),
            type=SymbolType.STOCK,
        )
        db.add(symbol)
        await db.flush()
    return symbol


def _parse_condition(condition: str) -> tuple[str, str]:
    """解析 condition 字段为 (type, direction)"""
    if ":" in condition:
        alert_type, direction = condition.split(":", 1)
        return alert_type, direction
    return condition, "above"


def _encode_condition(alert_type: str, direction: str) -> str:
    """编码 type 和 direction 到 condition 字段"""
    if alert_type == "price_break" and direction:
        return f"{alert_type}:{direction}"
    return alert_type


async def _do_check_alerts(db: AsyncSession) -> list[AlertEvent]:
    """检查所有提醒触发条件（内部函数）"""
    events: list[AlertEvent] = []
    now = datetime.now().strftime("%H:%M:%S")
    result = await db.execute(
        select(Alert, Symbol)
        .join(Symbol, Alert.symbol_id == Symbol.id)
        .where(Alert.enabled == True)
    )
    rows = result.all()
    for alert, symbol in rows:
        q = sina_quote(symbol.code)
        triggered = False
        message = ""
        alert_type, direction = _parse_condition(alert.condition)

        if alert_type == "price_break":
            if direction == "above" and q["price"] >= alert.threshold:
                triggered = True
                message = f"{symbol.name} 突破 {alert.threshold}，现价 {q['price']}"
            elif direction == "below" and q["price"] <= alert.threshold:
                triggered = True
                message = f"{symbol.name} 跌破 {alert.threshold}，现价 {q['price']}"
        elif alert_type == "change_pct":
            if abs(q["change_pct"]) >= alert.threshold:
                triggered = True
                dir_label = "上涨" if q["change_pct"] > 0 else "下跌"
                message = f"{symbol.name} {dir_label}{abs(q['change_pct'])}%"

        if triggered:
            events.append(AlertEvent(
                code=symbol.code, name=symbol.name,
                type=alert_type, message=message,
                time=now, current_value=q["price"],
            ))
    return events


@router.get("/watchlist", response_model=list[WatchItem])
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem, Symbol)
        .join(Symbol, WatchlistItem.symbol_id == Symbol.id)
        .order_by(WatchlistItem.sort_order)
    )
    rows = result.all()
    items: list[WatchItem] = []
    for wi, symbol in rows:
        q = sina_quote(symbol.code)
        alert_cnt_result = await db.execute(
            select(Alert).where(Alert.symbol_id == symbol.id, Alert.enabled == True)
        )
        alert_cnt = len(alert_cnt_result.scalars().all())
        items.append(WatchItem(
            code=symbol.code, name=q["name"], price=q["price"],
            change_pct=q["change_pct"], alert_count=alert_cnt,
            sort_order=wi.sort_order,
        ))
    return items


@router.post("/watchlist/{code}")
async def add_to_watchlist(code: str, db: AsyncSession = Depends(get_db)):
    q = sina_quote(code)
    symbol = await _get_or_create_symbol(db, code, q["name"])
    result = await db.execute(select(WatchlistItem).where(WatchlistItem.symbol_id == symbol.id))
    if result.scalar_one_or_none():
        return {"ok": True, "code": code, "added": False, "message": f"股票 {code} 已在自选列表中"}
    max_result = await db.execute(
        select(WatchlistItem.sort_order).order_by(WatchlistItem.sort_order.desc()).limit(1)
    )
    max_order = max_result.scalar() or -1
    wi = WatchlistItem(symbol_id=symbol.id, sort_order=max_order + 1)
    db.add(wi)
    await db.commit()
    return {"ok": True, "code": code, "added": True, "message": f"股票 {code} 已添加到自选列表"}


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Symbol).where(Symbol.code == code))
    symbol = result.scalar_one_or_none()
    if not symbol:
        return {"ok": True, "code": code, "removed": False, "message": f"股票 {code} 不在自选列表中"}
    wi_result = await db.execute(select(WatchlistItem).where(WatchlistItem.symbol_id == symbol.id))
    wi = wi_result.scalar_one_or_none()
    if wi:
        await db.delete(wi)
        await db.commit()
        return {"ok": True, "code": code, "removed": True, "message": f"股票 {code} 已从自选列表移除"}
    return {"ok": True, "code": code, "removed": False, "message": f"股票 {code} 不在自选列表中"}


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


@router.get("/alerts", response_model=list[AlertRule])
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert, Symbol).join(Symbol, Alert.symbol_id == Symbol.id))
    rows = result.all()
    alerts: list[AlertRule] = []
    for alert, symbol in rows:
        alert_type, direction = _parse_condition(alert.condition)
        alerts.append(AlertRule(
            id=alert.id, code=symbol.code, name=symbol.name,
            type=alert_type, threshold=alert.threshold,
            direction=direction, enabled=alert.enabled,
        ))
    return alerts


@router.post("/alerts", response_model=AlertRule)
async def create_alert(rule: AlertRule, db: AsyncSession = Depends(get_db)):
    q = sina_quote(rule.code)
    symbol = await _get_or_create_symbol(db, rule.code, q["name"])
    alert = Alert(
        symbol_id=symbol.id,
        condition=_encode_condition(rule.type, rule.direction),
        threshold=rule.threshold,
        enabled=rule.enabled,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertRule(
        id=alert.id, code=symbol.code, name=symbol.name,
        type=rule.type, threshold=alert.threshold,
        direction=rule.direction, enabled=alert.enabled,
    )


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert:
        await db.delete(alert)
        await db.commit()
    return {"ok": True}


@router.get("/check", response_model=list[AlertEvent])
async def check_alerts(db: AsyncSession = Depends(get_db)):
    """检查所有提醒触发条件"""
    return await _do_check_alerts(db)


@router.get("/summary", response_model=MonitorSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    events = await _do_check_alerts(db)
    enabled_result = await db.execute(select(Alert).where(Alert.enabled == True))
    active_alerts = len(enabled_result.scalars().all())
    wl_result = await db.execute(select(WatchlistItem))
    watchlist_count = len(wl_result.scalars().all())
    return MonitorSummary(
        active_alerts=active_alerts,
        triggered_today=len(events),
        watchlist_count=watchlist_count,
        recent_events=events,
    )
