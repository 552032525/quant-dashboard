import asyncio
import json
import subprocess
import sys
import os
from datetime import date
from app.adapters.base import DataSourceAdapter

WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baostock_worker.py")

class BaostockAdapter(DataSourceAdapter):
    def __init__(self):
        self._proc = subprocess.Popen(
            [sys.executable, "-u", WORKER_PATH],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1,
        )

    def _call(self, req: dict) -> dict:
        self._proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        result = json.loads(line)
        if "error" in result:
            raise ValueError(result["error"])
        return result

    async def get_realtime_quote(self, code: str) -> dict:
        return await asyncio.to_thread(self._get_realtime_quote, code)

    def _get_realtime_quote(self, code: str) -> dict:
        return self._call({"method": "realtime", "code": code})

    async def get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        return await asyncio.to_thread(self._get_kline, code, start_date, end_date, period)

    def _get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
        freq_map = {"daily": "d", "weekly": "w", "monthly": "m"}
        return self._call({
            "method": "kline", "code": code,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "freq": freq_map.get(period, "d"),
        })

    async def search_symbol(self, keyword: str) -> list[dict]:
        return await asyncio.to_thread(self._search_symbol, keyword)

    def _search_symbol(self, keyword: str) -> list[dict]:
        return self._call({"method": "search", "keyword": keyword})

    def __del__(self):
        try:
            self._proc.stdin.write(json.dumps({"method": "exit"}) + "\n")
            self._proc.stdin.flush()
            self._proc.wait(timeout=3)
        except Exception:
            self._proc.kill()
