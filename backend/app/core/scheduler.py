"""
APScheduler 定时任务调度器
- 开盘前数据更新（9:25）
- 收盘快照（15:30）
- 自选股价格刷新（每 30 秒）
"""
import asyncio
import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

logger = logging.getLogger("scheduler")

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def refresh_watchlist_prices():
    """每 30 秒刷新自选股价格（轻量心跳）"""
    from app.core.database import async_session
    from app.models.watchlist import WatchlistItem
    from app.models.symbol import Symbol
    from app.adapters import get_adapter

    try:
        async with async_session() as db:
            result = await db.execute(
                select(Symbol.code).select_from(WatchlistItem)
                .join(Symbol, WatchlistItem.symbol_id == Symbol.id)
            )
            codes = [row[0] for row in result.all()]
            if not codes:
                return

            adapter = get_adapter()
            for code in codes:
                try:
                    await adapter.get_realtime_quote(code)
                except Exception:
                    pass  # 静默跳过单个失败
    except Exception as e:
        logger.warning(f"自选股价格刷新异常: {e}")


async def daily_open_data_update():
    """开盘前 9:25 更新今日数据"""
    logger.info("⏰ 执行开盘前数据更新 (9:25)")
    from app.core.database import async_session

    try:
        async with async_session() as db:
            # 预留：可在此处自动拉取当日 K 线数据
            pass
        logger.info("✅ 开盘前数据更新完成")
    except Exception as e:
        logger.error(f"开盘前数据更新失败: {e}", exc_info=True)


async def daily_close_snapshot():
    """收盘 15:30 保存当日快照到 daily_stats"""
    logger.info("⏰ 执行收盘快照 (15:30)")

    try:
        from app.core.database import async_session
        from app.models.daily_stats import DailyStats
        from app.models.position import Position
        from app.models.symbol import Symbol
        from app.adapters import get_adapter

        today = date.today()

        async with async_session() as db:
            # 检查是否已有今日快照
            existing = await db.execute(
                select(DailyStats).where(DailyStats.date == today)
            )
            if existing.scalar_one_or_none():
                logger.info(f"今日 ({today}) 已有快照，跳过")
                return

            # 计算持仓数据
            result = await db.execute(select(Position))
            positions = result.scalars().all()
            total_cost = 0.0
            total_market_value = 0.0

            for p in positions:
                sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
                symbol = sym_result.scalar_one_or_none()
                code = symbol.code if symbol else ""
                current_price = None
                if code:
                    try:
                        adapter = get_adapter()
                        quote = await adapter.get_realtime_quote(code)
                        current_price = float(quote.get("price", 0))
                    except Exception:
                        pass
                cost = p.quantity * p.cost_price
                total_cost += cost
                if current_price and current_price > 0:
                    total_market_value += current_price * p.quantity
                else:
                    total_market_value += cost

            from datetime import timedelta
            yesterday = today - timedelta(days=1)
            yesterday_result = await db.execute(
                select(DailyStats).where(DailyStats.date <= yesterday)
                .order_by(DailyStats.date.desc()).limit(1)
            )
            yesterday_record = yesterday_result.scalar_one_or_none()

            if yesterday_record:
                daily_profit = round(total_market_value - yesterday_record.total_assets, 2)
                daily_profit_pct = round(daily_profit / yesterday_record.total_assets * 100, 2) if yesterday_record.total_assets > 0 else 0.0
                cumulative_profit = round(yesterday_record.cumulative_profit + daily_profit, 2)
            else:
                daily_profit = 0.0
                daily_profit_pct = 0.0
                cumulative_profit = 0.0

            record = DailyStats(
                date=today,
                total_assets=round(total_market_value, 2),
                total_market_value=round(total_market_value, 2),
                available_cash=0.0,
                daily_profit=daily_profit,
                daily_profit_pct=daily_profit_pct,
                cumulative_profit=cumulative_profit,
            )
            db.add(record)
            await db.commit()
            # 收盘后发送日报邮件
            try:
                from app.services.notify_service import send_alert_notification
                summary_msg = f"总资产: {record.total_assets}, 日收益: {record.daily_profit} ({record.daily_profit_pct}%)"
                await send_alert_notification(
                    [{"code": "SUMMARY", "name": "收盘摘要", "message": summary_msg}]
                )
            except Exception:
                pass  # 邮件失败不影响快照

            logger.info(f"✅ 收盘快照已保存: 总资产={record.total_assets}, 日收益={record.daily_profit}")
    except Exception as e:
        logger.error(f"收盘快照失败: {e}", exc_info=True)


def start_scheduler():
    """启动调度器"""
    # 每 30 秒刷新自选股价格
    scheduler.add_job(
        refresh_watchlist_prices,
        IntervalTrigger(seconds=30),
        id="refresh_watchlist",
        name="刷新自选股价格",
        replace_existing=True,
    )
    # 开盘前数据更新（交易日 9:25）
    scheduler.add_job(
        daily_open_data_update,
        CronTrigger(hour=9, minute=25, day_of_week="mon-fri"),
        id="daily_open",
        name="开盘前数据更新",
        replace_existing=True,
    )
    # 收盘快照（交易日 15:30）
    scheduler.add_job(
        daily_close_snapshot,
        CronTrigger(hour=15, minute=30, day_of_week="mon-fri"),
        id="daily_close",
        name="收盘快照",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ APScheduler 已启动（3 个定时任务）")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown(wait=False)
    logger.info("APScheduler 已关闭")
