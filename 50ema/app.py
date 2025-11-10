from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from ta.trend import SMAIndicator

app = FastAPI(title="Market Signal API")

class MarketData(BaseModel):
    values: list  # Expected: list of dicts with at least 'close'
    symbol: str
    timeframe: str

@app.post("/analyze")
def analyze(data: MarketData):
    # Convert input data into DataFrame
    df = pd.DataFrame(data.values)
    
    if 'close' not in df.columns:
        return {"error": "Missing 'close' column in input data"}

    df['close'] = df['close'].astype(float)

    # Ensure data is chronological (oldest first)
    df = df.iloc[::-1].reset_index(drop=True)

    # Compute 50-period SMA
    df['sma50'] = SMAIndicator(df['close'], window=50).sma_indicator()

    # Define trend direction
    df['uptrend'] = df['close'] > df['sma50']
    df['downtrend'] = df['close'] < df['sma50']

    # Get last 3 data points for better detection stability
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    before_prev = df.iloc[-3]

    # --- Improved Trading Logic ---
    # Detect SELL: price was in uptrend but just crossed below SMA
    if before_prev['uptrend'] and prev['uptrend'] and latest['downtrend']:
        signal = "BUY"

    # Detect BUY: price was in downtrend but just crossed above SMA
    elif before_prev['downtrend'] and prev['downtrend'] and latest['uptrend']:
        signal = "SELL"

    else:
        signal = "NEUTRAL"

    # --- Result Output ---
    result = {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "signal": signal,
        "last_close": round(latest['close'], 4),
        "sma50": round(latest['sma50'], 4),
        "timestamp_index": int(df.index[-1])
    }

    return result
@app.get("/")
def home():
    return {"message": "Market Signal API v2 is running successfully"}
