from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from ta.trend import EMAIndicator

app = FastAPI(title="Professional EMA Crossover API")

class MarketData(BaseModel):
    values: list  # list of dicts with at least 'close'
    symbol: str
    timeframe: str


@app.post("/analyze")
def analyze(data: MarketData):
    raw_data = data.values
    df = pd.DataFrame(raw_data)

    # --- VALIDATION ---
    if 'close' not in df.columns:
        return {"error": "Missing 'close' field in input data"}
    if len(df) < 51:
        return {"error": "Not enough data for 50 EMA calculation"}

    # --- PREP DATA ---
    df['close'] = df['close'].astype(float)
    df = df.iloc[::-1].reset_index(drop=True)  # oldest → newest

    # --- CALCULATE EMA50 ---
    df['ema50'] = EMAIndicator(df['close'], window=50).ema_indicator()

    # --- DEFINE LAST TWO CANDLES ---
    prev = df.iloc[-2]
    latest = df.iloc[-1]

    prev_close, prev_ema = prev['close'], prev['ema50']
    last_close, last_ema = latest['close'], latest['ema50']

    # --- CROSSOVER DETECTION ---
    signal = None
    direction = None
    crossover = None

    # BUY signal → crosses ABOVE EMA after being below
    if prev_close < prev_ema and last_close > last_ema:
        crossover = "BUY"
        direction = "UP"
        signal = "PRICE_CROSSED_ABOVE_EMA"

    # SELL signal → crosses BELOW EMA after being above
    elif prev_close > prev_ema and last_close < last_ema:
        crossover = "SELL"
        direction = "DOWN"
        signal = "PRICE_CROSSED_BELOW_EMA"

    # No crossover, just relative position
    else:
        if last_close > last_ema:
            direction = "UPTREND"
            signal = "PRICE_ABOVE_EMA"
        elif last_close < last_ema:
            direction = "DOWNTREND"
            signal = "PRICE_BELOW_EMA"
        else:
            direction = "NEUTRAL"
            signal = "ON_EMA"

    # --- RESPONSE ---
    result = {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "signal": signal,
        "crossover": crossover if crossover else "NONE",
        "direction": direction,
        "last_close": round(last_close, 5),
        "ema50": round(last_ema, 5),
        "index": int(df.index[-1]),
    }

    return result


@app.get("/")
def home():
    return {"message": "EMA Crossover Detector v3 running successfully"}
