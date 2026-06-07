import asyncio
import akshare as ak
from datetime import date, datetime, time, timedelta
from app.adapters.base import DataSourceAdapter
import logging

logger = logging.getLogger(__name__)

# ── 简单内存缓存 ────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL_SECONDS = {
    "spot": 30,       # 全市场快照 30 秒
    "kline": 300,     # K 线 5 分钟
    "index": 30,      # 指数 30 秒
    "heat": 60,       # 市场热度 60 秒
    "sectors": 300,   # 板块 5 分钟
    "rankings": 30,   # 排行 30 秒
}

def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and (datetime.now() - entry["ts"]).total_seconds() < entry["ttl"]:
        return entry["data"]
    return None

def _cache_set(key: str, data, ttl_key: str = "spot"):
    _cache[key] = {"data": data, "ts": datetime.now(), "ttl": CACHE_TTL_SECONDS.get(ttl_key, 30)}

# ── 交易时间判断 ────────────────────────────────────────────
def _is_trading_time() -> bool:
    """判断当前是否在 A 股连续竞价时间 (9:30-11:30, 13:00-15:00)，工作日"""
    now = datetime.now()
    if now.weekday() >= 5:  # 周六日
        return False
    t = now.time()
    morning = time(9, 30) <= t <= time(11, 30)
    afternoon = time(13, 0) <= t <= time(15, 0)
    return morning or afternoon

def _trading_status() -> str:
    now = datetime.now()
    if now.weekday() >= 5:
        return "休市(周末)"
    t = now.time()
    if t < time(9, 30):
        return "盘前"
    if time(9, 30) <= t <= time(11, 30):
        return "盘中"
    if t < time(13, 0):
        return "午休"
    if time(13, 0) <= t <= time(15, 0):
        return "盘中"
    return "盘后"

# ── 安全取值辅助 ────────────────────────────────────────────
def _safe_float(row, *keys, default=0.0) -> float:
    for k in keys:
        try:
            v = row.get(k)
            if v is not None:
                return float(v)
        except (ValueError, TypeError):
            continue
    return default

def _safe_str(row, *keys, default="") -> str:
    for k in keys:
        try:
            v = row.get(k)
            if v is not None:
                return str(v)
        except (ValueError, TypeError):
            continue
    return default

def _safe_int(row, *keys, default=0) -> int:
    for k in keys:
        try:
            v = row.get(k)
            if v is not None:
                return int(float(v))
        except (ValueError, TypeError):
            continue
    return default


class AkshareAdapter(DataSourceAdapter):
    async def get_realtime_quote(self, code: str) -> dict:
        return await asyncio.to_thread(self._get_realtime_quote, code)

    def _get_realtime_quote(self, code: str) -> dict:
        try:
            cache_key = f"quote:{code}"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                raise ValueError(f"akshare 返回空数据（查询 {code}）")

            row = df[df["代码"] == code]
            if row.empty:
                # 尝试宽松匹配
                row = df[df["代码"].astype(str).str.zfill(6) == str(code).zfill(6)]
            if row.empty:
                raise ValueError(f"未找到股票: {code}")

            r = row.iloc[0]
            result = {
                "code": code,
                "name": _safe_str(r, "名称"),
                "price": _safe_float(r, "最新价"),
                "change": _safe_float(r, "涨跌额"),
                "change_pct": _safe_float(r, "涨跌幅"),
                "volume": _safe_float(r, "成交量"),
                "high": _safe_float(r, "最高"),
                "low": _safe_float(r, "最低"),
                "open": _safe_float(r, "今开"),
                "pre_close": _safe_float(r, "昨收"),
                "trading_status": _trading_status(),
            }
            _cache_set(cache_key, result, "spot")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"获取 {code} 实时行情失败: {e}", exc_info=True)
            raise ValueError(f"获取 {code} 行情失败: {e}") from e

    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        return await asyncio.to_thread(self._get_kline, code, start_date, end_date, period)

    def _get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        try:
            cache_key = f"kline:{code}:{start_date}:{end_date}:{period}"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            minute_periods = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
            if period in minute_periods:
                start_str = start_date.strftime("%Y-%m-%d 09:30:00")
                end_str = end_date.strftime("%Y-%m-%d 15:00:00")
                df = ak.stock_zh_a_hist_min_em(symbol=code, period=period,
                    start_date=start_str, end_date=end_str, adjust="qfq")
                if df is None or df.empty:
                    logger.warning(f"{code} 分钟 K 线无数据 ({period}min)")
                    return []
                result = [{"date": _safe_str(row, "时间"), "open": _safe_float(row, "开盘"),
                         "high": _safe_float(row, "最高"), "low": _safe_float(row, "最低"),
                         "close": _safe_float(row, "收盘"), "volume": _safe_float(row, "成交量")}
                        for _, row in df.iterrows()]
            else:
                period_map = {"weekly": "week", "monthly": "month"}
                ak_period = period_map.get(period, "daily")
                df = ak.stock_zh_a_hist(symbol=code, period=ak_period,
                    start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
                if df is None or df.empty:
                    logger.warning(f"{code} 日 K 线无数据 ({period})")
                    return []
                result = [{"date": _safe_str(row, "日期"), "open": _safe_float(row, "开盘"),
                         "high": _safe_float(row, "最高"), "low": _safe_float(row, "最低"),
                         "close": _safe_float(row, "收盘"), "volume": _safe_float(row, "成交量")}
                        for _, row in df.iterrows()]

            _cache_set(cache_key, result, "kline")
            return result
        except Exception as e:
            logger.error(f"获取 {code} K线失败: {e}", exc_info=True)
            raise ValueError(f"获取 {code} K线失败: {e}") from e

    async def search_symbol(self, keyword: str) -> list[dict]:
        return await asyncio.to_thread(self._search_symbol, keyword)

    def _search_symbol(self, keyword: str) -> list[dict]:
        try:
            cache_key = f"search:{keyword}"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                logger.warning("搜索股票：akshare 返回空数据")
                return []

            name_col = "名称" if "名称" in df.columns else df.columns[1]
            code_col = "代码" if "代码" in df.columns else df.columns[0]
            mask = df[name_col].astype(str).str.contains(keyword, na=False) | df[code_col].astype(str).str.contains(keyword, na=False)
            result = [{"code": str(row[code_col]), "name": str(row[name_col])}
                      for _, row in df[mask].head(20).iterrows()]
            _cache_set(cache_key, result, "spot")
            return result
        except Exception as e:
            logger.error(f"搜索股票失败: {e}", exc_info=True)
            return []

    async def get_index_quotes(self) -> list[dict]:
        return await asyncio.to_thread(self._get_index_quotes)

    def _get_index_quotes(self) -> list[dict]:
        try:
            cache_key = "index_quotes"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            df = ak.stock_zh_index_spot_em()
            if df is None or df.empty:
                logger.warning("获取指数行情：空数据")
                return []

            code_col = "代码" if "代码" in df.columns else df.columns[0]
            targets = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指"}
            result = []
            for _, row in df.iterrows():
                code = str(row[code_col])
                if code in targets:
                    result.append({
                        "code": code,
                        "name": _safe_str(row, "名称"),
                        "price": _safe_float(row, "最新价"),
                        "change": _safe_float(row, "涨跌额"),
                        "change_pct": _safe_float(row, "涨跌幅"),
                    })
            _cache_set(cache_key, result, "index")
            return result
        except Exception as e:
            logger.error(f"获取指数行情失败: {e}", exc_info=True)
            return []

    async def get_market_heat(self) -> dict:
        return await asyncio.to_thread(self._get_market_heat)

    def _get_market_heat(self) -> dict:
        try:
            cache_key = "market_heat"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return {"up_count": 0, "down_count": 0, "flat_count": 0,
                        "limit_up": 0, "limit_down": 0, "total_volume": 0.0,
                        "north_flow": 0.0, "trading_status": _trading_status()}

            chg_col = "涨跌幅" if "涨跌幅" in df.columns else df.columns[4]
            up_count = int((df[chg_col] > 0).sum())
            down_count = int((df[chg_col] < 0).sum())
            flat_count = int((df[chg_col] == 0).sum())

            vol_col = "成交额" if "成交额" in df.columns else df.columns[5]
            total_volume = round(float(df[vol_col].sum()) / 1e8, 2)

            north_flow = 0.0
            try:
                north_df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
                if north_df is not None and len(north_df) > 0:
                    north_flow = _safe_float(north_df.iloc[-1], "当日净流入")
            except Exception:
                pass

            result = {
                "up_count": up_count, "down_count": down_count, "flat_count": flat_count,
                "limit_up": 0, "limit_down": 0,
                "total_volume": total_volume, "north_flow": north_flow,
                "trading_status": _trading_status(),
            }
            _cache_set(cache_key, result, "heat")
            return result
        except Exception as e:
            logger.error(f"获取市场热度失败: {e}", exc_info=True)
            return {"up_count": 0, "down_count": 0, "flat_count": 0,
                    "limit_up": 0, "limit_down": 0, "total_volume": 0.0,
                    "north_flow": 0.0, "trading_status": _trading_status()}

    async def get_sectors(self, sector_type: str = "industry") -> list[dict]:
        return await asyncio.to_thread(self._get_sectors, sector_type)

    def _get_sectors(self, sector_type: str) -> list[dict]:
        try:
            cache_key = f"sectors:{sector_type}"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            fn = ak.stock_board_industry_spot_em if sector_type == "industry" else ak.stock_board_concept_spot_em
            df = fn()
            if df is None or df.empty:
                return []

            result = []
            for _, row in df.iterrows():
                result.append({
                    "name": _safe_str(row, "板块名称"),
                    "change_pct": _safe_float(row, "涨跌幅"),
                    "lead_stock": _safe_str(row, "领涨股票", "领涨股"),
                    "stock_count": _safe_int(row, "公司家数", "上涨家数"),
                })
            _cache_set(cache_key, result, "sectors")
            return result
        except Exception as e:
            logger.error(f"获取板块数据失败: {e}", exc_info=True)
            return []

    async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]:
        return await asyncio.to_thread(self._get_rankings, rank_type, limit)

    def _get_rankings(self, rank_type: str, limit: int) -> list[dict]:
        try:
            cache_key = f"rankings:{rank_type}:{limit}"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return []

            chg_col = "涨跌幅" if "涨跌幅" in df.columns else df.columns[4]
            ascending = rank_type != "up"
            df_sorted = df.sort_values(chg_col, ascending=ascending).head(limit)

            result = []
            for _, row in df_sorted.iterrows():
                result.append({
                    "code": _safe_str(row, "代码"),
                    "name": _safe_str(row, "名称"),
                    "price": _safe_float(row, "最新价"),
                    "change_pct": _safe_float(row, chg_col),
                })
            _cache_set(cache_key, result, "rankings")
            return result
        except Exception as e:
            logger.error(f"获取排行榜失败: {e}", exc_info=True)
            return []

    async def get_intraday(self, code: str) -> list[dict]:
        return await asyncio.to_thread(self._get_intraday, code)

    def _get_intraday(self, code: str) -> list[dict]:
        try:
            cache_key = f"intraday:{code}"
            cached = _cache_get(cache_key)
            if cached:
                return cached

            today = datetime.now().strftime("%Y-%m-%d")
            df = ak.stock_zh_a_hist_min_em(symbol=code, period="1",
                start_date=f"{today} 09:30:00", end_date=f"{today} 15:00:00", adjust="")
            if df is None or df.empty:
                return []

            result = []
            for _, row in df.iterrows():
                result.append({
                    "time": _safe_str(row, "时间"),
                    "price": _safe_float(row, "收盘"),
                    "avg_price": _safe_float(row, "收盘"),
                    "volume": _safe_float(row, "成交量"),
                })
            _cache_set(cache_key, result, "spot")
            return result
        except Exception as e:
            logger.error(f"获取 {code} 分时数据失败: {e}", exc_info=True)
            return []
