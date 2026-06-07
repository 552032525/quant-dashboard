"""统一内存缓存层 — 基于 TTL 的简单缓存"""
import time
import logging
from typing import Any

logger = logging.getLogger("cache")

# 缓存存储
_cache_store: dict[str, dict] = {}

# 默认 TTL（秒）
DEFAULT_TTL = {
    "spot": 30,       # 实时行情 30 秒
    "kline": 300,     # K 线 5 分钟
    "index": 30,      # 指数 30 秒
    "heat": 60,       # 市场热度 60 秒
    "sectors": 300,   # 板块 5 分钟
    "rankings": 30,   # 排行 30 秒
    "fundamental": 600,  # 基本面 10 分钟
    "long": 3600,     # 长周期 1 小时
}


def get(key: str) -> Any | None:
    """从缓存获取值，过期返回 None"""
    entry = _cache_store.get(key)
    if entry:
        if time.time() - entry["ts"] < entry["ttl"]:
            return entry["data"]
        else:
            del _cache_store[key]
    return None


def set(key: str, data: Any, ttl: int | str = "spot"):
    """设置缓存值
    
    Args:
        key: 缓存键
        data: 缓存数据
        ttl: TTL 秒数，或 DEFAULT_TTL 中的键名
    """
    if isinstance(ttl, str):
        ttl = DEFAULT_TTL.get(ttl, 30)
    _cache_store[key] = {"data": data, "ts": time.time(), "ttl": ttl}


def delete(key: str):
    """删除缓存"""
    _cache_store.pop(key, None)


def clear(prefix: str = ""):
    """清空缓存
    
    Args:
        prefix: 可选，只清除以此前缀开头的键
    """
    global _cache_store
    if prefix:
        _cache_store = {k: v for k, v in _cache_store.items() if not k.startswith(prefix)}
    else:
        _cache_store.clear()


def stats() -> dict:
    """缓存统计"""
    total = len(_cache_store)
    active = sum(1 for v in _cache_store.values() if time.time() - v["ts"] < v["ttl"])
    return {"total_entries": total, "active_entries": active}
