import requests, re
import logging
import akshare as ak
import pandas as pd
from datetime import datetime

SINA_HEADERS = {'Referer': 'https://finance.sina.com.cn'}

# Row indices in stock_financial_abstract (stable ordering)

def _sf(v, d=0.0):
    try:
        f = float(v)
        import pandas as pd, math
        return d if pd.isna(f) or math.isinf(f) else f
    except Exception:
        return d

IDX_NET_PROFIT   = 0
IDX_REVENUE      = 1
IDX_EQUITY       = 5
IDX_GOODWILL     = 6
IDX_OPERATING_CF = 7
IDX_EPS          = 8
IDX_BPS          = 9
IDX_ROE          = 11
IDX_DEBT_RATIO   = 16
IDX_REV_PER_SHARE = 32

class FinancialService:

    def _sina_quote(self, code):
        prefix = 'sh' + code if code.startswith(('6','9')) else 'sz' + code
        url = f'http://hq.sinajs.cn/list={prefix}'
        resp = requests.get(url, headers=SINA_HEADERS, timeout=10)
        resp.encoding = 'gbk'
        m = re.search(r'"([^"]*)"', resp.text)
        if not m:
            return {'name': code, 'price': 0.0}
        parts = m.group(1).split(',')
        return {'name': parts[0], 'price': float(parts[3])}

    def _get_df(self, code):
        return ak.stock_financial_abstract(symbol=code)

    def get_financial_overview(self, code):
        q = self._sina_quote(code)
        try:
            df = self._get_df(code)
        except Exception:
            return {'code': code, 'name': q['name'], 'data': []}
        cols = sorted([c for c in df.columns if str(c).startswith('20')])[-20:]
        result = []
        for c in cols:
            d = f'{c[:4]}-{c[4:6]}-{c[6:]}'
            try: rev = float(df.iloc[IDX_REVENUE][c]) / 1e8
            except Exception: rev = 0.0
            try: prf = float(df.iloc[IDX_NET_PROFIT][c]) / 1e8
            except Exception: prf = 0.0
            try: csh = float(df.iloc[IDX_OPERATING_CF][c]) / 1e8
            except Exception: csh = 0.0
            result.append({'date': d, 'revenue': round(rev,2), 'net_profit': round(prf,2), 'cash_flow': _sf(round(csh,2))})
        return {'code': code, 'name': q['name'], 'data': result}

    def get_valuation(self, code):
        q = self._sina_quote(code)
        price = q['price']
        pe = pb = ps = roe = 0.0
        try:
            df = self._get_df(code)
            latest = sorted([c for c in df.columns if str(c).startswith('2025') or str(c).startswith('2026')])[-1]
            eps = float(df.iloc[IDX_EPS][latest])
            bps = float(df.iloc[IDX_BPS][latest])
            rps = float(df.iloc[IDX_REV_PER_SHARE][latest])
            roe = round(float(df.iloc[IDX_ROE][latest]), 2)
            pe = round(price / eps, 2) if eps > 0 else 0
            pb = round(price / bps, 2) if bps > 0 else 0
            ps = round(price / rps, 2) if rps > 0 else 0
        except Exception:
            pass
        return {'code': code, 'name': q['name'], 'pe': pe, 'pb': pb, 'ps': ps, 'roe': roe, 'dividend_yield': 0.0, 'industry_pe': 0.0}

    def get_risk(self, code):
        q = self._sina_quote(code)
        risk_items = []
        debt_ratio = pledge_ratio = goodwill_ratio = 0.0
        cash_flow_health = 'N/A'
        try:
            df = self._get_df(code)
            latest = sorted([c for c in df.columns if str(c).startswith('2025') or str(c).startswith('2026')])[-1]
            debt_ratio = round(float(df.iloc[IDX_DEBT_RATIO][latest]), 2)
            try:
                gw = float(df.iloc[IDX_GOODWILL][latest])
                import math
                eq = float(df.iloc[IDX_EQUITY][latest])
                goodwill_ratio = round(gw / eq * 100, 2) if eq > 0 and not math.isnan(gw) else 0
            except Exception: pass
            try:
                recent_cols = sorted([c for c in df.columns if str(c).startswith('2025') or str(c).startswith('2026')])[-4:]
                total_cf = sum(float(df.iloc[IDX_OPERATING_CF][c]) for c in recent_cols)
                total_np = sum(float(df.iloc[IDX_NET_PROFIT][c]) for c in recent_cols)
                ratio = round(total_cf / total_np, 2) if total_np > 0 else 0
                if ratio > 1:
                    cash_flow_health = '\u5065\u5eb7'
                elif ratio > 0.5:
                    cash_flow_health = '\u5173\u6ce8'
                else:
                    cash_flow_health = '\u9884\u8b66'
                    risk_items.append(f'\u7ecf\u8425\u73b0\u91d1\u6d41/\u51c0\u5229\u6da6\u6bd4\u4ec5{ratio}\uff0c\u5229\u6da6\u542b\u91d1\u91cf\u4e0d\u8db3')
            except Exception: pass
            try:
                pledge_df = ak.stock_gpzy_pledge_ratio_em()
                code_col = pledge_df.columns[0]
                pledge_row = pledge_df[pledge_df[code_col] == code]
                if len(pledge_row) > 0:
                    ratio_col = pledge_df.columns[1]
                    pledge_ratio = float(pledge_row.iloc[0][ratio_col])
            except Exception: pass
        except Exception as e:
            risk_items.append(f'\u6570\u636e\u83b7\u53d6\u5f02\u5e38: {e}')

        if debt_ratio > 70:
            risk_items.append(f'\u8d44\u4ea7\u8d1f\u503a\u7387 {debt_ratio}%\uff0c\u504f\u9ad8')
        elif debt_ratio > 50:
            risk_items.append(f'\u8d44\u4ea7\u8d1f\u503a\u7387 {debt_ratio}%\uff0c\u9002\u4e2d')

        if goodwill_ratio > 30:
            risk_items.append(f'\u5546\u8a89\u5360\u51c0\u8d44\u4ea7 {goodwill_ratio}%\uff0c\u51cf\u503c\u98ce\u9669\u9ad8')
        elif goodwill_ratio > 10:
            risk_items.append(f'\u5546\u8a89\u5360\u51c0\u8d44\u4ea7 {goodwill_ratio}%\uff0c\u9700\u5173\u6ce8')

        if pledge_ratio > 30:
            risk_items.append(f'\u8d28\u62bc\u6bd4\u4f8b {pledge_ratio}%\uff0c\u504f\u9ad8')

        risk_count = 0
        for r in risk_items:
            if any(w in r for w in ['\u9884\u8b66','\u504f\u9ad8','\u51cf\u503c','\u542b\u91d1\u91cf']):
                risk_count += 1
        if risk_count >= 2:
            risk_level = '\u9ad8'
        elif risk_count >= 1:
            risk_level = '\u4e2d'
        else:
            risk_level = '\u4f4e'

        return {'code': code, 'name': q['name'], 'debt_ratio': debt_ratio, 'pledge_ratio': pledge_ratio, 'cash_flow_health': cash_flow_health, 'goodwill_ratio': goodwill_ratio, 'risk_level': risk_level, 'risk_items': risk_items}

    def get_holders(self, code):
        q = self._sina_quote(code)
        holders = []
        try:
            df = ak.stock_gdfx_top_10_em(date=datetime.now().strftime('%Y%m%d'))
            sub = df[df.iloc[:,0] == code]
            for _, row in sub.iterrows():
                holders.append({
                    'name': str(row.iloc[1]) if len(row) > 1 else '',
                    'ratio': float(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 0,
                    'change': str(row.iloc[3]) if len(row) > 3 else '\u4e0d\u53d8',
                })
        except Exception: pass
        return {'code': code, 'name': q['name'], 'top_holders': holders, 'institution_change': '\u6682\u65e0\u6570\u636e'}


_financial_service = FinancialService()

def get_financial_service():
    return _financial_service

# test
if __name__ == '__main__':
    s = FinancialService()
    print(s.get_valuation('600519'))