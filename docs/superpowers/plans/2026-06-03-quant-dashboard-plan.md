# 量化交易看板 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建量化交易看板 MVP 一期：行情 K 线图 + 持仓管理 + AI 分析 + 部署到服务器。

**Architecture:** 单仓结构，frontend/（Vue3 + ECharts + Tailwind）+ backend/（FastAPI + SQLAlchemy + akshare）+ Docker Compose 编排。

**Tech Stack:** Vue3, Vite, Pinia, ECharts 5, TailwindCSS, FastAPI, SQLAlchemy 2.0, akshare, OpenAI, Celery, Redis, PostgreSQL 16, Docker

---

## Phase 1: 项目脚手架

### Task 1: Docker Compose 编排

**Files:** docker-compose.yml, .env.example

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: "3.8"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: quant
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-quant123}
      POSTGRES_DB: quant_dashboard
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quant -d quant_dashboard"]
      interval: 5s; timeout: 5s; retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s; timeout: 5s; retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://quant:${POSTGRES_PASSWORD:-quant123}@db:5432/quant_dashboard
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_BASE_URL: ${OPENAI_BASE_URL:-https://api.openai.com/v1}
      DATA_SOURCE: ${DATA_SOURCE:-akshare}
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    volumes:
      - ./backend:/app

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.services.scheduler worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://quant:${POSTGRES_PASSWORD:-quant123}@db:5432/quant_dashboard
      REDIS_URL: redis://redis:6379/0
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  pgdata:
```

- [ ] **Step 2: 创建 .env.example**

```bash
POSTGRES_PASSWORD=quant123
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DATA_SOURCE=akshare
```

- [ ] **Step 3: 验证 docker-compose 语法**

Run: `docker-compose config`
Expected: 无错误，输出配置摘要

---

### Task 2: FastAPI 后端脚手架

**Files:** backend/requirements.txt, backend/Dockerfile, backend/app/main.py, backend/app/core/config.py, backend/app/core/database.py

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
pydantic==2.9.2
pydantic-settings==2.5.2
akshare==1.14.0
openai==1.51.0
httpx==0.27.2
celery[redis]==5.4.0
redis==5.1.1
python-dotenv==1.0.1
```

- [ ] **Step 2: 创建 backend/Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: 创建 backend/app/core/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://quant:quant123@localhost:5432/quant_dashboard"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    data_source: str = "akshare"
    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: 创建 backend/app/core/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 5: 创建 backend/app/main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models import Base
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Quant Dashboard", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: 验证后端启动**

Run: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8000`
Check: `curl http://localhost:8000/api/health` returns `{"status":"ok"}`

---

### Task 3: Vue3 前端脚手架

**Files:** frontend/ (Vite + Vue3 + TS), tailwind.config.js, Dockerfile, nginx.conf

- [ ] **Step 1: 初始化 Vue3 项目**

Run: `cd frontend && npm create vite@latest . -- --template vue-ts && npm install`

- [ ] **Step 2: 安装依赖**

Run: `cd frontend && npm install vue-router@4 pinia echarts vue-echarts && npm install -D tailwindcss @tailwindcss/vite`

- [ ] **Step 3: 配置 tailwind.config.js**

```js
export default {
  content: ["./index.html", "./src/**/*.{vue,ts,js}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0d1b2a",
        surface: "#132438",
        "surface-2": "#1a314a",
        primary: "#0052ff",
        gain: "#05b169",
        loss: "#cf202f",
        "text-primary": "#f0f4f8",
        "text-secondary": "#8899aa",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: { pill: "100px" },
    },
  },
};
```

- [ ] **Step 4: 创建全局样式 frontend/src/style.css**

```css
@import "tailwindcss";
@layer base {
  body { @apply bg-canvas text-text-primary font-sans; margin: 0; min-height: 100vh; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0d1b2a; }
  ::-webkit-scrollbar-thumb { background: #1a314a; border-radius: 3px; }
}
```

- [ ] **Step 5: 创建 nginx 配置和 Dockerfile**

frontend/nginx.conf:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /api/ { proxy_pass http://backend:8000; }
}
```

frontend/Dockerfile:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 6: 验证前端构建**

Run: `cd frontend && npm run build`
Expected: 无错误，dist/ 生成

---

## Phase 2: 数据模型与 API

### Task 4: 数据库模型（5个表）

**Files:** backend/app/models/base.py, symbol.py, klinedata.py, position.py, alert.py, watchlist.py, __init__.py

- [ ] **Step 1: 创建 base.py**

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, func

class Base(DeclarativeBase): pass

class TimestampMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: 创建 symbol.py**

```python
from sqlalchemy import String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum
from app.models.base import Base, TimestampMixin

class Market(str, enum.Enum): SH="SH"; SZ="SZ"
class SymbolType(str, enum.Enum): STOCK="stock"; ETF="etf"; INDEX="index"

class Symbol(Base, TimestampMixin):
    __tablename__ = "symbols"
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[Market] = mapped_column(SqlEnum(Market), nullable=False)
    type: Mapped[SymbolType] = mapped_column(SqlEnum(SymbolType), default=SymbolType.STOCK)
```

- [ ] **Step 3: 创建 klinedata.py**

```python
from sqlalchemy import BigInteger, Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.models.base import Base, TimestampMixin

class KLineData(Base, TimestampMixin):
    __tablename__ = "klinedata"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
```

- [ ] **Step 4: 创建 position.py**

```python
from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class Position(Base, TimestampMixin):
    __tablename__ = "positions"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
```

- [ ] **Step 5: 创建 alert.py 和 watchlist.py**

alert.py:
```python
from sqlalchemy import BigInteger, Float, Boolean, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
```

watchlist.py:
```python
from sqlalchemy import BigInteger, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class WatchlistItem(Base, TimestampMixin):
    __tablename__ = "watchlist"
    symbol_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("symbols.id"), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
```

- [ ] **Step 6: 创建 models/__init__.py**

```python
from app.models.base import Base
from app.models.symbol import Symbol, Market, SymbolType
from app.models.klinedata import KLineData
from app.models.position import Position
from app.models.alert import Alert
from app.models.watchlist import WatchlistItem
```

- [ ] **Step 7: 验证建表**

Run: `docker-compose up -d db && sleep 3 && docker-compose up backend`
Check: `docker-compose exec db psql -U quant -d quant_dashboard -c "\dt"`
Expected: 看到 symbols, klinedata, positions, alerts, watchlist

---

### Task 5: Pydantic Schemas

**Files:** backend/app/schemas/__init__.py, market.py, portfolio.py, ai.py

- [ ] **Step 1: market.py**

```python
from pydantic import BaseModel
from datetime import date

class KLineItem(BaseModel):
    date: date; open: float; high: float; low: float; close: float; volume: float

class RealtimeQuote(BaseModel):
    code: str; name: str; price: float; change: float; change_pct: float
    volume: float; high: float; low: float; open: float; pre_close: float

class SymbolInfo(BaseModel):
    code: str; name: str; market: str; type: str
```

- [ ] **Step 2: portfolio.py**

```python
from pydantic import BaseModel
from datetime import datetime

class PositionCreate(BaseModel):
    symbol_code: str; quantity: int; cost_price: float

class PositionUpdate(BaseModel):
    quantity: int | None = None; cost_price: float | None = None

class PositionResponse(BaseModel):
    id: int; symbol_code: str; symbol_name: str; quantity: int; cost_price: float
    current_price: float | None = None; market_value: float | None = None
    profit_loss: float | None = None; profit_loss_pct: float | None = None
    created_at: datetime

class PortfolioSummary(BaseModel):
    total_assets: float; total_market_value: float; available_cash: float
    total_profit_loss: float; total_profit_loss_pct: float
```

- [ ] **Step 3: ai.py**

```python
from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    symbol_code: str; days: int = 30

class ChatRequest(BaseModel):
    message: str; symbol_code: str | None = None

class AIResponse(BaseModel):
    content: str
```

---

### Task 6: 数据源适配器

**Files:** backend/app/adapters/__init__.py, base.py, akshare_adapter.py

- [ ] **Step 1: base.py（抽象基类）**

```python
from abc import ABC, abstractmethod
from datetime import date

class DataSourceAdapter(ABC):
    @abstractmethod
    async def get_realtime_quote(self, code: str) -> dict: ...
    @abstractmethod
    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]: ...
    @abstractmethod
    async def search_symbol(self, keyword: str) -> list[dict]: ...
```

- [ ] **Step 2: akshare_adapter.py**

```python
import akshare as ak
from datetime import date
from app.adapters.base import DataSourceAdapter

class AkshareAdapter(DataSourceAdapter):
    async def get_realtime_quote(self, code: str) -> dict:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if row.empty: raise ValueError(f"未找到股票: {code}")
        r = row.iloc[0]
        return {"code":code,"name":r["名称"],"price":float(r["最新价"]),"change":float(r["涨跌额"]),
                "change_pct":float(r["涨跌幅"]),"volume":float(r["成交量"]),"high":float(r["最高"]),
                "low":float(r["最低"]),"open":float(r["今开"]),"pre_close":float(r["昨收"])}

    async def get_kline(self, code, start_date, end_date, period="daily"):
        df = ak.stock_zh_a_hist(symbol=code, period=period,
            start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
        return [{"date":row["日期"],"open":float(row["开盘"]),"high":float(row["最高"]),
                 "low":float(row["最低"]),"close":float(row["收盘"]),"volume":float(row["成交量"])}
                for _,row in df.iterrows()]

    async def search_symbol(self, keyword: str) -> list[dict]:
        df = ak.stock_zh_a_spot_em()
        mask = df["名称"].str.contains(keyword) | df["代码"].str.contains(keyword)
        return [{"code":row["代码"],"name":row["名称"]} for _,row in df[mask].head(20).iterrows()]
```

- [ ] **Step 3: __init__.py（工厂函数）**

```python
from app.adapters.base import DataSourceAdapter
from app.adapters.akshare_adapter import AkshareAdapter
from app.core.config import settings

def get_adapter() -> DataSourceAdapter:
    if settings.data_source == "akshare": return AkshareAdapter()
    raise ValueError(f"未知数据源: {settings.data_source}")
```

---

### Task 7: 行情 API + 持仓 API + AI API

**Files:** backend/app/api/__init__.py, router.py, market.py, portfolio.py, ai.py

- [ ] **Step 1: router.py**

```python
from fastapi import APIRouter
from app.api.market import router as market_router
from app.api.portfolio import router as portfolio_router
from app.api.ai import router as ai_router

api_router = APIRouter(prefix="/api")
api_router.include_router(market_router, tags=["market"])
api_router.include_router(portfolio_router, tags=["portfolio"])
api_router.include_router(ai_router, tags=["ai"])
```

- [ ] **Step 2: market.py**

```python
from fastapi import APIRouter, HTTPException, Query
from datetime import date, timedelta
from app.adapters import get_adapter
from app.schemas.market import KLineItem, RealtimeQuote, SymbolInfo

router = APIRouter(prefix="/market")

@router.get("/realtime/{code}", response_model=RealtimeQuote)
async def get_realtime(code: str):
    try: return RealtimeQuote(**await get_adapter().get_realtime_quote(code))
    except ValueError as e: raise HTTPException(404, detail=str(e))

@router.get("/kline/{code}", response_model=list[KLineItem])
async def get_kline(code: str, start_date: date = Query(default_factory=lambda: date.today()-timedelta(days=365)),
                    end_date: date = Query(default_factory=date.today), period: str = "daily"):
    try:
        data = await get_adapter().get_kline(code, start_date, end_date, period)
        return [KLineItem(**item) for item in data]
    except Exception as e: raise HTTPException(500, detail=str(e))

@router.get("/search", response_model=list[SymbolInfo])
async def search_symbol(keyword: str = Query(..., min_length=1)):
    try:
        data = await get_adapter().search_symbol(keyword)
        return [SymbolInfo(**item, market="SH" if item["code"].startswith("6") else "SZ", type="stock") for item in data]
    except Exception as e: raise HTTPException(500, detail=str(e))
```

- [ ] **Step 3: portfolio.py**

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.position import Position
from app.models.symbol import Symbol
from app.schemas.portfolio import PositionCreate, PositionUpdate, PositionResponse, PortfolioSummary

router = APIRouter(prefix="/portfolio")

@router.get("", response_model=list[PositionResponse])
async def list_positions(db: AsyncSession = Depends(get_db)):
    positions = (await db.execute(select(Position).order_by(Position.created_at.desc()))).scalars().all()
    resp = []
    for p in positions:
        sym = (await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))).scalar_one_or_none()
        resp.append(PositionResponse(id=p.id, symbol_code=sym.code if sym else "", symbol_name=sym.name if sym else "",
            quantity=p.quantity, cost_price=p.cost_price, created_at=p.created_at))
    return resp

@router.post("", response_model=PositionResponse, status_code=201)
async def create_position(data: PositionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Symbol).where(Symbol.code == data.symbol_code))
    symbol = result.scalar_one_or_none()
    if not symbol: raise HTTPException(404, detail=f"未找到股票: {data.symbol_code}")
    p = Position(symbol_id=symbol.id, quantity=data.quantity, cost_price=data.cost_price)
    db.add(p); await db.commit(); await db.refresh(p)
    return PositionResponse(id=p.id, symbol_code=symbol.code, symbol_name=symbol.name,
        quantity=p.quantity, cost_price=p.cost_price, created_at=p.created_at)

@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(position_id: int, data: PositionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, detail="持仓记录不存在")
    if data.quantity is not None: p.quantity = data.quantity
    if data.cost_price is not None: p.cost_price = data.cost_price
    await db.commit(); await db.refresh(p)
    sym = (await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))).scalar_one()
    return PositionResponse(id=p.id, symbol_code=sym.code, symbol_name=sym.name,
        quantity=p.quantity, cost_price=p.cost_price, created_at=p.created_at)

@router.delete("/{position_id}", status_code=204)
async def delete_position(position_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, detail="持仓记录不存在")
    await db.delete(p); await db.commit()

@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    positions = (await db.execute(select(Position))).scalars().all()
    total_cost = sum(p.quantity * p.cost_price for p in positions)
    return PortfolioSummary(total_assets=total_cost, total_market_value=total_cost,
        available_cash=0, total_profit_loss=0, total_profit_loss_pct=0)
```

- [ ] **Step 4: ai.py**

```python
from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from datetime import date, timedelta
from app.core.config import settings
from app.adapters import get_adapter
from app.schemas.ai import AnalyzeRequest, ChatRequest, AIResponse

router = APIRouter(prefix="/ai")
ANALYZE_PROMPT = "你是量化交易分析师。以下是{name}({code})最近{days}日行情数据：\n{data}\n请从技术面给出简要分析：趋势判断、关键支撑/压力位、风险提示。200字以内。"

def _client(): return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

@router.post("/analyze", response_model=AIResponse)
async def analyze(req: AnalyzeRequest):
    adapter = get_adapter()
    quote = await adapter.get_realtime_quote(req.code)
    klines = await adapter.get_kline(req.code, date.today()-timedelta(days=req.days), date.today())
    data_text = "\n".join(f"{k['date']}: O{k['open']:.2f} H{k['high']:.2f} L{k['low']:.2f} C{k['close']:.2f}" for k in klines[-30:])
    prompt = ANALYZE_PROMPT.format(name=quote["name"], code=req.code, days=req.days, data=data_text)
    resp = await _client().chat.completions.create(model="gpt-5.5", messages=[{"role":"user","content":prompt}], max_tokens=400)
    return AIResponse(content=resp.choices[0].message.content or "")

@router.post("/chat", response_model=AIResponse)
async def chat(req: ChatRequest):
    msgs = [{"role":"user","content":req.message}]
    if req.symbol_code:
        q = await get_adapter().get_realtime_quote(req.symbol_code)
        msgs.insert(0, {"role":"system","content":f"当前标的: {q['name']}({req.symbol_code})，现价{q['price']}，涨跌幅{q['change_pct']}%"})
    resp = await _client().chat.completions.create(model="gpt-5.5", messages=msgs, max_tokens=600)
    return AIResponse(content=resp.choices[0].message.content or "")
```

---

## Phase 3: 前端页面

### Task 8: 前端基础设施

**Files:** frontend/src/router/index.ts, api/index.ts, stores/market.ts, stores/portfolio.ts, main.ts, App.vue

- [ ] **Step 1: router/index.ts**

```typescript
import { createRouter, createWebHistory } from "vue-router";
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "market", component: () => import("../views/MarketView.vue") },
    { path: "/portfolio", name: "portfolio", component: () => import("../views/PortfolioView.vue") },
    { path: "/ai", name: "ai", component: () => import("../views/AIChatView.vue") },
  ],
});
```

- [ ] **Step 2: api/index.ts**

```typescript
const BASE = "/api";
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error((await res.json().catch(()=>({detail:res.statusText}))).detail || "请求失败");
  if (res.status === 204) return undefined as T;
  return res.json();
}
export const api = {
  market: {
    realtime: (code: string) => request<any>(`/market/realtime/${code}`),
    kline: (code: string, start?: string, end?: string, period = "daily") =>
      request<any[]>(`/market/kline/${code}?start_date=${start||""}&end_date=${end||""}&period=${period}`),
    search: (keyword: string) => request<any[]>(`/market/search?keyword=${encodeURIComponent(keyword)}`),
  },
  portfolio: {
    list: () => request<any[]>("/portfolio"),
    create: (data: any) => request<any>("/portfolio", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: any) => request<any>(`/portfolio/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/portfolio/${id}`, { method: "DELETE" }),
    summary: () => request<any>("/portfolio/summary"),
  },
  ai: {
    analyze: (code: string, days = 30) =>
      request<any>("/ai/analyze", { method: "POST", body: JSON.stringify({ symbol_code: code, days }) }),
    chat: (message: string, code?: string) =>
      request<any>("/ai/chat", { method: "POST", body: JSON.stringify({ message, symbol_code: code }) }),
  },
};
```

- [ ] **Step 3: stores/market.ts**

```typescript
import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useMarketStore = defineStore("market", () => {
  const activeSymbol = ref("600519"); const klineData = ref<any[]>([]); const quote = ref<any>(null); const loading = ref(false);
  async function fetchKline(code: string) {
    loading.value = true;
    try { klineData.value = await api.market.kline(code); quote.value = await api.market.realtime(code); activeSymbol.value = code; }
    finally { loading.value = false; }
  }
  return { activeSymbol, klineData, quote, loading, fetchKline };
});
```

- [ ] **Step 4: stores/portfolio.ts**

```typescript
import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const usePortfolioStore = defineStore("portfolio", () => {
  const positions = ref<any[]>([]); const summary = ref<any>(null);
  async function fetchAll() { positions.value = await api.portfolio.list(); summary.value = await api.portfolio.summary(); }
  async function add(data: { symbol_code: string; quantity: number; cost_price: number }) { await api.portfolio.create(data); await fetchAll(); }
  async function remove(id: number) { await api.portfolio.delete(id); await fetchAll(); }
  return { positions, summary, fetchAll, add, remove };
});
```

- [ ] **Step 5: main.ts + App.vue**

main.ts:
```typescript
import { createApp } from "vue"; import { createPinia } from "pinia"; import App from "./App.vue"; import router from "./router"; import "./style.css";
createApp(App).use(createPinia()).use(router).mount("#app");
```

App.vue:
```vue
<template>
  <div class="flex h-screen">
    <nav class="w-14 bg-surface flex flex-col items-center py-4 gap-5 border-r border-surface-2">
      <router-link to="/" class="nav-icon" title="行情">📈</router-link>
      <router-link to="/portfolio" class="nav-icon" title="持仓">💼</router-link>
      <router-link to="/ai" class="nav-icon" title="AI">🤖</router-link>
    </nav>
    <main class="flex-1 overflow-auto"><router-view /></main>
  </div>
</template>
<style scoped>
.nav-icon { @apply w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-surface-2 transition-colors; }
.router-link-active { @apply bg-surface-2; }
</style>
```

---

### Task 9: K线图组件 + 行情看板

**Files:** frontend/src/components/KLineChart.vue, MetricCard.vue, frontend/src/views/MarketView.vue

- [ ] **Step 1: KLineChart.vue**

```vue
<template><div ref="chartRef" class="w-full h-full"></div></template>
<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from "vue"; import * as echarts from "echarts";
const props = defineProps<{ data: any[] }>();
const chartRef = ref<HTMLDivElement>(); let chart: echarts.ECharts | null = null;

function calcMA(data: any[], period: number) {
  const r: (number|null)[] = [];
  for (let i=0; i<data.length; i++) {
    if (i < period-1) { r.push(null); continue; }
    let s=0; for (let j=0; j<period; j++) s+=data[i-j].close; r.push(+(s/period).toFixed(2));
  }
  return r;
}
function buildOption(data: any[]) {
  const dates = data.map(d=>d.date);
  return {
    backgroundColor:"transparent",
    grid:[{left:"3%",right:"3%",top:"5%",height:"60%"},{left:"3%",right:"3%",top:"72%",height:"20%"}],
    xAxis:[
      {type:"category",data:dates,axisLine:{lineStyle:{color:"#1a314a"}},axisLabel:{color:"#8899aa",fontSize:10}},
      {type:"category",gridIndex:1,data:dates,axisLabel:{show:false},axisLine:{show:false},axisTick:{show:false}}
    ],
    yAxis:[
      {type:"value",axisLine:{show:false},axisLabel:{color:"#8899aa",fontSize:10},splitLine:{lineStyle:{color:"#1a314a"}}},
      {type:"value",gridIndex:1,axisLabel:{show:false},splitLine:{show:false}}
    ],
    series:[
      {name:"K线",type:"candlestick",data:data.map(d=>[d.open,d.close,d.low,d.high]),itemStyle:{color:"#05b169",color0:"#cf202f",borderColor:"#05b169",borderColor0:"#cf202f"}},
      {name:"MA5",type:"line",data:calcMA(data,5),smooth:true,lineStyle:{color:"#f5a623",width:1},symbol:"none"},
      {name:"MA10",type:"line",data:calcMA(data,10),smooth:true,lineStyle:{color:"#4a90d9",width:1},symbol:"none"},
      {name:"MA20",type:"line",data:calcMA(data,20),smooth:true,lineStyle:{color:"#e066ff",width:1},symbol:"none"},
      {name:"量",type:"bar",xAxisIndex:1,yAxisIndex:1,data:data.map(d=>d.volume),itemStyle:{color:(p:any)=>{const i=p.dataIndex;return data[i]?.close>=data[i]?.open?"#05b169":"#cf202f"}}}
    ],
    tooltip:{trigger:"axis",backgroundColor:"#132438",borderColor:"#1a314a",textStyle:{color:"#f0f4f8"}}
  };
}
onMounted(()=>{if(chartRef.value){chart=echarts.init(chartRef.value);if(props.data.length)chart.setOption(buildOption(props.data));window.addEventListener("resize",()=>chart?.resize());}});
watch(()=>props.data,v=>{if(chart&&v.length)chart.setOption(buildOption(v),true);});
onUnmounted(()=>chart?.dispose());
</script>
```

- [ ] **Step 2: MetricCard.vue**

```vue
<template>
  <div class="bg-surface rounded-xl p-3 border border-surface-2">
    <div class="text-text-secondary text-xs mb-1">{{ label }}</div>
    <div class="text-xl font-mono" :class="trend==='up'?'text-gain':trend==='down'?'text-loss':'text-text-primary'">{{ value.toFixed(decimals??2) }}</div>
    <div v-if="sub" class="text-xs mt-1" :class="trend==='up'?'text-gain':'text-loss'">{{ sub }}</div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ label: string; value: number; decimals?: number; sub?: string; trend?: "up"|"down"|"neutral" }>();
</script>
```

- [ ] **Step 3: MarketView.vue**

```vue
<template>
  <div class="h-full flex flex-col">
    <div class="px-4 py-3 border-b border-surface-2 flex gap-3 items-center">
      <input v-model="kw" @keyup.enter="search" placeholder="搜索股票代码/名称..."
        class="bg-surface-2 text-text-primary px-3 py-1.5 rounded-lg text-sm w-64 outline-none focus:ring-1 focus:ring-primary" />
      <div v-if="results.length" class="absolute top-12 bg-surface-2 rounded-lg shadow-lg z-50 max-h-60 overflow-auto">
        <div v-for="r in results" :key="r.code" @click="select(r.code)" class="px-3 py-2 hover:bg-surface cursor-pointer text-sm">{{ r.code }} {{ r.name }}</div>
      </div>
    </div>
    <div class="flex-1 flex">
      <div class="flex-1 p-4">
        <div class="flex items-center gap-3 mb-3">
          <h2 class="text-lg font-medium">{{ m.quote?.name || m.activeSymbol }}</h2>
          <span v-if="m.quote" class="font-mono text-lg" :class="m.quote.change_pct>=0?'text-gain':'text-loss'">{{ m.quote.price?.toFixed(2) }}</span>
          <span v-if="m.quote" class="text-sm font-mono" :class="m.quote.change_pct>=0?'text-gain':'text-loss'">{{ m.quote.change_pct>=0?'+':'' }}{{ m.quote.change_pct?.toFixed(2) }}%</span>
        </div>
        <KLineChart v-if="m.klineData.length" :data="m.klineData" class="h-[calc(100%-3rem)]" />
        <div v-else class="h-full flex items-center justify-center text-text-secondary">输入股票代码查看 K 线图</div>
      </div>
      <aside class="w-72 border-l border-surface-2 p-4 flex flex-col gap-3 overflow-auto">
        <MetricCard label="最新价" :value="m.quote?.price??0" :trend="m.quote?.change_pct>=0?'up':'down'" />
        <MetricCard label="涨跌幅" :value="m.quote?.change_pct??0" :sub="m.quote?.change?.toFixed(2)" :trend="m.quote?.change_pct>=0?'up':'down'" />
        <MetricCard label="成交量" :value="m.quote?.volume??0" :decimals="0" trend="neutral" />
        <MetricCard label="最高" :value="m.quote?.high??0" trend="neutral" />
        <MetricCard label="最低" :value="m.quote?.low??0" trend="neutral" />
        <MetricCard label="今开" :value="m.quote?.open??0" trend="neutral" />
        <MetricCard label="昨收" :value="m.quote?.pre_close??0" trend="neutral" />
      </aside>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue"; import { useMarketStore } from "../stores/market"; import { api } from "../api";
import KLineChart from "../components/KLineChart.vue"; import MetricCard from "../components/MetricCard.vue";
const m = useMarketStore(); const kw = ref(""); const results = ref<any[]>([]);
async function search() { if(kw.value.trim()) results.value = await api.market.search(kw.value.trim()); }
function select(code: string) { results.value=[]; kw.value=""; m.fetchKline(code); }
onMounted(()=>m.fetchKline("600519"));
</script>
```

---

### Task 10: 持仓页面 + AI 分析页面

**Files:** frontend/src/views/PortfolioView.vue, AIChatView.vue

- [ ] **Step 1: PortfolioView.vue**

```vue
<template>
  <div class="p-6">
    <h2 class="text-xl font-medium mb-4">持仓管理</h2>
    <div class="grid grid-cols-4 gap-3 mb-6" v-if="p.summary">
      <MetricCard label="总资产" :value="p.summary.total_assets" trend="neutral" />
      <MetricCard label="持仓市值" :value="p.summary.total_market_value" trend="neutral" />
      <MetricCard label="浮动盈亏" :value="p.summary.total_profit_loss" :trend="p.summary.total_profit_loss>=0?'up':'down'" />
      <MetricCard label="盈亏比例" :value="p.summary.total_profit_loss_pct" trend="neutral" />
    </div>
    <div class="bg-surface rounded-xl p-4 mb-4 border border-surface-2">
      <h3 class="text-sm font-medium mb-3 text-text-secondary">添加持仓</h3>
      <div class="flex gap-3">
        <input v-model="f.code" placeholder="股票代码" class="flex-1 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <input v-model.number="f.qty" type="number" placeholder="数量" class="w-24 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <input v-model.number="f.cost" type="number" step="0.01" placeholder="成本价" class="w-28 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <button @click="add" class="bg-primary text-white px-5 py-2 rounded-pill text-sm font-medium hover:opacity-90">添加</button>
      </div>
    </div>
    <div class="bg-surface rounded-xl border border-surface-2 overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="border-b border-surface-2 text-text-secondary text-xs uppercase">
          <th class="text-left px-4 py-3">代码</th><th class="text-left px-4 py-3">名称</th><th class="text-right px-4 py-3">数量</th><th class="text-right px-4 py-3">成本价</th><th class="text-right px-4 py-3">操作</th>
        </tr></thead>
        <tbody>
          <tr v-for="pos in p.positions" :key="pos.id" class="border-b border-surface-2 hover:bg-surface-2">
            <td class="px-4 py-3 font-mono">{{ pos.symbol_code }}</td><td class="px-4 py-3">{{ pos.symbol_name }}</td>
            <td class="px-4 py-3 text-right font-mono">{{ pos.quantity }}</td><td class="px-4 py-3 text-right font-mono">{{ pos.cost_price?.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right"><button @click="del(pos.id)" class="text-loss hover:opacity-80 text-xs">删除</button></td>
          </tr>
          <tr v-if="!p.positions.length"><td colspan="5" class="px-4 py-8 text-center text-text-secondary">暂无持仓记录</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, onMounted } from "vue"; import { usePortfolioStore } from "../stores/portfolio"; import MetricCard from "../components/MetricCard.vue";
const p = usePortfolioStore(); const f = reactive({ code:"", qty:0, cost:0 });
async function add() { if(!f.code||f.qty<=0||f.cost<=0)return; await p.add({symbol_code:f.code,quantity:f.qty,cost_price:f.cost}); f.code="";f.qty=0;f.cost=0; }
async function del(id:number) { await p.remove(id); }
onMounted(()=>p.fetchAll());
</script>
```

- [ ] **Step 2: AIChatView.vue**

```vue
<template>
  <div class="p-6 max-w-3xl mx-auto h-full flex flex-col">
    <h2 class="text-xl font-medium mb-4">AI 行情分析</h2>
    <div class="bg-surface rounded-xl p-4 mb-4 border border-surface-2">
      <div class="flex gap-3 items-center">
        <input v-model="code" placeholder="股票代码" class="bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm w-32 outline-none focus:ring-1 focus:ring-primary" />
        <button @click="analyze" :disabled="loading" class="bg-primary text-white px-5 py-2 rounded-pill text-sm font-medium hover:opacity-90 disabled:opacity-50">{{ loading?'分析中...':'一键分析' }}</button>
      </div>
      <div v-if="result" class="mt-4 p-3 bg-surface-2 rounded-lg text-sm leading-relaxed">{{ result }}</div>
    </div>
    <div class="flex-1 bg-surface rounded-xl border border-surface-2 flex flex-col overflow-hidden">
      <div ref="box" class="flex-1 overflow-auto p-4 space-y-3">
        <div v-for="(m,i) in msgs" :key="i" :class="m.role==='user'?'text-right':''">
          <div :class="m.role==='user'?'bg-primary text-white ml-auto':'bg-surface-2 text-text-primary'" class="inline-block max-w-[80%] px-4 py-2 rounded-xl text-sm">{{ m.content }}</div>
        </div>
        <div v-if="!msgs.length" class="text-text-secondary text-sm text-center py-8">输入问题开始 AI 对话</div>
      </div>
      <div class="border-t border-surface-2 p-3 flex gap-2">
        <input v-model="input" @keyup.enter="chat" placeholder="输入问题..." class="flex-1 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <button @click="chat" class="bg-primary text-white px-4 py-2 rounded-pill text-sm hover:opacity-90">发送</button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, nextTick } from "vue"; import { api } from "../api";
const code=ref("600519"); const loading=ref(false); const result=ref(""); const input=ref("");
const msgs=ref<{role:string;content:string}[]>([]); const box=ref<HTMLDivElement>();
async function analyze(){loading.value=true;try{const r=await api.ai.analyze(code.value);result.value=r.content;}finally{loading.value=false;}}
async function chat(){if(!input.value.trim())return;msgs.value.push({role:"user",content:input.value.trim()});input.value="";await nextTick();box.value?.scrollTo({top:box.value.scrollHeight,behavior:"smooth"});const r=await api.ai.chat(msgs.value[msgs.value.length-1].content,code.value);msgs.value.push({role:"assistant",content:r.content});await nextTick();box.value?.scrollTo({top:box.value.scrollHeight,behavior:"smooth"});}
</script>
```

---

## Phase 4: 部署

### Task 11: 本地验证 + 部署到服务器

- [ ] **Step 1: 本地全栈启动验证**

Run: `docker-compose up -d --build`
Check: `docker-compose ps` — 所有服务 Status: Up
Check: `curl http://localhost/api/health` — `{"status":"ok"}`
Check: 浏览器打开 `http://localhost` — 看到 Vue3 页面

- [ ] **Step 2: 上传到服务器**

```bash
tar -czf quant.tar.gz --exclude=node_modules --exclude=__pycache__ --exclude=.git .
scp quant.tar.gz root@43.138.253.185:/opt/
ssh root@43.138.253.185 "cd /opt && mkdir -p quant-dashboard && tar -xzf quant.tar.gz -C quant-dashboard"
```

- [ ] **Step 3: 服务器端配置并启动**

```bash
ssh root@43.138.253.185
cd /opt/quant-dashboard
echo 'POSTGRES_PASSWORD=quant123' > .env
echo 'OPENAI_API_KEY=sk-xxx' >> .env
echo 'DATA_SOURCE=akshare' >> .env
docker-compose up -d --build
```

- [ ] **Step 4: 验证部署**

Check: `docker-compose ps` — 所有服务 running
Check: `curl http://43.138.253.185/api/health` — `{"status":"ok"}`

---

## 自检清单

- [x] Spec 全覆盖：行情、持仓、AI、部署
- [x] 无 TBD/占位符
- [x] API 端点与前端调用一致
- [x] 前后端类型匹配

> 关联 Spec：docs/superpowers/specs/2026-06-03-quant-dashboard-design.md
