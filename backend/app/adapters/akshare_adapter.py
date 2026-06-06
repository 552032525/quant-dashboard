import asyncio
import akshare as ak
from datetime import date, datetime
from app.adapters.base import DataSourceAdapter

class AkshareAdapter(DataSourceAdapter):
    async def get_realtime_quote(self, code: str) -> dict:
        return await asyncio.to_thread(self._get_realtime_quote, code)

    def _get_realtime_quote(self, code: str) -> dict:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if row.empty:
            raise ValueError(f"未找到股票: {code}")
        r = row.iloc[0]
        return {
            "code": code, "name": r["名称"],
            "price": float(r["最新价"]), "change": float(r["涨跌额"]),
            "change_pct": float(r["涨跌幅"]), "volume": float(r["成交量"]),
            "high": float(r["最高"]), "low": float(r["最低"]),
            "open": float(r["今开"]), "pre_close": float(r["昨收"]),
        }

    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        return await asyncio.to_thread(self._get_kline, code, start_date, end_date, period)

    def _get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        minute_periods = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
        if period in minute_periods:
            start_str = start_date.strftime("%Y-%m-%d 09:30:00")
            end_str = end_date.strftime("%Y-%m-%d 15:00:00")
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=period,
                start_date=start_str, end_date=end_str, adjust="qfq")
            return [{"date": str(row["时间"]), "open": float(row["开盘"]), "high": float(row["最高"]),
                     "low": float(row["最低"]), "close": float(row["收盘"]), "volume": float(row["成交量"])}
                    for _, row in df.iterrows()]
        period_map = {"weekly": "week", "monthly": "month"}
        ak_period = period_map.get(period, "daily")
        df = ak.stock_zh_a_hist(symbol=code, period=ak_period,
            start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
        return [{"date": str(row["日期"]), "open": float(row["开盘"]), "high": float(row["最高"]),
                 "low": float(row["最低"]), "close": float(row["收盘"]), "volume": float(row["成交量"])}
                for _, row in df.iterrows()]

    async def search_symbol(self, keyword: str) -> list[dict]:
        return await asyncio.to_thread(self._search_symbol, keyword)

    def _search_symbol(self, keyword: str) -> list[dict]:
        df = ak.stock_zh_a_spot_em()
        mask = df["名称"].str.contains(keyword) | df["代码"].str.contains(keyword)
        return [{"code": row["代码"], "name": row["名称"]} for _, row in df[mask].head(20).iterrows()]

    async def get_index_quotes(self) -> list[dict]:
        return await asyncio.to_thread(self._get_index_quotes)

    def _get_index_quotes(self) -> list[dict]:
        df = ak.stock_zh_index_spot_em()
        targets = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指"}
        result = []
        for _, row in df.iterrows():
            code = str(row["代码"])
            if code in targets:
                result.append({
                    "code": code, "name": row["名称"],
                    "price": float(row["最新价"]), "change": float(row["涨跌额"]),
                    "change_pct": float(row["涨跌幅"]),
                })
        return result

    async def get_market_heat(self) -> dict:
        return await asyncio.to_thread(self._get_market_heat)

    def _get_market_heat(self) -> dict:
        df = ak.stock_zh_a_spot_em()
        up_count = int((df["涨跌幅"] > 0).sum())
        down_count = int((df["涨跌幅"] < 0).sum())
        flat_count = int((df["涨跌幅"] == 0).sum())
        total_volume = round(float(df["成交额"].sum()) / 1e8, 2)
        north_flow = 0.0
        try:
            north_df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            if len(north_df) > 0:
                north_flow = float(north_df.iloc[-1]["当日净流入"])
        except Exception:
            pass
        return {
            "up_count": up_count, "down_count": down_count, "flat_count": flat_count,
            "limit_up": 0, "limit_down": 0,
            "total_volume": total_volume, "north_flow": north_flow,
        }

    async def get_sectors(self, sector_type: str = "industry") -> list[dict]:
        return await asyncio.to_thread(self._get_sectors, sector_type)

    def _get_sectors(self, sector_type: str) -> list[dict]:
        fn = ak.stock_board_industry_spot_em if sector_type == "industry" else ak.stock_board_concept_spot_em
        df = fn()
        result = []
        for _, row in df.iterrows():
            result.append({
                "name": row["板块名称"],
                "change_pct": float(row["涨跌幅"]),
                "lead_stock": str(row.get("领涨股票", "")),
                "stock_count": int(row.get("公司家数", 0)),
            })
        return result

    async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]:
        return await asyncio.to_thread(self._get_rankings, rank_type, limit)

    def _get_rankings(self, rank_type: str, limit: int) -> list[dict]:
        df = ak.stock_zh_a_spot_em()
        ascending = rank_type != "up"
        df_sorted = df.sort_values("涨跌幅", ascending=ascending).head(limit)
        result = []
        for _, row in df_sorted.iterrows():
            result.append({
                "code": row["代码"], "name": row["名称"],
                "price": float(row["最新价"]), "change_pct": float(row["涨跌幅"]),
            })
        return result

    async def get_intraday(self, code: str) -> list[dict]:
        return await asyncio.to_thread(self._get_intraday, code)

    def _get_intraday(self, code: str) -> list[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        df = ak.stock_zh_a_hist_min_em(symbol=code, period="1",
            start_date=f"{today} 09:30:00", end_date=f"{today} 15:00:00", adjust="")
        result = []
        for _, row in df.iterrows():
            result.append({
                "time": str(row["时间"]),
                "price": float(row["收盘"]),
                "avg_price": float(row["收盘"]),
                "volume": float(row["成交量"]),
            })
        return result