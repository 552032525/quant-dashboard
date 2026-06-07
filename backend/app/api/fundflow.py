from fastapi import APIRouter, HTTPException
from app.schemas.fundflow import (
    StockFlowResult, NorthBoundResult, NorthBoundDaily,
    SectorFlowResult, MarketFlowSummary, AIReport, ReportRequest,
)
from app.services.fundflow_service import get_fundflow_service
from openai import OpenAI
from app.core.config import settings
import json

router = APIRouter(prefix="/fundflow")

_service = get_fundflow_service()


def _ai_report(code: str, name: str, context: str) -> AIReport:
    if not settings.openai_api_key:
        return AIReport(
            code=code, name=name,
            content="未配置 OpenAI API Key，无法生成 AI 解读。",
            summary="",
        )

    prompt = f"""你是一个A股资金面分析师。以下是 {name}({code}) 的资金流向数据摘要：

{context}

请从资金面角度给出简要分析：主力意图判断、资金趋势预判、关键风险提示。200字以内。"""

    try:
        client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        content = resp.choices[0].message.content
        summary = content[:50] if content else ""
        return AIReport(code=code, name=name, content=content or "", summary=summary)
    except Exception as e:
        return AIReport(code=code, name=name, content=f"AI 生成失败: {str(e)}", summary="")


@router.get("/stock/{code}", response_model=StockFlowResult)
async def get_stock_flow(code: str):
    try:
        data = _service.get_stock_flow(code)
        return StockFlowResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/northbound", response_model=NorthBoundResult)
async def get_northbound():
    try:
        data = _service.get_northbound_flow()
        return NorthBoundResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/northbound/daily", response_model=NorthBoundDaily)
async def get_northbound_daily():
    try:
        data = _service.get_northbound_daily()
        if data is None:
            raise HTTPException(status_code=404, detail="北向资金数据暂不可用")
        return NorthBoundDaily(**data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors", response_model=SectorFlowResult)
async def get_sector_flow():
    try:
        data = _service.get_sector_flow()
        return SectorFlowResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market", response_model=MarketFlowSummary)
async def get_market_flow():
    try:
        data = _service.get_market_flow()
        return MarketFlowSummary(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report", response_model=AIReport)
async def get_report(req: ReportRequest):
    try:
        stock_data = _service.get_stock_flow(req.code)
        name = stock_data["name"]
        flows = stock_data["flows"]

        # 构建资金流上下文摘要
        recent5 = flows[-5:] if len(flows) >= 5 else flows
        total_main = sum(f["main_net"] for f in recent5)
        total_super = sum(f["super_large_net"] for f in recent5)
        context = (
            f"近{len(recent5)}日主力净流入: {total_main:.0f}万元\n"
            f"近{len(recent5)}日超大单净流入: {total_super:.0f}万元\n"
        )

        # 附加上板块信息
        try:
            sector_data = _service.get_sector_flow()
            all_sectors = sector_data["inflow_top10"] + sector_data["outflow_top10"]
            sector_names = ", ".join(s["name"][:4] for s in all_sectors[:10])
            context += f"前10活跃板块: {sector_names}"
        except Exception:
            pass

        return _ai_report(req.code, name, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
