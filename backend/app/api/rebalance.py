from fastapi import APIRouter, HTTPException
from app.schemas.rebalance import RebalanceResult, PositionAdvice
from openai import OpenAI
from app.core.config import settings

router = APIRouter(prefix="/rebalance")


@router.post("/advice", response_model=RebalanceResult)
async def get_rebalance_advice(body: dict):
    """AI 提供仓位调整建议"""
    positions = body.get("positions", [])
    advice = []

    if settings.openai_api_key and positions:
        try:
            pos_text = "\n".join(
                f"- {p.get('name','')}({p.get('code','')}): 持仓{p.get('quantity',0)}股, 成本{p.get('cost_price',0)}元"
                for p in positions
            )
            prompt = f"""你是一个A股仓位管理顾问。根据以下持仓给出调仓建议（每只股票给出：买入/持有/减仓/加仓，并说明理由）。返回JSON格式：
{{"advice":[{{"code":"代码","name":"名称","action":"hold/buy_more/reduce/add","suggested_weight":权重百分比,"reason":"理由"}}],"summary":"总体建议100字"}}

持仓：
{pos_text}"""

            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600, temperature=0.7,
            )
            import json
            text = resp.choices[0].message.content or "{}"
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(text)
            advice = [PositionAdvice(**a) for a in data.get("advice", [])]
            summary = data.get("summary", "")
        except Exception as e:
            summary = f"AI 分析失败: {str(e)}"
    else:
        summary = "未配置 AI 或持仓为空"

    if not advice:
        summary = summary or "暂无调仓建议"

    return RebalanceResult(advice=advice, summary=summary)
