from polygon import RESTClient
from dotenv import load_dotenv
import os
from datetime import datetime, date, timedelta
import random
from database import write_market, read_market
from functools import lru_cache
from datetime import timezone

load_dotenv(override=True)

polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"


def is_market_open() -> bool:
    client = RESTClient(polygon_api_key)
    market_status = client.get_market_status()
    return market_status.market == "open"


def _last_trading_day() -> date:
    """Return the most recent completed trading day (never today)."""
    d = datetime.now(tz=timezone.utc).date() - timedelta(days=1)
    while d.weekday() >= 5:  # skip Saturday (5) and Sunday (6)
        d -= timedelta(days=1)
    return d


def get_all_share_prices_polygon_eod() -> dict[str, float]:
    """With much thanks to student Reema R. for fixing the timezone issue with this!"""
    client = RESTClient(polygon_api_key)

    # Determine the last completed trading day.  The probe can fail during
    # market hours on the free plan, so fall back to the calculated date.
    try:
        probe = client.get_previous_close_agg("SPY")[0]
        last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
        today = datetime.now(tz=timezone.utc).date()
        if last_close >= today:
            last_close = _last_trading_day()
    except Exception:
        last_close = _last_trading_day()

    results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
    return {result.ticker: result.close for result in results}


@lru_cache(maxsize=2)
def get_market_for_prior_date(today):
    market_data = read_market(today)
    if not market_data:
        try:
            market_data = get_all_share_prices_polygon_eod()
            if market_data:
                write_market(today, market_data)
        except Exception as e:
            # Cache the failure as an empty dict so subsequent calls don't
            # retry the API and trigger a 429 rate-limit cascade.
            print(f"Could not fetch market data from Polygon: {e}")
            market_data = {}
    return market_data


def get_share_price_polygon_eod(symbol) -> float:
    today = datetime.now().date().strftime("%Y-%m-%d")
    market_data = get_market_for_prior_date(today)
    price = market_data.get(symbol)
    if price is None:
        raise ValueError(f"No price available for {symbol}")
    return price


def get_share_price_polygon_min(symbol) -> float:
    client = RESTClient(polygon_api_key)
    result = client.get_snapshot_ticker("stocks", symbol)
    return result.min.close or result.prev_day.close


def get_share_price_polygon(symbol) -> float:
    if is_paid_polygon:
        return get_share_price_polygon_min(symbol)
    else:
        return get_share_price_polygon_eod(symbol)


def get_share_price(symbol) -> float:
    if polygon_api_key:
        try:
            price = get_share_price_polygon(symbol)
            if price:
                return price
        except ValueError:
            pass  # market data unavailable (already logged at fetch time)
        except Exception as e:
            print(f"Was not able to use the polygon API due to {e}; using a random number")
    return float(random.randint(1, 100))
