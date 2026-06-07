import json
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.financial_service import get_financial_service
from app.schemas.fundamental import (
    FinancialOverview, ValuationData, RiskScreening, HolderData,
    AIReport, AIResponse, CompareRequest, CompareResult,
)

router = APIRouter(prefix="/fundamental")
fs = get_financial_service()

def _client():
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


@router.get("/overview/{code}", response_model=FinancialOverview)
async def overview(code: str):
    try:
        return fs.get_financial_overview(code)
    except Exception as e:
        raise HTTPException(500, f"财务数据获取失败: {e}")


@router.get("/valuation/{code}", response_model=ValuationData)
async def valuation(code: str):
    try:
        return fs.get_valuation(code)
    except Exception as e:
        raise HTTPException(500, f"估值数据获取失败: {e}")


@router.get("/risk/{code}", response_model=RiskScreening)
async def risk(code: str):
    try:
        return fs.get_risk(code)
    except Exception as e:
        raise HTTPException(500, f"风险数据获取失败: {e}")


@router.get("/holders/{code}", response_model=HolderData)
async def holders(code: str):
    try:
        return fs.get_holders(code)
    except Exception as e:
        raise HTTPException(500, f"股东数据获取失败: {e}")


REPORT_PROMPT = """你是一个专业的A股基本面分析师。请基于以下财务数据，生成一份结构化的基本面研报。

股票: {name}({code})

近5年财务数据（部分）:
{financial_data}

估值数据:
P/E: {pe}, P/B: {pb}, P/S: {ps}, ROE: {roe}%, 股息率: {dividend_yield}%

风险筛查:
资产负债率: {debt_ratio}%, 质押比例: {pledge_ratio}%, 商誉占比: {goodwill_ratio}%
现金流健康度: {cash_flow_health}
风险事项: {risk_items}

请按以下结构输出（Markdown格式）:

## 公司概况
一句话介绍公司主营业务和行业地位。

## 财报核心亮点
- 营收趋势与增速分析
- 利润质量判断
- 现金流状况

## 估值分析
- 当前估值水平判断（低估/合理/高估）
- 与行业对比

## 风险提示
- 主要风险点

## 综合评级
给出综合评级（优秀/良好/关注/谨慎）和一句话投资建议。
"""


@router.post("/report", response_model=AIReport)
async def report(req: dict):
    code = req.get("code", "")
    try:
        overview = fs.get_financial_overview(code)
        val = fs.get_valuation(code)
        risk = fs.get_risk(code)
    except Exception as e:
        raise HTTPException(500, f"数据获取失败: {e}")

    fin_data = json.dumps(overview["data"][-8:], ensure_ascii=False, indent=2)
    prompt = REPORT_PROMPT.format(
        name=overview["name"], code=code, financial_data=fin_data,
        pe=val["pe"], pb=val["pb"], ps=val["ps"], roe=val["roe"],
        dividend_yield=val["dividend_yield"],
        debt_ratio=risk["debt_ratio"], pledge_ratio=risk["pledge_ratio"],
        goodwill_ratio=risk["goodwill_ratio"], cash_flow_health=risk["cash_flow_health"],
        risk_items="; ".join(risk.get("risk_items", [])) or "无明显风险",
    )
    response = await _client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
    )
    content = response.choices[0].message.content or ""
    summary_line = ""
    for line in content.split("\n"):
        if "综合评级" in line or "投资建议" in line:
            summary_line = line.strip().lstrip("# ").lstrip("- ")
            break
    if not summary_line and len(content) > 50:
        summary_line = content.split("\n")[-1].strip()[:100]
    return AIReport(code=code, name=overview["name"], content=content, summary=summary_line)


CHAT_PROMPT = """你是一个A股基本面分析助手。当前分析标的: {name}({code})

以下是该股票的财务数据摘要:
{financial_context}

请基于以上数据回答用户问题。如果数据不足以回答，请诚实说明。回答尽量简洁，300字以内。"""


@router.post("/chat", response_model=AIResponse)
async def chat(req: dict):
    code = req.get("code", "")
    message = req.get("message", "")
    try:
        overview = fs.get_financial_overview(code)
        val = fs.get_valuation(code)
        risk = fs.get_risk(code)
    except Exception as e:
        raise HTTPException(500, f"数据获取失败: {e}")

    financial_context = f"""
P/E: {val['pe']}, P/B: {val['pb']}, ROE: {val['roe']}%
资产负债率: {risk['debt_ratio']}%, 质押比例: {risk['pledge_ratio']}%
最近季度营收: {overview['data'][-1]['revenue']}亿, 净利润: {overview['data'][-1]['net_profit']}亿
现金流健康度: {risk['cash_flow_health']}
风险等级: {risk['risk_level']}
"""
    system_prompt = CHAT_PROMPT.format(name=overview["name"], code=code, financial_context=financial_context)
    response = await _client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        max_tokens=600,
    )
    return AIResponse(content=response.choices[0].message.content or "")


COMPARE_PROMPT = """你是一个A股基本面分析师。请对比以下股票的财务指标并给出评价。

对比数据:
{compare_data}

请给出:
1. 各项指标的横向排名
2. 综合最优推荐及理由
3. 各股票主要风险
200字以内。"""


@router.post("/compare", response_model=CompareResult)
async def compare(req: CompareRequest):
    codes = req.codes
    if len(codes) < 2:
        raise HTTPException(400, "至少需要2只股票")
    if len(codes) > 6:
        raise HTTPException(400, "最多对比6只股票")

    table = []
    for code in codes:
        try:
            val = fs.get_valuation(code)
            risk = fs.get_risk(code)
            overview = fs.get_financial_overview(code)
            row = {
                "code": code, "name": val["name"],
                "pe": val["pe"], "pb": val["pb"], "roe": val["roe"],
                "debt_ratio": risk["debt_ratio"],
                "risk_level": risk["risk_level"],
            }
            data = overview["data"]
            if len(data) >= 8:
                recent = sum(d["revenue"] for d in data[-4:])
                prev = sum(d["revenue"] for d in data[-8:-4])
                row["revenue_growth"] = round((recent / prev - 1) * 100, 2) if prev > 0 else 0
            else:
                row["revenue_growth"] = 0
            table.append(row)
        except Exception:
            table.append({"code": code, "name": code, "pe": 0, "pb": 0, "roe": 0,
                         "debt_ratio": 0, "risk_level": "N/A", "revenue_growth": 0})

    prompt = COMPARE_PROMPT.format(compare_data=json.dumps(table, ensure_ascii=False, indent=2))
    response = await _client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return CompareResult(table=table, ai_comment=response.choices[0].message.content or "")
