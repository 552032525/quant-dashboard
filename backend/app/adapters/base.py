from abc import ABC, abstractmethod
from datetime import date

class DataSourceAdapter(ABC):
    @abstractmethod
    async def get_realtime_quote(self, code: str) -> dict:
        ...

    @abstractmethod
    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        ...

    @abstractmethod
    async def search_symbol(self, keyword: str) -> list[dict]:
        ...
