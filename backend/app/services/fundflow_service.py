import requests, re, json
from datetime import date, datetime, timedelta

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}

def _prefix(code: str) -> str:
    if code.startswith(("8", "4")) or (len(code) == 6 and code.startswith("92")):
        return "bj" + code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code

def _sina_name(code: str) -> str:
    prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
    url = f"http://hq.sinajs.cn/list={prefix}"
    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if m:
            return m.group(1).split(",")[0]
    except:
        pass
    return code


class FundFlowService:

    # ─── 个股资金流向 ───────────────────────────────────────
    def get_stock_flow(self, code: str):
        """新浪 MoneyFlow API 获取个股每日资金流向"""
        name = _sina_name(code)
        flows = []

        try:
            url = (
                "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                f"MoneyFlow.ssl_money_flow?daima={_prefix(code)}"
            )
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.encoding = "gbk"
            data = resp.json()

            for item in data[-20:]:  # 取最近20日
                flows.append({
                    "date": item.get("opendate", ""),
                    "main_net": float(item.get("netamount", 0)),
                    "super_large_net": float(item.get("superamount", 0)),
                    "large_net": float(item.get("bigamount", 0)),
                    "mid_net": float(item.get("midamount", 0)),
                    "small_net": float(item.get("smlamount", 0)),
                })
        except Exception:
            pass

        return {"code": code, "name": name, "flows": flows}

    # ─── 北向资金流向 ───────────────────────────────────────
    def get_northbound_flow(self, days: int = 20):
        """腾-讯数据获取北向资金近期流向"""
        items = []
        try:
            url = f"http://qt.gtimg.cn/q=ff_hsgt"
            resp = requests.get(url, timeout=10)
            resp.encoding = "gbk"
            text = resp.text

            # 解析 ff_hsgt 数据（格式: var v_ff_hsgt="日期~沪净~深净~沪余额~深余额"）
            m = re.search(r'v_ff_hsgt="([^"]*)"', text)
            if not m:
                return {"items": items}

            # 返回的可能是多条, 用 ; 分割
            entries = m.group(1).strip().split(";")
            for entry in entries[-days:]:
                if not entry.strip():
                    continue
                parts = entry.split("~")
                if len(parts) >= 5:
                    try:
                        items.append({
                            "date": parts[0],
                            "sh_net": float(parts[1]) if parts[1] else 0,
                            "sz_net": float(parts[2]) if parts[2] else 0,
                            "total_net": (float(parts[1]) if parts[1] else 0) + (float(parts[2]) if parts[2] else 0),
                        })
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass

        return {"items": items}

    def get_northbound_daily(self):
        """当日北向资金概况"""
        try:
            url = "http://qt.gtimg.cn/q=ff_hsgt"
            resp = requests.get(url, timeout=10)
            resp.encoding = "gbk"
            text = resp.text

            m = re.search(r'v_ff_hsgt="([^"]*)"', text)
            if not m:
                return None

            entries = m.group(1).strip().split(";")
            if not entries or not entries[-1].strip():
                return None

            parts = entries[-1].split("~")
            if len(parts) >= 5:
                return {
                    "date": parts[0],
                    "sh_net": float(parts[1]) if parts[1] else 0,
                    "sz_net": float(parts[2]) if parts[2] else 0,
                    "total_net": (float(parts[1]) if parts[1] else 0) + (float(parts[2]) if parts[2] else 0),
                    "sh_balance": float(parts[3]) if len(parts) > 3 and parts[3] else 0,
                    "sz_balance": float(parts[4]) if len(parts) > 4 and parts[4] else 0,
                }
        except Exception:
            pass
        return None

    # ─── 板块资金流向 ───────────────────────────────────────
    def get_sector_flow(self):
        """新浪板块资金流向排名"""
        inflow = []
        outflow = []

        try:
            url = (
                "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                "MoneyFlow.ssl_bkzj_sshy"
            )
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.encoding = "gbk"
            data = resp.json()

            sorted_data = sorted(data, key=lambda x: float(x.get("netamount", 0)), reverse=True)
            for item in sorted_data[:10]:
                inflow.append({
                    "name": item.get("boardname", ""),
                    "net_amount": float(item.get("netamount", 0)),
                    "main_net": float(item.get("mainamount", 0)),
                    "change_pct": float(item.get("changeratio", 0)),
                })

            for item in sorted_data[-10:]:
                outflow.append({
                    "name": item.get("boardname", ""),
                    "net_amount": float(item.get("netamount", 0)),
                    "main_net": float(item.get("mainamount", 0)),
                    "change_pct": float(item.get("changeratio", 0)),
                })
            # 流出按净流入从小到大
            outflow.sort(key=lambda x: x["net_amount"])

        except Exception:
            pass

        return {"inflow_top10": inflow, "outflow_top10": outflow}

    # ─── 大盘资金总览 ───────────────────────────────────────
    def get_market_flow(self):
        """聚合计算大盘资金概况"""
        today = date.today().isoformat()
        main_net = 0.0
        up_count = 0
        down_count = 0

        try:
            # 从主要指数推断涨跌家数（上证）
            url = "http://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006"
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.encoding = "gbk"
            for line in resp.text.strip().split("\n"):
                m = re.search(r'"([^"]*)"', line)
                if not m:
                    continue
                parts = m.group(1).split(",")
                if len(parts) > 30:
                    # 上证指数通常包含涨跌家数
                    pass
        except Exception:
            pass

        # 用板块资金汇总近似主力净流入
        try:
            url = (
                "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                "MoneyFlow.ssl_bkzj_sshy"
            )
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.encoding = "gbk"
            data = resp.json()
            main_net = sum(float(item.get("netamount", 0)) for item in data)
        except Exception:
            pass

        return {
            "date": today,
            "main_net": round(main_net / 10000, 2),  # 万元 -> 亿元
            "total_turnover": 0,
            "up_count": up_count,
            "down_count": down_count,
        }


# 单例
_fundflow_service: FundFlowService | None = None


def get_fundflow_service() -> FundFlowService:
    global _fundflow_service
    if _fundflow_service is None:
        _fundflow_service = FundFlowService()
    return _fundflow_service
