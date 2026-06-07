import requests, re, math, json
import logging
from datetime import date, datetime, timedelta
from openai import OpenAI
from app.core.config import settings

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}


def _prefix(code: str) -> str:
    if code.startswith(("8", "4")) or (len(code) == 6 and code.startswith("92")):
        return "bj" + code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code


def _sina_name(code: str) -> str:
    prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if m: return m.group(1).split(",")[0]
    except Exception: pass
    return code


class StockPickService:

    # ─── 多因子选股 ─────────────────────────────────────────
    def screen_stocks(self, filters: dict) -> list[dict]:
        """基于简单规则的多因子筛选"""
        candidates = []
        # 使用预设的候选池（避免全市场扫描）
        pool = [
            ("600519", "贵州茅台"), ("000858", "五粮液"), ("300750", "宁德时代"),
            ("601318", "中国平安"), ("000333", "美的集团"), ("600036", "招商银行"),
            ("002415", "海康威视"), ("600900", "长江电力"), ("601899", "紫金矿业"),
            ("600276", "恒瑞医药"), ("000651", "格力电器"), ("600030", "中信证券"),
            ("002594", "比亚迪"), ("601012", "隆基绿能"), ("300059", "东方财富"),
            ("000725", "京东方A"), ("600809", "山西汾酒"), ("002475", "立讯精密"),
            ("600585", "海螺水泥"), ("000002", "万科A"), ("601166", "兴业银行"),
            ("002714", "牧原股份"), ("600031", "三一重工"), ("300015", "爱尔眼科"),
            ("000568", "泸州老窖"), ("600436", "片仔癀"), ("601888", "中国中免"),
            ("002352", "顺丰控股"), ("300124", "汇川技术"), ("000063", "中兴通讯"),
        ]

        for code, name in pool:
            try:
                score = 0
                pe, pb, roe, mcap = 0, 0, 0, 0

                # 从新浪获取实时数据做简单筛选
                resp = requests.get(
                    f"http://hq.sinajs.cn/list={_prefix(code)}",
                    headers=SINA_HEADERS, timeout=5
                )
                resp.encoding = "gbk"
                m = re.search(r'"([^"]*)"', resp.text)
                if not m: continue
                parts = m.group(1).split(",")
                if len(parts) < 10: continue

                price = float(parts[3]) if parts[3] else 0
                if price <= 0: continue

                change_pct = 0
                if len(parts) > 4 and parts[2]:
                    prev_close = float(parts[2])
                    if prev_close > 0:
                        change_pct = (price - prev_close) / prev_close * 100

                # 趋势得分
                if change_pct > 2: score += 3
                elif change_pct > 0: score += 1
                elif change_pct < -2: score -= 2

                # PE/PB 等需要额外接口，此处用简化的打分逻辑
                # 实际应用中可接入 akshare 的 stock_a_lg_indicator

                candidates.append({
                    "code": code, "name": name,
                    "pe": pe, "pb": pb, "roe": roe,
                    "market_cap": mcap, "score": max(0, score),
                })
            except Exception:
                continue

        # 按得分排序
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:20]

    # ─── 策略回测 ───────────────────────────────────────────
    def run_backtest(self, params: dict) -> dict:
        """简单策略回测引擎"""
        code = params.get("code", "600519")
        strategy = params.get("strategy", "ma_cross")
        start = params.get("start_date", "2025-01-01")
        end = params.get("end_date", "2026-01-01")
        name = _sina_name(code)

        # 获取历史K线
        kline = self._get_kline(code, start, end)
        if len(kline) < 50:
            return {
                "code": code, "name": name, "strategy": strategy,
                "total_return": 0, "annual_return": 0, "max_drawdown": 0,
                "sharpe": 0, "win_rate": 0, "trade_count": 0,
                "trades": [], "nav_curve": [],
            }

        closes = [k["close"] for k in kline]
        dates = [k["date"] for k in kline]

        # 生成信号
        signals = [0] * len(closes)  # 0=持有, 1=买入, -1=卖出
        if strategy == "ma_cross":
            short_n = params.get("ma_short", 5)
            long_n = params.get("ma_long", 20)
            ma_short = self._sma(closes, short_n)
            ma_long = self._sma(closes, long_n)
            for i in range(long_n, len(closes)):
                if ma_short[i] is not None and ma_long[i] is not None:
                    if ma_short[i] > ma_long[i] and ma_short[i-1] <= ma_long[i-1]:
                        signals[i] = 1  # 金叉买入
                    elif ma_short[i] < ma_long[i] and ma_short[i-1] >= ma_long[i-1]:
                        signals[i] = -1  # 死叉卖出
        elif strategy == "momentum":
            mom_days = params.get("momentum_days", 20)
            for i in range(mom_days, len(closes)):
                momentum = (closes[i] - closes[i - mom_days]) / closes[i - mom_days]
                if momentum > 0.05:
                    signals[i] = 1
                elif momentum < -0.03:
                    signals[i] = -1

        # 模拟交易
        trades = []
        nav = [1.0]
        position = 0
        cash = 100000
        peak_nav = 1.0
        max_dd = 0

        for i in range(1, len(closes)):
            if signals[i] == 1 and position == 0:
                shares = int(cash / closes[i] / 100) * 100
                if shares > 0:
                    cost = shares * closes[i] * 1.0003  # 佣金
                    cash -= cost
                    position = shares
                    trades.append({
                        "date": dates[i], "action": "buy",
                        "price": closes[i], "shares": shares, "profit": 0,
                    })
            elif signals[i] == -1 and position > 0:
                proceeds = position * closes[i] * 0.9997
                profit = proceeds - (position * trades[-1]["price"] * 1.0003)
                cash += proceeds
                trades.append({
                    "date": dates[i], "action": "sell",
                    "price": closes[i], "shares": position, "profit": round(profit, 2),
                })
                position = 0

            current_nav = (cash + position * closes[i]) / 100000
            nav.append(current_nav)
            peak_nav = max(peak_nav, current_nav)
            dd = (peak_nav - current_nav) / peak_nav
            max_dd = max(max_dd, dd)

        # 平仓
        if position > 0:
            cash += position * closes[-1] * 0.9997
            position = 0
            nav[-1] = cash / 100000

        total_return = (nav[-1] - 1) * 100
        days = len(closes)
        annual_return = ((nav[-1]) ** (252 / max(days, 1)) - 1) * 100

        # 夏普比率
        returns = [(nav[i] - nav[i-1]) / nav[i-1] for i in range(1, len(nav))]
        avg_ret = sum(returns) / max(len(returns), 1)
        std_ret = math.sqrt(sum((r - avg_ret)**2 for r in returns) / max(len(returns), 1))
        sharpe = (avg_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0

        # 胜率
        wins = sum(1 for t in trades if t["profit"] > 0 and t["action"] == "sell")
        sells = sum(1 for t in trades if t["action"] == "sell")
        win_rate = (wins / sells * 100) if sells > 0 else 0

        nav_curve = [
            {"date": dates[min(i, len(dates)-1)], "nav": round(nav[min(i, len(nav)-1)], 4)}
            for i in range(0, len(dates), max(1, len(dates)//50))
        ]

        return {
            "code": code, "name": name, "strategy": strategy,
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "sharpe": round(sharpe, 2),
            "win_rate": round(win_rate, 1),
            "trade_count": len([t for t in trades if t["action"] == "sell"]),
            "trades": trades[-20:],
            "nav_curve": nav_curve,
        }

    def _get_kline(self, code: str, start: str, end: str) -> list[dict]:
        """获取K线数据"""
        result = []
        try:
            # 使用腾讯API
            market = "sh" if code.startswith(("6", "9")) else "sz"
            url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,320,qfq"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            days = data.get("data", {}).get(f"{market}{code}", {}).get("day", []) or \
                   data.get("data", {}).get(f"{market}{code}", {}).get("qfqday", [])
            for d in days:
                date_str = d[0]
                if start <= date_str <= end:
                    result.append({
                        "date": date_str,
                        "open": float(d[1]), "close": float(d[2]),
                        "high": float(d[3]), "low": float(d[4]),
                        "volume": float(d[5]),
                    })
        except Exception:
            pass
        return result

    def _sma(self, values: list[float], n: int) -> list:
        result = []
        for i in range(len(values)):
            if i < n - 1:
                result.append(None)
            else:
                result.append(sum(values[i-n+1:i+1]) / n)
        return result

    # ─── 策略列表 ───────────────────────────────────────────
    def get_strategies(self) -> list[dict]:
        return [
            {"key": "ma_cross", "name": "双均线交叉", "description": "短期均线上穿长期均线买入，下穿卖出",
             "params": [{"name": "ma_short", "label": "短期均线", "default": 5, "min": 2, "max": 30},
                        {"name": "ma_long", "label": "长期均线", "default": 20, "min": 10, "max": 120}]},
            {"key": "momentum", "name": "动量策略", "description": "基于过去N日收益率决定买卖方向",
             "params": [{"name": "momentum_days", "label": "动量周期", "default": 20, "min": 5, "max": 60}]},
            {"key": "grid", "name": "网格交易", "description": "在价格区间内等分网格，低买高卖",
             "params": [{"name": "grid_count", "label": "网格数量", "default": 10, "min": 5, "max": 50}]},
        ]


_stockpick_service: StockPickService | None = None


def get_stockpick_service() -> StockPickService:
    global _stockpick_service
    if _stockpick_service is None:
        _stockpick_service = StockPickService()
    return _stockpick_service