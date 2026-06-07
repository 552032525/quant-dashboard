"""新浪财经行情数据工具 - 统一接口"""
import logging
import re
import requests

logger = logging.getLogger(__name__)
SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}


def _sina_prefix(code: str) -> str:
    """根据代码生成新浪行情前缀"""
    if code.startswith("92"):
        return "bj" + code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code


def _sina_raw_parts(code: str) -> list:
    """获取新浪行情原始字段（内部共享，避免重复请求）"""
    prefix = _sina_prefix(code)
    resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers=SINA_HEADERS, timeout=5)
    resp.encoding = "gbk"
    m = re.search(r'"([^"]*)"', resp.text)
    if m:
        return m.group(1).split(",")
    return []


def sina_quote(code: str) -> dict:
    """获取个股实时行情（新浪接口）
    
    Returns:
        {"name": str, "price": float, "change_pct": float, "prev_close": float, "open": float, "high": float, "low": float, "volume": float}
        失败时返回 name=code, price=0, change_pct=0
    """
    try:
        parts = _sina_raw_parts(code)
        if len(parts) >= 4:
            price = float(parts[3]) if parts[3] else 0
            prev = float(parts[2]) if parts[2] else 0
            chg = (price - prev) / prev * 100 if prev > 0 else 0
            return {
                "name": parts[0],
                "price": price,
                "prev_close": prev,
                "change_pct": round(chg, 2),
                "open": float(parts[1]) if len(parts) > 1 and parts[1] else 0,
                "high": float(parts[4]) if len(parts) > 4 and parts[4] else 0,
                "low": float(parts[5]) if len(parts) > 5 and parts[5] else 0,
                "volume": float(parts[8]) if len(parts) > 8 and parts[8] else 0,
            }
    except Exception:
        logger.warning(f"新浪行情获取失败: {code}")
    return {"name": code, "price": 0, "change_pct": 0, "prev_close": 0, "open": 0, "high": 0, "low": 0, "volume": 0}


def sina_index_quote(index_code: str) -> dict:
    """获取指数行情
    
    Args:
        index_code: 如 "s_sh000001"（上证）、"s_sz399001"（深证）、"s_sz399006"（创业板）
    """
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={index_code}", headers=SINA_HEADERS, timeout=5)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if m:
            parts = m.group(1).split(",")
            if len(parts) >= 4:
                price = float(parts[3]) if parts[3] else 0
                prev = float(parts[2]) if parts[2] else 0
                chg = (price - prev) / prev * 100 if prev > 0 else 0
                return {
                    "name": parts[0],
                    "price": price,
                    "prev_close": prev,
                    "change_pct": round(chg, 2),
                }
    except Exception:
        logger.warning(f"新浪指数获取失败: {index_code}")
    return {"name": "", "price": 0, "prev_close": 0, "change_pct": 0}
