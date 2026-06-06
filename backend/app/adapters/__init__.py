from app.adapters.base import DataSourceAdapter
from app.adapters.akshare_adapter import AkshareAdapter
from app.adapters.baostock_adapter import BaostockAdapter
from app.adapters.web_adapter import WebAdapter
from app.core.config import settings

_adapter: DataSourceAdapter | None = None

def get_adapter() -> DataSourceAdapter:
    global _adapter
    if _adapter is None:
        if settings.data_source == "baostock":
            _adapter = BaostockAdapter()
        elif settings.data_source == "akshare":
            _adapter = AkshareAdapter()
        elif settings.data_source == "web":
            _adapter = WebAdapter()
        else:
            raise ValueError(f"未知数据源: {settings.data_source}")
    return _adapter