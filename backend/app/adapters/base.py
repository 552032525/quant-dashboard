from abc import ABC, abstractmethod
from datetime import date

class DataSourceAdapter(ABC):
    @abstractmethod
    async def get_realtime_quote(self, code: str) -> dict: ...

    @abstractmethod
    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]: ...

    @abstractmethod
    async def search_symbol(self, keyword: str) -> list[dict]: ...

    @abstractmethod
    async def get_index_quotes(self) -> list[dict]: ...

    @abstractmethod
    async def get_market_heat(self) -> dict: ...

    @abstractmethod
    async def get_sectors(self, sector_type: str = "industry") -> list[dict]: ...

    @abstractmethod
    async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]: ...

    @abstractmethod
    async def get_intraday(self, code: str) -> list[dict]: ...