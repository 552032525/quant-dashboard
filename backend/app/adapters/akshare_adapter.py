import asyncio
import akshare as ak
from datetime import date
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
        df = ak.stock_zh_a_hist(symbol=code, period=period,
            start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
        return [{"date": row["日期"], "open": float(row["开盘"]), "high": float(row["最高"]),
                 "low": float(row["最低"]), "close": float(row["收盘"]), "volume": float(row["成交量"])}
                for _, row in df.iterrows()]

    async def search_symbol(self, keyword: str) -> list[dict]:
        return await asyncio.to_thread(self._search_symbol, keyword)

    def _search_symbol(self, keyword: str) -> list[dict]:
        df = ak.stock_zh_a_spot_em()
        mask = df["名称"].str.contains(keyword) | df["代码"].str.contains(keyword)
        return [{"code": row["代码"], "name": row["名称"]} for _, row in df[mask].head(20).iterrows()]
