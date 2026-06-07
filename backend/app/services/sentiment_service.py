import requests, re
import logging
from datetime import datetime
from openai import OpenAI
from app.core.config import settings

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}


def _prefix(code: str) -> str:
    if code.startswith(("8", "4")) or (len(code) == 6 and code.startswith("92")):
        return "bj" + code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code


def _sina_name(code: str) -> str:
    prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
    url = f"http://hq.sinajs.cn/list={prefix}"
    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if m:
            return m.group(1).split(",")[0]
    except Exception:
        pass
    return code


class SentimentService:

    # ─── 个股新闻 ───────────────────────────────────────────
    def get_stock_news(self, code: str) -> dict:
        """新浪个股新闻搜索"""
        name = _sina_name(code)
        items = []
        try:
            url = (
                f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                f"Market_Center.getHQNodeData?page=1&num=20&sort=symbol&asc=1"
                f"&node=zxqy&symbol={code}&_s_r_a=init"
            )
            resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
            resp.encoding = "gbk"
            data = resp.json()
            for item in data[:20]:
                items.append({
                    "title": item.get("name", ""),
                    "summary": item.get("symbol", ""),
                    "source": "新浪财经",
                    "time": item.get("trade", ""),
                    "url": f"https://finance.sina.com.cn/realstock/company/{_prefix(code)}/nc.shtml",
                    "sentiment": None,
                })
        except Exception:
            # 用备用方式：直接搜索
            try:
                url = f"https://search.sina.com.cn/?q={code}+股票&range=all&c=news&sort=time"
                resp = requests.get(url, headers={**SINA_HEADERS, "User-Agent": "Mozilla/5.0"}, timeout=10)
                resp.encoding = "utf-8"
                # 简单解析标题
                titles = re.findall(r'<h2[^>]*><a[^>]*>([^<]+)</a>', resp.text)
                for t in titles[:15]:
                    items.append({
                        "title": t.strip(),
                        "summary": "",
                        "source": "新浪搜索",
                        "time": "",
                        "url": "",
                        "sentiment": None,
                    })
            except Exception:
                pass

        return {"code": code, "name": name, "items": items}

    # ─── 市场热点 ───────────────────────────────────────────
    def get_market_news(self) -> dict:
        """市场热点新闻"""
        hot = []
        breaking = []
        try:
            # 新浪财经首页新闻
            url = "https://finance.sina.com.cn/"
            resp = requests.get(url, headers={**SINA_HEADERS, "User-Agent": "Mozilla/5.0"}, timeout=10)
            resp.encoding = "utf-8"
            titles = re.findall(r'<a[^>]*>([^<]{8,60})</a>', resp.text)
            seen = set()
            for t in titles:
                t = t.strip()
                if len(t) >= 8 and t not in seen and not t.startswith("<"):
                    seen.add(t)
                    hot.append({
                        "title": t, "summary": "", "source": "新浪财经",
                        "time": datetime.now().strftime("%H:%M"), "url": "", "sentiment": None,
                    })
                if len(hot) >= 15:
                    break
        except Exception:
            pass
        return {"hot_topics": hot, "breaking_news": breaking}

    # ─── AI 情感评分 ────────────────────────────────────────
    def analyze_sentiment(self, code: str, news_texts: list[str]) -> dict:
        """用 AI 对新闻列表做情感打分"""
        name = _sina_name(code)
        if not settings.openai_api_key or not news_texts:
            return {
                "code": code, "name": name,
                "overall": 0, "positive_count": 0, "negative_count": 0,
                "neutral_count": len(news_texts), "key_topics": [],
            }

        joined = "\n".join(f"{i+1}. {t}" for i, t in enumerate(news_texts[:15]))
        prompt = f"""分析以下关于股票 {name}({code}) 的新闻标题，对每条的 sentiment 打分（-1=利空, 0=中性, 1=利好），
并提取3-5个关键议题。只返回JSON格式：{{"scores": [每个标题的分数], "topics": ["议题1","议题2"]}}"

新闻标题：
{joined}"""

        try:
            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            import json
            text = resp.choices[0].message.content or "{}"
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(text)
            scores = data.get("scores", [])
            pos = sum(1 for s in scores if s > 0.3)
            neg = sum(1 for s in scores if s < -0.3)
            neu = len(scores) - pos - neg
            overall = sum(scores) / len(scores) if scores else 0
            return {
                "code": code, "name": name,
                "overall": round(overall, 2),
                "positive_count": pos, "negative_count": neg,
                "neutral_count": neu,
                "key_topics": data.get("topics", []),
            }
        except Exception:
            return {
                "code": code, "name": name,
                "overall": 0, "positive_count": 0, "negative_count": 0,
                "neutral_count": len(news_texts), "key_topics": [],
            }

    # ─── 研报摘要 ───────────────────────────────────────────
    def summarize_research(self, code: str, content: str = "") -> dict:
        """AI 生成研报摘要"""
        name = _sina_name(code)
        if not settings.openai_api_key:
            return {
                "code": code, "name": name,
                "content": "未配置 OpenAI API Key", "key_points": [], "rating": "",
            }

        prompt = f"""你是一个A股分析师。请对以下关于 {name}({code}) 的材料进行摘要，提取3-5个要点，并给出评级（买入/增持/持有/减持/卖出）。

材料内容：
{content if content else f"请基于公开信息对{name}({code})做简要分析"}

请以JSON格式返回：{{"summary": "200字摘要", "points": ["要点1","要点2","要点3"], "rating": "评级"}}"""

        try:
            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            import json
            text = resp.choices[0].message.content or "{}"
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(text)
            return {
                "code": code, "name": name,
                "content": data.get("summary", ""),
                "key_points": data.get("points", []),
                "rating": data.get("rating", ""),
            }
        except Exception as e:
            return {
                "code": code, "name": name,
                "content": f"生成失败: {str(e)}", "key_points": [], "rating": "",
            }


_sentiment_service: SentimentService | None = None


def get_sentiment_service() -> SentimentService:
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service