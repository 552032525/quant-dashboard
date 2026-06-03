from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    symbol_code: str
    days: int = 30

class ChatRequest(BaseModel):
    message: str
    symbol_code: str | None = None

class AIResponse(BaseModel):
    content: str
