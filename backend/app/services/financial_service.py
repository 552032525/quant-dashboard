import akshare as ak
from datetime import datetime

class FinancialService:

    def get_financial_overview(self, code: str) -> dict:
        """获取近5年营收/利润/现金流"""
        df = ak.stock_financial_abstract(symbol=code)
        df = df[df["选项"] == "常用指标"].copy()
        cols = ["指标", "20230331", "20230630", "20230930", "20231231",
                "20240331", "20240630", "20240930", "20241231",
                "20250331", "20250630", "20250930", "20251231",
                "20260331"]
        available = [c for c in cols if c in df.columns]
        sub = df[available].copy()
        revenue_row = sub[sub["指标"] == "营业总收入"]
        profit_row = sub[sub["指标"] == "归母净利润"]
        cash_row = sub[sub["指标"] == "经营活动产生的现金流量净额"]

        dates = [c for c in available if c != "指标"]
        result = []
        for d in dates[-20:]:
            d_formatted = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            rev = float(revenue_row[d].iloc[0]) / 1e8 if len(revenue_row) > 0 and revenue_row[d].notna().iloc[0] else 0
            prf = float(profit_row[d].iloc[0]) / 1e8 if len(profit_row) > 0 and profit_row[d].notna().iloc[0] else 0
            csh = float(cash_row[d].iloc[0]) / 1e8 if len(cash_row) > 0 and cash_row[d].notna().iloc[0] else 0
            result.append({"date": d_formatted, "revenue": round(rev, 2), "net_profit": round(prf, 2), "cash_flow": round(csh, 2)})

        name = ""
        try:
            df2 = ak.stock_individual_info_em(symbol=code)
            name = str(df2[df2["item"] == "股票简称"]["value"].iloc[0])
        except Exception:
            name = code
        return {"code": code, "name": name, "data": result}

    def get_valuation(self, code: str) -> dict:
        """获取估值指标"""
        name = code
        pe = pb = ps = roe = dividend_yield = 0.0
        row = {}
        try:
            df = ak.stock_individual_info_em(symbol=code)
            row = {r["item"]: r["value"] for _, r in df.iterrows()}
            name = str(row.get("股票简称", code))
            pe = float(row.get("市盈率-动态", 0) or 0)
            pb = float(row.get("市净率", 0) or 0)
            roe = float(row.get("净资产收益率", 0) or 0)
            try:
                div_df = ak.stock_history_dividend_detail(symbol=code, indicator="分红")
                if len(div_df) > 0:
                    total_div = float(div_df.iloc[0].get("派息", 0) or 0)
                    price = float(row.get("最新价", 0) or 0)
                    if price > 0:
                        dividend_yield = round(total_div / price * 100, 2)
            except Exception:
                pass
        except Exception:
            pass
        try:
            price = float(row.get("最新价", 0) or 0)
            total_shares = float(row.get("总股本", 0) or 0)
            overview = self.get_financial_overview(code)
            if overview["data"]:
                latest_rev = overview["data"][-1]["revenue"]
                if latest_rev > 0 and total_shares > 0:
                    ps = round((price * total_shares) / (latest_rev * 1e8) * 1e8, 2)
        except Exception:
            pass
        return {"code": code, "name": name, "pe": pe, "pb": pb, "ps": ps,
                "roe": roe, "dividend_yield": dividend_yield, "industry_pe": 0.0}

    def get_risk(self, code: str) -> dict:
        """风险筛查"""
        name = code
        debt_ratio = pledge_ratio = goodwill_ratio = 0.0
        risk_items = []
        cash_flow_health = "关注"
        try:
            df = ak.stock_financial_abstract(symbol=code)
            df = df[df["选项"] == "常用指标"].copy()
            debt_rows = df[df["指标"] == "资产负债率"]
            if len(debt_rows) > 0:
                latest_col = sorted([c for c in df.columns if c.startswith("202")])[-1]
                debt_ratio = float(debt_rows[latest_col].iloc[0]) if debt_rows[latest_col].notna().iloc[0] else 0

            gw_rows = df[df["指标"] == "商誉"]
            net_rows = df[df["指标"] == "归属于母公司股东权益合计"]
            if len(gw_rows) > 0 and len(net_rows) > 0:
                latest_col = sorted([c for c in df.columns if c.startswith("202")])[-1]
                gw = float(gw_rows[latest_col].iloc[0]) if gw_rows[latest_col].notna().iloc[0] else 0
                net = float(net_rows[latest_col].iloc[0]) if net_rows[latest_col].notna().iloc[0] else 1
                goodwill_ratio = round(gw / net * 100, 2) if net > 0 else 0

            cash_rows = df[df["指标"] == "经营活动产生的现金流量净额"]
            profit_rows = df[df["指标"] == "归母净利润"]
            if len(cash_rows) > 0 and len(profit_rows) > 0:
                latest_cols = sorted([c for c in df.columns if c.startswith("202")])[-4:]
                total_cash = sum(float(cash_rows[c].iloc[0]) for c in latest_cols if cash_rows[c].notna().iloc[0])
                total_profit = sum(float(profit_rows[c].iloc[0]) for c in latest_cols if profit_rows[c].notna().iloc[0])
                ratio = round(total_cash / total_profit, 2) if total_profit > 0 else 0
                if ratio > 1:
                    cash_flow_health = "健康"
                elif ratio > 0.5:
                    cash_flow_health = "关注"
                else:
                    cash_flow_health = "预警"
                    risk_items.append(f"经营现金流/净利润比仅{ratio}，利润含金量不足")

            try:
                pledge_df = ak.stock_gpzy_pledge_ratio_em()
                pledge_row = pledge_df[pledge_df["股票代码"] == code]
                if len(pledge_row) > 0:
                    pledge_ratio = float(pledge_row.iloc[0]["质押比例"]) if pledge_row["质押比例"].notna().iloc[0] else 0
            except Exception:
                pass

            try:
                info = ak.stock_individual_info_em(symbol=code)
                name = str(info[info["item"] == "股票简称"]["value"].iloc[0])
            except Exception:
                name = code

        except Exception as e:
            return {"code": code, "name": name, "debt_ratio": 0, "pledge_ratio": 0,
                    "cash_flow_health": "关注", "goodwill_ratio": 0,
                    "risk_level": "中", "risk_items": [f"数据获取异常: {e}"]}

        if debt_ratio > 70:
            risk_items.append(f"资产负债率 {debt_ratio}%，偏高")
        elif debt_ratio > 50:
            risk_items.append(f"资产负债率 {debt_ratio}%，适中")

        if goodwill_ratio > 30:
            risk_items.append(f"商誉占净资产 {goodwill_ratio}%，减值风险高")
        elif goodwill_ratio > 10:
            risk_items.append(f"商誉占净资产 {goodwill_ratio}%，需关注")

        if pledge_ratio > 30:
            risk_items.append(f"质押比例 {pledge_ratio}%，偏高")

        risk_count = len([r for r in risk_items if "预警" in cash_flow_health or "偏高" in r or "减值" in r or "含金量" in r])
        if risk_count >= 2:
            risk_level = "高"
        elif risk_count >= 1:
            risk_level = "中"
        else:
            risk_level = "低"

        return {"code": code, "name": name, "debt_ratio": debt_ratio, "pledge_ratio": pledge_ratio,
                "cash_flow_health": cash_flow_health, "goodwill_ratio": goodwill_ratio,
                "risk_level": risk_level, "risk_items": risk_items}

    def get_holders(self, code: str) -> dict:
        """获取十大股东"""
        name = code
        holders = []
        try:
            df = ak.stock_gdfx_top_10_em(date=datetime.now().strftime("%Y%m%d"))
            sub = df[df["代码"] == code]
            if len(sub) > 0:
                name = str(sub.iloc[0].get("名称", code))
                for _, row in sub.iterrows():
                    holders.append({
                        "name": str(row.get("股东名称", "")),
                        "ratio": float(row.get("持股比例", 0) or 0),
                        "change": str(row.get("变动方向", "不变")),
                    })
        except Exception:
            pass
        return {"code": code, "name": name, "top_holders": holders, "institution_change": "暂无数据"}


_financial_service = FinancialService()

def get_financial_service() -> FinancialService:
    return _financial_service
