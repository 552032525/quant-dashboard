import re
import json
import requests
from datetime import date, datetime
from app.adapters.base import DataSourceAdapter

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}
SINA_QUOTE = "http://hq.sinajs.cn/list={codes}"
SINA_SEARCH = "http://suggest3.sinajs.cn/suggest/type=111&key={kw}&name=sdata"
SINA_RANK = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num={limit}&sort=changepercent&asc={asc}&node=hs_a"
TENCENT_KLINE = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix},{period},{start},{end},{count},qfq"
TENCENT_MINUTE = "http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={prefix},m{minute},,{count}"

SECTOR_ETFS = [
    ("512880", "证券"), ("512690", "白酒"), ("512170", "医疗"),
    ("515050", "5G通信"), ("515700", "新能源车"), ("512760", "芯片"),
    ("159915", "创业板"), ("510050", "上证50"), ("510300", "沪深300"),
    ("510500", "中证500"), ("512100", "中证1000"), ("588000", "科创50"),
    ("512200", "房地产"), ("516970", "基建"), ("159865", "养殖"),
    ("159766", "旅游"), ("515880", "通信"), ("516510", "云计算"),
    ("516160", "新能源"), ("515790", "光伏"), ("159611", "电力"),
    ("512660", "军工"), ("512980", "传媒"), ("515210", "钢铁"),
    ("516110", "汽车"), ("159869", "游戏"), ("512480", "半导体"),
    ("515220", "煤炭"), ("516880", "建材"), ("516780", "稀土"),
]


class WebAdapter(DataSourceAdapter):

    # ── 实时行情 ──

    async def get_realtime_quote(self, code: str) -> dict:
        prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
        url = SINA_QUOTE.format(codes=prefix)
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        text = resp.text
        m = re.search(r'"([^"]*)"', text)
        if not m:
            raise ValueError(f"未找到股票: {code}")
        parts = m.group(1).split(",")
        if len(parts) < 32:
            raise ValueError(f"数据不完整: {code}")
        price = float(parts[3])
        pre_close = float(parts[2])
        change = price - pre_close
        change_pct = round(change / pre_close * 100, 2) if pre_close else 0
        return {
            "code": code, "name": parts[0],
            "price": price, "change": round(change, 3),
            "change_pct": change_pct,
            "volume": int(float(parts[8])), "high": float(parts[4]),
            "low": float(parts[5]), "open": float(parts[1]),
            "pre_close": pre_close,
        }

    # ── K线 ──

    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
        minute_map = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
        if period in minute_map:
            url = TENCENT_MINUTE.format(prefix=prefix, minute=period, count=320)
            resp = requests.get(url, timeout=15)
            data = resp.json()
            rows = data["data"][prefix].get(f"m{period}", [])
            # 腾讯分钟K: [datetime, open, close, high, low, volume, ...]
            return [{"date": r[0], "open": float(r[1]), "close": float(r[2]),
                     "high": float(r[3]), "low": float(r[4]), "volume": float(r[5])}
                    for r in rows if r[0] >= start_date.strftime("%Y%m%d0000")]
        period_map = {"weekly": "week", "monthly": "month"}
        tk_period = period_map.get(period, "day")
        count = 200 if tk_period == "week" else 120 if tk_period == "month" else 365
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        url = TENCENT_KLINE.format(prefix=prefix, period=tk_period, start=start_str, end=end_str, count=count)
        resp = requests.get(url, timeout=15)
        data = resp.json()
        rows = data["data"][prefix].get(f"qfq{tk_period}", [])
        # 腾讯日/周/月K: [date, open, close, high, low, volume]
        return [{"date": r[0], "open": float(r[1]), "close": float(r[2]),
                 "high": float(r[3]), "low": float(r[4]), "volume": float(r[5])}
                for r in rows]

    # ── 搜索 ──

    async def search_symbol(self, keyword: str) -> list[dict]:
        url = SINA_SEARCH.format(kw=keyword)
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        text = resp.text
        # 格式: var sdata="名称,111,shXXXXXX,"
        items = re.findall(r'([\u4e00-\u9fffA-Za-z]+),11[01],(s[hz]\d{6}),', text)
        results = []
        seen = set()
        for name, raw in items:
            code = raw[2:]
            if code not in seen and (code.startswith(("6", "0", "3", "9"))):
                seen.add(code)
                results.append({"code": code, "name": name})
            if len(results) >= 10:
                break
        return results

    # ── 指数行情 ──

    async def get_index_quotes(self) -> list[dict]:
        codes = "s_sh000001,s_sz399001,s_sz399006"
        url = SINA_QUOTE.format(codes=codes)
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        code_map = {"sh000001": "000001", "sz399001": "399001", "sz399006": "399006"}
        result = []
        for line in resp.text.strip().split("\n"):
            m = re.search(r's_(\w+?)="([^"]*)"', line)
            if not m:
                continue
            raw_code = m.group(1)
            code = code_map.get(raw_code, raw_code)
            parts = m.group(2).split(",")
            if len(parts) < 5:
                continue
            result.append({"code": code, "name": parts[0], "price": float(parts[1]),
                           "change": float(parts[2]), "change_pct": float(parts[3])})
        return result

    # ── 市场热度 ──

    async def get_market_heat(self) -> dict:
        try:
            up_resp = requests.get(SINA_RANK.format(limit=1, asc="0"), timeout=10)
            up_resp.encoding = "utf-8"
            up_data = up_resp.json()
            up_max_pct = float(up_data[0]["changepercent"]) if up_data else 0.0
            down_resp = requests.get(SINA_RANK.format(limit=1, asc="1"), timeout=10)
            down_resp.encoding = "utf-8"
            down_data = down_resp.json()
            down_max_pct = float(down_data[0]["changepercent"]) if down_data else 0.0
            return {
                "up_count": 0, "down_count": 0, "flat_count": 0,
                "limit_up": 10 if up_max_pct > 9.5 else 0,
                "limit_down": 10 if down_max_pct < -9.5 else 0,
                "total_volume": 0.0, "north_flow": 0.0,
            }
        except Exception:
            return {"up_count": 0, "down_count": 0, "flat_count": 0,
                    "limit_up": 0, "limit_down": 0, "total_volume": 0, "north_flow": 0}

    # ── 板块（ETF代理）──

    async def get_sectors(self, sector_type: str = "industry") -> list[dict]:
        codes = ",".join(
            (f"sh{e[0]}" if e[0].startswith(("5", "6")) else f"sz{e[0]}") for e in SECTOR_ETFS
        )
        url = SINA_QUOTE.format(codes=codes)
        resp = requests.get(url, headers=SINA_HEADERS, timeout=15)
        resp.encoding = "gbk"
        etf_map = dict(SECTOR_ETFS)
        result = []
        for line in resp.text.strip().split("\n"):
            m = re.search(r'([shz]{2}\d+)="([^"]*)"', line)
            if not m:
                continue
            code = m.group(1)[2:]
            parts = m.group(2).split(",")
            if len(parts) < 4:
                continue
            price = float(parts[3])
            pre_close = float(parts[2])
            change_pct = round((price - pre_close) / pre_close * 100, 2) if pre_close else 0
            result.append({
                "name": etf_map.get(code, parts[0][:4]),
                "change_pct": change_pct,
                "lead_stock": parts[0],
                "stock_count": 0,
            })
        return result

    # ── 涨跌排行 ──

    async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]:
        asc = "1" if rank_type != "up" else "0"
        url = SINA_RANK.format(limit=limit, asc=asc)
        resp = requests.get(url, timeout=15)
        resp.encoding = "utf-8"
        data = resp.json()
        result = []
        for item in data:
            result.append({
                "code": item["code"],
                "name": item["name"],
                "price": float(item["trade"]),
                "change_pct": float(item["changepercent"]),
            })
        return result

    # ── 分时 ──

    async def get_intraday(self, code: str) -> list[dict]:
        prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
        url = f"http://ifzq.gtimg.cn/appstock/app/minute/query?_var=min_data&code={prefix}"
        resp = requests.get(url, timeout=15)
        text = resp.text
        m = re.search(r'min_data=(\{.*\})', text, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(1))
        rows = data["data"][prefix]["data"]["data"]
        result = []
        for row in rows:
            parts = row.split()
            if len(parts) >= 3:
                result.append({
                    "time": parts[0],
                    "price": float(parts[1]),
                    "avg_price": float(parts[1]),
                    "volume": float(parts[2]),
                })
        return result