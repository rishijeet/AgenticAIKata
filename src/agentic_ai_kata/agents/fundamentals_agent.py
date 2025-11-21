import math
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf


class FundamentalsAgent:
    """
    Collects basic fundamentals for a given ticker using yfinance.
    Attempts to be robust to missing fields.
    """

    def _safe_get(self, d: Dict[str, Any], key: str) -> Optional[Any]:
        try:
            return d.get(key)
        except Exception:
            return None

    def _fast_get(self, fast: Any, attr: str) -> Optional[Any]:
        try:
            return getattr(fast, attr)
        except Exception:
            return None

    def _first_value(self, series: pd.Series) -> Optional[Any]:
        try:
            return series.dropna().iloc[0] if not series.empty else None
        except Exception:
            return None

    def fetch(self, ticker: str) -> Dict[str, Any]:
        t = yf.Ticker(ticker)

        # Prefer get_info (yfinance >= 0.2.40) but fall back gracefully
        info: Dict[str, Any] = {}
        try:
            if hasattr(t, "get_info"):
                info = t.get_info() or {}
            else:
                # Older path: may be unavailable in future
                info = getattr(t, "info", {}) or {}
        except Exception:
            info = {}

        # Fast info is cheaper and reliable for price/market cap
        fast: Any = None
        try:
            fast = getattr(t, "fast_info", None)
        except Exception:
            fast = None

        # Price & valuation
        last_price = (self._fast_get(fast, "last_price") if fast is not None else None) or self._safe_get(info, "currentPrice")
        currency = (self._fast_get(fast, "currency") if fast is not None else None) or self._safe_get(info, "currency")
        market_cap = (self._fast_get(fast, "market_cap") if fast is not None else None) or self._safe_get(info, "marketCap")

        trailing_pe = self._safe_get(info, "trailingPE")
        forward_pe = self._safe_get(info, "forwardPE")
        price_to_book = self._safe_get(info, "priceToBook")

        # Identity
        long_name = self._safe_get(info, "longName") or self._safe_get(info, "shortName")
        sector = self._safe_get(info, "sector")
        industry = self._safe_get(info, "industry")
        exchange = self._safe_get(info, "exchange") or self._safe_get(info, "fullExchangeName")

        # Financial statements
        revenue = None
        net_income = None
        free_cash_flow = None
        try:
            fin = t.financials  # annual
            if isinstance(fin, pd.DataFrame) and not fin.empty:
                if "Total Revenue" in fin.index:
                    revenue = self._first_value(fin.loc["Total Revenue"])  # latest column
                if "Net Income" in fin.index:
                    net_income = self._first_value(fin.loc["Net Income"])  # latest column
        except Exception:
            pass
        try:
            cf = t.cashflow  # annual cashflow
            if isinstance(cf, pd.DataFrame) and not cf.empty:
                # yfinance may label as 'Free Cash Flow' or 'FreeCashFlow'
                for key in ["Free Cash Flow", "FreeCashFlow"]:
                    if key in cf.index:
                        free_cash_flow = self._first_value(cf.loc[key])
                        break
        except Exception:
            pass

        return {
            "ticker": ticker.upper(),
            "identity": {
                "name": long_name,
                "sector": sector,
                "industry": industry,
                "exchange": exchange,
            },
            "price": {
                "last": last_price,
                "currency": currency,
            },
            "valuation": {
                "market_cap": market_cap,
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "price_to_book": price_to_book,
            },
            "financials": {
                "revenue": revenue,
                "net_income": net_income,
                "free_cash_flow": free_cash_flow,
            },
            "raw_info_available": bool(info),
        }
