import requests, re
import math
from datetime import date, timedelta

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}

def _prefix(code: str) -> str:
    if code.startswith(("8", "4")) or (len(code) == 6 and code.startswith("92")):
        return "bj" + code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code

def _sina_name_price(code: str):
    url = f"http://hq.sinajs.cn/list={_prefix(code)}"
    resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
    resp.encoding = "gbk"
    m = re.search(r'"([^"]*)"', resp.text)
    if not m:
        return code, 0.0
    parts = m.group(1).split(",")
    price = float(parts[3])
    if code.startswith(("8", "4")) or (len(code) == 6 and code.startswith("92")):
        change = float(parts[2])
        price = float(parts[3])
    return parts[0], price


def _sma(values, n):
    """简单移动平均"""
    result = []
    for i in range(len(values)):
        if i < n - 1:
            result.append(None)
        else:
            result.append(sum(values[i-n+1:i+1]) / n)
    return result


def _ema(values, n):
    """指数移动平均"""
    result = []
    k = 2 / (n + 1)
    for i, v in enumerate(values):
        if i == 0:
            result.append(v)
        else:
            result.append(v * k + result[-1] * (1 - k))
    return result


def calc_all_indicators(klines: list[dict]) -> dict:
    """传入K线数据 [{date,open,high,low,close,volume}...] 返回完整指标"""
    n = len(klines)
    if n < 60:
        return {}

    dates = [k["date"] for k in klines]
    opens = [k["open"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    closes = [k["close"] for k in klines]
    volumes = [k["volume"] for k in klines]

    # MA
    ma5 = _sma(closes, 5)
    ma10 = _sma(closes, 10)
    ma20 = _sma(closes, 20)
    ma60 = _sma(closes, 60)

    # BOLL (20-period)
    boll_mid = ma20[:]
    boll_up = []
    boll_dn = []
    for i in range(n):
        if i < 19:
            boll_up.append(None)
            boll_dn.append(None)
        else:
            window = closes[i-19:i+1]
            mean = sum(window) / 20
            variance = sum((x - mean) ** 2 for x in window) / 20
            std = math.sqrt(variance)
            boll_up.append(mean + 2 * std)
            boll_dn.append(mean - 2 * std)

    # MACD (12, 26, 9)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif = [ema12[i] - ema26[i] for i in range(n)]
    dea = _ema(dif, 9)
    macd_bar = [2 * (dif[i] - dea[i]) for i in range(n)]

    # RSI (6, 12, 24)
    def _rsi(values, period):
        result = []
        gains = []
        losses = []
        for i in range(1, len(values)):
            diff = values[i] - values[i-1]
            gains.append(diff if diff > 0 else 0)
            losses.append(-diff if diff < 0 else 0)

        for i in range(len(values)):
            if i < period:
                result.append(None)
            else:
                avg_gain = sum(gains[i-period:i]) / period
                avg_loss = sum(losses[i-period:i]) / period
                if avg_loss == 0:
                    result.append(100.0)
                else:
                    rs = avg_gain / avg_loss
                    result.append(100 - 100 / (1 + rs))
        return result

    rsi6 = _rsi(closes, 6)
    rsi12 = _rsi(closes, 12)
    rsi24 = _rsi(closes, 24)

    # KDJ (9, 3, 3)
    kdj_k = []
    kdj_d = []
    kdj_j = []
    prev_k = 50.0
    prev_d = 50.0
    for i in range(n):
        if i < 8:
            kdj_k.append(None)
            kdj_d.append(None)
            kdj_j.append(None)
        else:
            h9 = max(highs[i-8:i+1])
            l9 = min(lows[i-8:i+1])
            rsv = (closes[i] - l9) / (h9 - l9) * 100 if h9 != l9 else 50
            k = 2/3 * prev_k + 1/3 * rsv
            d = 2/3 * prev_d + 1/3 * k
            j = 3 * k - 2 * d
            kdj_k.append(round(k, 2))
            kdj_d.append(round(d, 2))
            kdj_j.append(round(j, 2))
            prev_k, prev_d = k, d

    return {
        "dates": dates, "open": opens, "high": highs, "low": lows,
        "close": closes, "volume": volumes,
        "ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60,
        "boll_up": boll_up, "boll_mid": boll_mid, "boll_dn": boll_dn,
        "macd_dif": dif, "macd_dea": dea, "macd_bar": macd_bar,
        "rsi6": rsi6, "rsi12": rsi12, "rsi24": rsi24,
        "kdj_k": kdj_k, "kdj_d": kdj_d, "kdj_j": kdj_j,
    }


def detect_anomalies(klines: list[dict]) -> list[dict]:
    """量价异动检测"""
    n = len(klines)
    if n < 20:
        return []

    closes = [k["close"] for k in klines]
    volumes = [k["volume"] for k in klines]
    opens = [k["open"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]

    anomalies = []
    for i in range(20, n):
        avg_vol = sum(volumes[i-20:i]) / 20
        vol = volumes[i]
        change_pct = (closes[i] - closes[i-1]) / closes[i-1] * 100
        body_ratio = abs(closes[i] - opens[i]) / opens[i] if opens[i] > 0 else 0
        date_str = klines[i]["date"]

        if vol > avg_vol * 2 and change_pct > 5:
            anomalies.append({
                "date": date_str, "type": "放量长阳",
                "description": f"成交量{vol/avg_vol:.1f}倍均量，涨幅{change_pct:.1f}%，资金介入明显"
            })
        elif vol > avg_vol * 2 and change_pct < -5:
            anomalies.append({
                "date": date_str, "type": "放量长阴",
                "description": f"成交量{vol/avg_vol:.1f}倍均量，跌幅{abs(change_pct):.1f}%，抛压沉重"
            })
        elif vol < avg_vol * 0.5 and body_ratio < 0.003:
            anomalies.append({
                "date": date_str, "type": "缩量十字星",
                "description": f"成交量萎缩至{vol/avg_vol:.1f}倍均量，变盘信号"
            })

    return anomalies[-5:]  # 最近5条


def calc_score(klines: list[dict], indicators: dict) -> dict:
    """量化打分 0-100"""
    n = len(klines)
    if n < 60:
        return {"trend": 0, "momentum": 0, "volatility": 0, "volume_score": 0, "total": 0, "description": "数据不足"}

    close = klines[-1]["close"]
    ma5_val = indicators["ma5"][-1]
    ma10_val = indicators["ma10"][-1]
    ma20_val = indicators["ma20"][-1]
    ma60_val = indicators["ma60"][-1]
    rsi6_val = indicators["rsi6"][-1] or 50
    rsi12_val = indicators["rsi12"][-1] or 50
    dif_val = indicators["macd_dif"][-1]
    dea_val = indicators["macd_dea"][-1]

    # 趋势 (0-20): MA多头排列
    trend = 0
    if ma5_val and ma10_val and ma20_val and ma60_val:
        if ma5_val > ma10_val > ma20_val > ma60_val and close > ma5_val:
            trend = 20
        elif close > ma20_val and ma5_val > ma10_val:
            trend = 15
        elif close > ma20_val:
            trend = 10
        elif close > ma60_val:
            trend = 5

    # 动量 (0-20): RSI + MACD
    momentum = 0
    if rsi6_val and rsi12_val:
        avg_rsi = (rsi6_val + rsi12_val) / 2
        if 40 <= avg_rsi <= 70:
            momentum += 10
        elif 30 <= avg_rsi <= 80:
            momentum += 5
    if dif_val > dea_val:
        momentum += 5
    if dif_val > 0:
        momentum += 5

    # 波动 (0-20): BOLL位置
    volatility = 10
    if indicators["boll_up"][-1] and indicators["boll_mid"][-1] and indicators["boll_dn"][-1]:
        up = indicators["boll_up"][-1]
        mid = indicators["boll_mid"][-1]
        dn = indicators["boll_dn"][-1]
        if close > up:
            volatility = 5  # 超买
        elif close > mid:
            volatility = 15
        elif close > dn:
            volatility = 10
        else:
            volatility = 5  # 超卖

    # 量能 (0-20)
    volume_score = 10
    vols = indicators["volume"][-20:]
    if vols:
        avg_vol = sum(v for v in vols if v) / len([v for v in vols if v])
        last_vol = indicators["volume"][-1]
        last_change = (klines[-1]["close"] - klines[-2]["close"]) / klines[-2]["close"] * 100
        if last_vol > avg_vol * 1.5 and last_change > 0:
            volume_score = 20
        elif last_vol > avg_vol * 1.5 and last_change < 0:
            volume_score = 5
        elif last_vol < avg_vol * 0.5:
            volume_score = 10

    total = trend + momentum + volatility + volume_score

    desc_parts = []
    if trend >= 15:
        desc_parts.append("趋势偏多")
    elif trend >= 10:
        desc_parts.append("趋势震荡偏多")
    else:
        desc_parts.append("趋势偏弱")

    if momentum >= 15:
        desc_parts.append("动能充足")
    elif momentum >= 10:
        desc_parts.append("动能一般")
    else:
        desc_parts.append("动能不足")

    if total >= 70:
        desc_parts.append("综合偏强")
    elif total >= 40:
        desc_parts.append("综合中性")
    else:
        desc_parts.append("综合偏弱")

    return {"trend": trend, "momentum": momentum, "volatility": volatility,
            "volume_score": volume_score, "total": total,
            "description": "；".join(desc_parts)}


def get_indicators(code: str, period: str = "daily") -> dict:
    """获取完整指标数据"""
    from app.adapters import get_adapter
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365 if period == "daily" else 730)
    klines = adapter.get_kline(code, start, end, period)
    if isinstance(klines, list) and len(klines) > 0:
        # convert from async wrapper if needed
        pass
    return calc_all_indicators(klines)


def get_anomalies(code: str) -> dict:
    """获取异动"""
    from app.adapters import get_adapter
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365)
    klines = adapter.get_kline(code, start, end, "daily")
    name, _ = _sina_name_price(code)
    anomalies = detect_anomalies(klines)
    return {"code": code, "name": name, "anomalies": anomalies}


def get_score(code: str) -> dict:
    """获取打分"""
    from app.adapters import get_adapter
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365)
    klines = adapter.get_kline(code, start, end, "daily")
    indicators = calc_all_indicators(klines)
    name, _ = _sina_name_price(code)
    score = calc_score(klines, indicators)
    return {"code": code, "name": name, **score}
