from fastapi import APIRouter, HTTPException
import logging
from datetime import date, timedelta
import requests, re
from openai import OpenAI
from app.core.config import settings
from app.core.sina_utils import sina_quote
from app.schemas.review import DailyReview, StockReview, WeeklyReview

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}
router = APIRouter(prefix="/review")



def _market_snapshot() -> str:
    """获取市场快照作为复盘上下文"""
    snapshot = []
    indices = [("s_sh000001", "上证"), ("s_sz399001", "深证"), ("s_sz399006", "创业板")]
    try:
        for idx, nm in indices:
            resp = requests.get(f"http://hq.sinajs.cn/list={idx}", headers=SINA_HEADERS, timeout=5)
            resp.encoding = "gbk"
            m = re.search(r'"([^"]*)"', resp.text)
            if m:
                parts = m.group(1).split(",")
                if len(parts) >= 4:
                    price = parts[3]
                    prev = parts[2]
                    chg = (float(price) - float(prev)) / float(prev) * 100 if prev and float(prev) > 0 else 0
                    snapshot.append(f"{nm}: {price} ({chg:+.2f}%)")
    except Exception:
        pass
    return "\n".join(snapshot)


@router.post("/daily", response_model=DailyReview)
async def generate_daily_review():
    today = date.today().isoformat()
    snapshot = _market_snapshot()

    if not settings.openai_api_key:
        return DailyReview(
            date=today, content="未配置 OpenAI API Key",
            market_summary="", hot_sectors=[], risk_alert=""
        )

    prompt = f"""你是一个A股复盘分析师。请根据今日市场数据做简要复盘（200字以内），包括：
1. 大盘概况 2. 热点板块 3. 风险提示

返回JSON格式：{{"market_summary":"大盘概况50字","hot_sectors":["板块1","板块2"],"risk_alert":"风险提示30字"}}

今日数据：
{snapshot}"""

    try:
        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400, temperature=0.7,
        )
        import json
        text = resp.choices[0].message.content or "{}"
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(text)
        return DailyReview(
            date=today,
            content=f"复盘日期：{today}\n{snapshot}\n\n{data.get('market_summary','')}",
            market_summary=data.get("market_summary", ""),
            hot_sectors=data.get("hot_sectors", []),
            risk_alert=data.get("risk_alert", ""),
        )
    except Exception as e:
        return DailyReview(date=today, content=f"生成失败: {e}", market_summary="", hot_sectors=[], risk_alert="")


@router.post("/stock/{code}", response_model=StockReview)
async def generate_stock_review(code: str):
    name = sina_quote(code)["name"]

    if not settings.openai_api_key:
        return StockReview(code=code, name=name, content="未配置 AI", technical_view="", fundamental_view="", overall_rating="")

    # 获取K线数据
    kline_data = []
    try:
        market = "sh" if code.startswith(("6", "9")) else "sz"
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,30,qfq"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        days = data.get("data", {}).get(f"{market}{code}", {}).get("day", []) or \
               data.get("data", {}).get(f"{market}{code}", {}).get("qfqday", [])
        for d in days[-10:]:
            kline_data.append(f"{d[0]}: O{d[1]} C{d[2]} H{d[3]} L{d[4]} V{d[5]}")
    except Exception:
        pass

    prompt = f"""你是一个A股研究员。请为{name}({code})生成一份简要调研报告（200字以内），包括：
1. 技术面观点 2. 基本面看法 3. 综合评级（强烈推荐/推荐/中性/回避）

返回JSON: {{"technical_view":"技术面50字","fundamental_view":"基本面50字","overall_rating":"评级","content":"完整报告"}}

近10日K线：
{chr(10).join(kline_data[-10:])}"""

    try:
        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400, temperature=0.7,
        )
        import json
        text = resp.choices[0].message.content or "{}"
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(text)
        return StockReview(
            code=code, name=name,
            content=data.get("content", ""),
            technical_view=data.get("technical_view", ""),
            fundamental_view=data.get("fundamental_view", ""),
            overall_rating=data.get("overall_rating", "中性"),
        )
    except Exception as e:
        return StockReview(code=code, name=name, content=f"生成失败: {e}", technical_view="", fundamental_view="", overall_rating="")


@router.post("/weekly", response_model=WeeklyReview)
async def generate_weekly_review():
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    week_end = today.isoformat()
    snapshot = _market_snapshot()

    if not settings.openai_api_key:
        return WeeklyReview(week_range=f"{week_start}~{week_end}", content="未配置 AI", weekly_return=0, key_events=[])

    prompt = f"""你是一个A股周报分析师。请根据本周市场数据写一份周度总结（150字以内），包括关键事件。

返回JSON: {{"content":"周度总结","key_events":["事件1","事件2"]}}

市场快照: {snapshot}"""

    try:
        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.7,
        )
        import json
        text = resp.choices[0].message.content or "{}"
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(text)
        return WeeklyReview(
            week_range=f"{week_start}~{week_end}",
            content=data.get("content", ""),
            weekly_return=0,
            key_events=data.get("key_events", []),
        )
    except Exception as e:
        return WeeklyReview(week_range=f"{week_start}~{week_end}", content=f"生成失败: {e}", weekly_return=0, key_events=[])