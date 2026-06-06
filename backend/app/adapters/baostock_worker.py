import sys
import json
import os
import baostock as bs
from datetime import date, timedelta

sys.stdout = sys.stderr
bs.login()
sys.stdout = os.fdopen(1, "w", buffering=1)

_stock_cache = None

def _load_stocks():
    global _stock_cache
    if _stock_cache is not None:
        return _stock_cache
    rs = bs.query_stock_basic()
    _stock_cache = []
    while rs.next():
        row = rs.get_row_data()
        code, name = row[0], row[1]
        _stock_cache.append((code, name))
    return _stock_cache

def _get_name(bs_code):
    for code, name in _load_stocks():
        if code == bs_code:
            return name
    return ""

def to_bs_code(code):
    if code.startswith("sh.") or code.startswith("sz."):
        return code
    return f"{'sh' if code.startswith('6') else 'sz'}.{code}"

while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        req = json.loads(line)
        method = req["method"]
        if method == "kline":
            bs_code = to_bs_code(req["code"])
            rs = bs.query_history_k_data_plus(
                bs_code, "date,open,high,low,close,volume",
                start_date=req["start"], end_date=req["end"],
                frequency=req.get("freq", "d"), adjustflag="3",
            )
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            result = [{"date": r[0], "open": float(r[1]), "high": float(r[2]),
                       "low": float(r[3]), "close": float(r[4]), "volume": float(r[5])} for r in rows]
        elif method == "realtime":
            bs_code = to_bs_code(req["code"])
            name = _get_name(bs_code)
            end = date.today().strftime("%Y-%m-%d")
            start = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
            rs = bs.query_history_k_data_plus(bs_code, "date,open,high,low,close,volume,preclose,pctChg", start_date=start, end_date=end, frequency="d", adjustflag="3")
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            if not rows:
                result = {"error": f"未找到股票: {req['code']}"}
            else:
                latest = rows[-1]
                prev_close_val = float(latest[6]) if latest[6] else float(latest[4])
                result = {
                    "code": req["code"], "name": name,
                    "price": float(latest[4]),
                    "change": round(float(latest[4]) - prev_close_val, 2),
                    "change_pct": float(latest[7]) if latest[7] else 0,
                    "volume": float(latest[5]),
                    "high": float(latest[3]), "low": float(latest[2]),
                    "open": float(latest[1]), "pre_close": prev_close_val,
                }
        elif method == "search":
            kw = req["keyword"]
            results = []
            for code, name in _load_stocks():
                if kw.lower() in code.lower() or kw in name:
                    results.append({"code": code.split(".")[-1], "name": name})
                if len(results) >= 20:
                    break
            result = results
        elif method == "exit":
            break
        else:
            result = {"error": f"未知方法: {method}"}
        sys.stdout.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(json.dumps({"error": str(e)}, ensure_ascii=False) + "\n")
        sys.stdout.flush()

bs.logout()
