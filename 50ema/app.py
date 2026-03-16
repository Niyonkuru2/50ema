"""
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from ta.trend import EMAIndicator

app = FastAPI(title="Pullback Structure Strategy API")

class MarketData(BaseModel):
    values: list  # must include open, high, low, close
    symbol: str
    timeframe: str


def detect_structure(df):
    highs = []
    lows = []

    # Detect swing highs & lows
    for i in range(2, len(df) - 2):
        if df['high'][i] > df['high'][i-1] and df['high'][i] > df['high'][i-2] \
           and df['high'][i] > df['high'][i+1] and df['high'][i] > df['high'][i+2]:
            highs.append(df['high'][i])

        if df['low'][i] < df['low'][i-1] and df['low'][i] < df['low'][i-2] \
           and df['low'][i] < df['low'][i+1] and df['low'][i] < df['low'][i+2]:
            lows.append(df['low'][i])

    if len(highs) < 2 or len(lows) < 2:
        return "NO_STRUCTURE"

    # Last two swings
    if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
        return "UPTREND"

    elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
        return "DOWNTREND"

    return "RANGE"


@app.post("/analyze")
def analyze(data: MarketData):
    df = pd.DataFrame(data.values)

    if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        return {"error": "Missing OHLC data"}

    if len(df) < 60:
        return {"error": "Not enough data"}

    df = df.iloc[::-1].reset_index(drop=True)

    #  Convert all OHLC to float to fix comparison errors
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)

    # EMA50
    df['ema50'] = EMAIndicator(df['close'], window=50).ema_indicator()

    structure = detect_structure(df)

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    signal = "NO_TRADE"
    stop_loss = None
    take_profit = None

    # BUY CONDITIONS
    if structure == "UPTREND":
        if latest['close'] > latest['ema50']:
            # Pullback = previous candle closed near EMA
            if abs(prev['close'] - prev['ema50']) < 0.001:
                # Bullish confirmation candle
                if latest['close'] > latest['open']:
                    signal = "BUY"
                    stop_loss = df['low'].iloc[-5:-1].min()
                    risk = latest['close'] - stop_loss
                    take_profit = latest['close'] + (risk * 2)

    # SELL CONDITIONS
    if structure == "DOWNTREND":
        if latest['close'] < latest['ema50']:
            if abs(prev['close'] - prev['ema50']) < 0.001:
                if latest['close'] < latest['open']:
                    signal = "SELL"
                    stop_loss = df['high'].iloc[-5:-1].max()
                    risk = stop_loss - latest['close']
                    take_profit = latest['close'] - (risk * 2)

    return {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "structure": structure,
        "signal": signal,
        "entry": round(latest['close'], 5),
        "stop_loss": round(stop_loss, 5) if stop_loss else None,
        "take_profit": round(take_profit, 5) if take_profit else None
    }

@app.get("/")
def home():
    return {"message": "Pullback Structure Strategy API running successfully"}
"""

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from ta.trend import EMAIndicator

# ==========================================
# Create FastAPI app
# ==========================================
app = FastAPI(title="Pro M30 Trend Strategy API")


# ==========================================
# Request body structure
# ==========================================
class MarketData(BaseModel):
    values: list   # List of candles with open, high, low, close
    symbol: str
    timeframe: str


@app.post("/analyze")
def analyze(data: MarketData):

    # Convert incoming candle data to DataFrame
    df = pd.DataFrame(data.values)

    # Ensure OHLC columns exist
    if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        return {"error": "Missing OHLC data"}

    # Need enough history for structure + HTF analysis
    if len(df) < 120:
        return {"error": "Not enough data"}

    # Reverse candles so oldest at top, latest at bottom
    df = df.iloc[::-1].reset_index(drop=True)

    # Convert all price values to float
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)

    # ==========================================
    # EMA CALCULATIONS
    # ==========================================

    # M30 trend EMA
    df['ema50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()

    # Higher timeframe proxy (H1/H4) using EMA200
    df['ema200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()

    latest = df.iloc[-1]

    # ==========================================
    # SUPPORT & RESISTANCE (Recent Zones)
    # ==========================================

    # Support = lowest low of last 50 candles
    support = df['low'].iloc[-50:].min()

    # Resistance = highest high of last 50 candles
    resistance = df['high'].iloc[-50:].max()

    # ==========================================
    # MARKET STRUCTURE (Swing Analysis)
    # ==========================================

    # Recent highs/lows for HH/HL detection
    recent_highs = df['high'].iloc[-10:]
    recent_lows = df['low'].iloc[-10:]

    # Higher High pattern
    higher_highs = recent_highs.is_monotonic_increasing

    # Lower Low pattern
    lower_lows = recent_lows.is_monotonic_decreasing

    # ==========================================
    # CONSOLIDATION DETECTION
    # ==========================================

    # Range size of last 20 candles
    recent_range = df['high'].iloc[-20:].max() - df['low'].iloc[-20:].min()

    # Average true movement (proxy)
    avg_range = (df['high'] - df['low']).iloc[-50:].mean()

    # If range is very small → consolidation
    in_consolidation = recent_range < avg_range * 0.8

    # ==========================================
    # VOLATILITY FILTER (News proxy)
    # ==========================================

    # Detect unusually large candle
    last_candle_range = latest['high'] - latest['low']

    high_volatility = last_candle_range > avg_range * 2

    # ==========================================
    # TREND FILTERS
    # ==========================================

    # Higher timeframe trend direction
    htf_up = latest['close'] > latest['ema200']
    htf_down = latest['close'] < latest['ema200']

    # M30 trend direction
    m30_up = latest['close'] > latest['ema50']
    m30_down = latest['close'] < latest['ema50']

    # ==========================================
    # INITIAL OUTPUT VALUES
    # ==========================================
    signal = "NO_TRADE"
    structure = "RANGE"
    stop_loss = None
    take_profit = None

    # ==========================================
    # BUY CONDITIONS
    # ==========================================
    if (
        htf_up and                  # Higher timeframe bullish
        m30_up and                  # M30 bullish
        higher_highs and            # HH structure
        not in_consolidation and    # Not sideways
        not high_volatility and     # No news spike
        latest['close'] <= support * 1.01  # Near support pullback
    ):

        structure = "UPTREND"
        signal = "BUY"

        # Stop loss below support
        stop_loss = support

        # Risk size
        risk = latest['close'] - stop_loss

        # 1:2 reward
        take_profit = latest['close'] + (risk * 2)

    # ==========================================
    # SELL CONDITIONS
    # ==========================================
    elif (
        htf_down and                # Higher timeframe bearish
        m30_down and                # M30 bearish
        lower_lows and              # LL structure
        not in_consolidation and
        not high_volatility and
        latest['close'] >= resistance * 0.99  # Near resistance
    ):

        structure = "DOWNTREND"
        signal = "SELL"

        # Stop loss above resistance
        stop_loss = resistance

        risk = stop_loss - latest['close']

        take_profit = latest['close'] - (risk * 2)

    # ==========================================
    # RETURN RESULT
    # ==========================================
    return {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "structure": structure,
        "signal": signal,
        "entry": round(latest['close'], 5),
        "ema50": round(latest['ema50'], 5),
        "ema200": round(latest['ema200'], 5),
        "support": round(support, 5),
        "resistance": round(resistance, 5),
        "stop_loss": round(stop_loss, 5) if stop_loss else None,
        "take_profit": round(take_profit, 5) if take_profit else None,
        "consolidation": in_consolidation,
        "high_volatility": high_volatility
    }


@app.get("/")
def home():
    return {"message": "Professional M30 Trend Strategy API running"}
