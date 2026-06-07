import json
from fastapi import APIRouter, HTTPException, Query
from datetime import date, timedelta
from openai import AsyncOpenAI
from app.core.config import settings
from app.adapters import get_adapter
from app.services.technical_service import calc_all_indicators, detect_anomalies, calc_score, _sina_name_price
from app.schemas.technical import IndicatorData, AnomalyResult, ScoreResult, AIReport

router = APIRouter(prefix="/technical")

def _client():
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


@router.get("/indicators/{code}", response_model=IndicatorData)
async def indicators(code: str, period: str = Query("daily")):
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365 if period == "daily" else 730)
    klines = await adapter.get_kline(code, start, end, period)
    result = calc_all_indicators(klines)
    if not result:
        raise HTTPException(500, "指标计算失败，数据不足")
    return result


@router.get("/anomaly/{code}", response_model=AnomalyResult)
async def anomaly(code: str):
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365)
    klines = await adapter.get_kline(code, start, end, "daily")
    name, _ = _sina_name_price(code)
    anomalies = detect_anomalies(klines)
    return {"code": code, "name": name, "anomalies": anomalies}


@router.post("/score", response_model=ScoreResult)
async def score(req: dict):
    code = req.get("code", "")
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365)
    klines = await adapter.get_kline(code, start, end, "daily")
    indicators = calc_all_indicators(klines)
    name, _ = _sina_name_price(code)
    s = calc_score(klines, indicators)
    return {"code": code, "name": name, **s}


REPORT_PROMPT = """你是一个A股技术分析师。以下是 {name}({code}) 的技术指标数据：

近5日均线: MA5={ma5}, MA10={ma10}, MA20={ma20}, MA60={ma60}
现价相对均线位置: {ma_position}
布林带: UP={boll_up}, MID={boll_mid}, DN={boll_dn}
MACD: DIF={dif}, DEA={dea}, BAR={bar}
RSI: RSI6={rsi6}, RSI12={rsi12}, RSI24={rsi24}
KDJ: K={kdj_k}, D={kdj_d}, J={kdj_j}
近期异动: {anomalies}

请从技术面角度给出分析：
1. 形态识别（当前处于什么技术形态）
2. 关键支撑位和压力位
3. 短期操作建议
300字以内。"""


@router.post("/report", response_model=AIReport)
async def report(req: dict):
    code = req.get("code", "")
    adapter = get_adapter()
    end = date.today()
    start = end - timedelta(days=365)
    klines = await adapter.get_kline(code, start, end, "daily")
    indicators = calc_all_indicators(klines)
    name, _ = _sina_name_price(code)
    anomalies = detect_anomalies(klines)

    # Get last valid values
    def last(arr):
        vals = [v for v in arr if v is not None]
        return f"{vals[-1]:.2f}" if vals else "N/A"

    close = klines[-1]["close"]
    ma_positions = []
    for ma_name, ma_arr in [("MA5", indicators["ma5"]), ("MA20", indicators["ma20"]), ("MA60", indicators["ma60"])]:
        vals = [v for v in ma_arr if v is not None]
        if vals:
            ma_pos = "上方" if close > vals[-1] else "下方"
            ma_positions.append(f"{ma_name}{ma_pos}")

    anomaly_text = "无显著异动"
    if anomalies:
        anomaly_text = "; ".join(a["description"] for a in anomalies[:3])

    prompt = REPORT_PROMPT.format(
        name=name, code=code,
        ma5=last(indicators["ma5"]), ma10=last(indicators["ma10"]),
        ma20=last(indicators["ma20"]), ma60=last(indicators["ma60"]),
        ma_position=", ".join(ma_positions),
        boll_up=last(indicators["boll_up"]), boll_mid=last(indicators["boll_mid"]),
        boll_dn=last(indicators["boll_dn"]),
        dif=last(indicators["macd_dif"]), dea=last(indicators["macd_dea"]),
        bar=last(indicators["macd_bar"]),
        rsi6=last(indicators["rsi6"]), rsi12=last(indicators["rsi12"]),
        rsi24=last(indicators["rsi24"]),
        kdj_k=last(indicators["kdj_k"]), kdj_d=last(indicators["kdj_d"]),
        kdj_j=last(indicators["kdj_j"]),
        anomalies=anomaly_text,
    )

    response = await _client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )
    content = response.choices[0].message.content or ""
    summary = content.split("\n")[-1].strip()[:100] if content else ""
    return {"code": code, "name": name, "content": content, "summary": summary}
