from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from datetime import date, timedelta
from app.core.config import settings
from app.adapters import get_adapter
from app.schemas.ai import AnalyzeRequest, ChatRequest, AIResponse

router = APIRouter(prefix="/ai")

ANALYZE_PROMPT = (
    "你是一个量化交易分析师。以下是 {name}({code}) 最近 {days} 日的行情数据：\n\n"
    "{data}\n\n"
    "请从技术面角度给出简要分析：趋势判断、关键支撑/压力位、风险提示。200 字以内。"
)

def _client():
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

@router.post("/analyze", response_model=AIResponse)
async def analyze(req: AnalyzeRequest):
    adapter = get_adapter()
    quote = adapter.get_realtime_quote(req.code)
    klines = adapter.get_kline(
        req.code, date.today() - timedelta(days=req.days), date.today()
    )
    recent = klines[-30:]
    data_text = "\n".join(
        f"{k['date']}: O{k['open']:.2f} H{k['high']:.2f} L{k['low']:.2f} C{k['close']:.2f}"
        for k in recent
    )
    prompt = ANALYZE_PROMPT.format(
        name=quote["name"], code=req.code, days=req.days, data=data_text
    )
    response = await _client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return AIResponse(content=response.choices[0].message.content or "")

@router.post("/chat", response_model=AIResponse)
async def chat(req: ChatRequest):
    messages = [{"role": "user", "content": req.message}]
    if req.symbol_code:
        quote = get_adapter().get_realtime_quote(req.symbol_code)
        context = (
            f"当前分析标的: {quote['name']}({req.symbol_code})，"
            f"现价 {quote['price']}，涨跌幅 {quote['change_pct']}%"
        )
        messages.insert(0, {"role": "system", "content": context})
    response = await _client().chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=600,
    )
    return AIResponse(content=response.choices[0].message.content or "")
