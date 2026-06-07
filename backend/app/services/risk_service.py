import requests, re, json
from datetime import date
from openai import OpenAI
from app.core.config import settings

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}


def _sina_name(code: str) -> str:
    prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if m: return m.group(1).split(",")[0]
    except: pass
    return code


class RiskService:

    def check_stock_risk(self, code: str) -> dict:
        """个股风险筛查"""
        name = _sina_name(code)
        items = []
        overall = "low"

        try:
            # 获取实时行情做简单风险判断
            prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
            resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers=SINA_HEADERS, timeout=10)
            resp.encoding = "gbk"
            m = re.search(r'"([^"]*)"', resp.text)
            if m:
                parts = m.group(1).split(",")
                if len(parts) >= 6:
                    price = float(parts[3]) if parts[3] else 0
                    prev_close = float(parts[2]) if parts[2] else 0
                    high = float(parts[4]) if parts[4] else 0
                    low = float(parts[5]) if parts[5] else 0

                    if prev_close > 0:
                        change_pct = (price - prev_close) / prev_close * 100
                        if abs(change_pct) > 9:
                            items.append({
                                "type": "price", "severity": "high",
                                "description": f"股价异动：涨跌幅 {change_pct:.1f}%",
                                "detail": "可能存在重大利好/利空消息"
                            })
                            overall = "high"
                        elif abs(change_pct) > 5:
                            items.append({
                                "type": "price", "severity": "medium",
                                "description": f"股价较大波动：涨跌幅 {change_pct:.1f}%",
                                "detail": ""
                            })
                            if overall != "high": overall = "medium"

                    if high > 0 and low > 0 and price > 0:
                        amplitude = (high - low) / price * 100
                        if amplitude > 10:
                            items.append({
                                "type": "price", "severity": "medium",
                                "description": f"日内振幅过大：{amplitude:.1f}%",
                                "detail": "可能存在多空分歧加剧"
                            })
        except Exception:
            pass

        # AI 风险分析
        suggestion = ""
        if settings.openai_api_key and items:
            try:
                risks_text = "\n".join(f"- {i['description']}" for i in items)
                prompt = f"""对股票 {name}({code}) 的风险信号做简要评估，给出1-2句话建议：
{risks_text}"""
                client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
                resp = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150, temperature=0.7,
                )
                suggestion = resp.choices[0].message.content or ""
            except Exception:
                pass

        return {
            "code": code, "name": name,
            "overall_risk": overall,
            "items": items,
            "suggestion": suggestion or "未发现显著风险信号",
        }

    def get_market_risk(self) -> dict:
        """大盘系统性风险"""
        today = date.today().isoformat()
        signals = []
        risk_level = "low"

        try:
            # 获取三大指数
            indices = ["s_sh000001", "s_sz399001", "s_sz399006"]
            names = ["上证指数", "深证成指", "创业板指"]
            for idx, nm in zip(indices, names):
                resp = requests.get(f"http://hq.sinajs.cn/list={idx}", headers=SINA_HEADERS, timeout=10)
                resp.encoding = "gbk"
                m = re.search(r'"([^"]*)"', resp.text)
                if m:
                    parts = m.group(1).split(",")
                    if len(parts) >= 4:
                        price = float(parts[3]) if parts[3] else 0
                        prev = float(parts[2]) if parts[2] else 0
                        if prev > 0:
                            chg = (price - prev) / prev * 100
                            if chg < -3:
                                signals.append(f"{nm} 跌幅超3% ({chg:.1f}%)")
                                risk_level = "high"
                            elif chg < -1.5:
                                signals.append(f"{nm} 跌幅超1.5% ({chg:.1f}%)")
                                if risk_level != "high": risk_level = "medium"
        except Exception:
            pass

        return {
            "date": today,
            "risk_level": risk_level,
            "signals": signals,
            "description": "监测到系统风险信号" if signals else "大盘运行正常",
        }

    def check_portfolio_risks(self, positions: list[dict]) -> list[dict]:
        """持仓风控检查"""
        results = []
        for pos in positions:
            code = pos.get("code", "")
            name = pos.get("name", "") or _sina_name(code)
            risk_flags = []
            stop_loss = 0
            take_profit = 0

            try:
                prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
                resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers=SINA_HEADERS, timeout=5)
                resp.encoding = "gbk"
                m = re.search(r'"([^"]*)"', resp.text)
                if m:
                    parts = m.group(1).split(",")
                    if len(parts) >= 4:
                        price = float(parts[3]) if parts[3] else 0
                        if price > 0:
                            cost = pos.get("cost_price", price)
                            pl_pct = (price - cost) / cost * 100 if cost > 0 else 0
                            stop_loss = round(cost * 0.93, 2)
                            take_profit = round(cost * 1.15, 2)
                            if pl_pct < -7:
                                risk_flags.append(f"浮亏超7% ({pl_pct:.1f}%)")
                            elif pl_pct > 20:
                                risk_flags.append(f"浮盈超20%，考虑止盈 ({pl_pct:.1f}%)")
                            if price <= stop_loss:
                                risk_flags.append("触及止损线")
            except Exception:
                pass

            results.append({
                "code": code, "name": name,
                "weight_pct": pos.get("weight_pct", 0),
                "risk_flags": risk_flags,
                "stop_loss_price": stop_loss,
                "take_profit_price": take_profit,
            })
        return results


_risk_service: RiskService | None = None


def get_risk_service() -> RiskService:
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskService()
    return _risk_service
