from app.adapters.base import DataSourceAdapter
from app.adapters.akshare_adapter import AkshareAdapter
from app.core.config import settings

def get_adapter() -> DataSourceAdapter:
    if settings.data_source == "akshare":
        return AkshareAdapter()
    raise ValueError(f"未知数据源: {settings.data_source}")
