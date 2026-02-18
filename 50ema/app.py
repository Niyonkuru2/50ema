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

    # ✅ Convert all OHLC to float to fix comparison errors
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
