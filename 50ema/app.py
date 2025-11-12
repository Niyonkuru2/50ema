from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from ta.trend import EMAIndicator

app = FastAPI(title="Market Signal API")

class MarketData(BaseModel):
    values: list  # expects list of dicts with at least 'close'
    symbol: str
    timeframe: str

@app.post("/analyze")
def analyze(data: MarketData):
    # Convert input to DataFrame
    raw_data = data.values
    df = pd.DataFrame(raw_data)
    
    # Ensure correct type and order
    df['close'] = df['close'].astype(float)
    df = df.iloc[::-1].reset_index(drop=True)  # oldest first, newest last

    # Calculate 50 EMA
    df['ema50'] = EMAIndicator(df['close'], window=50).ema_indicator()

    # Get last close and EMA
    latest = df.iloc[-1]
    last_close = latest['close']
    ema50 = latest['ema50']

    # Determine position
    if last_close > ema50:
        signal = "ABOVE_EMA"
    elif last_close < ema50:
        signal = "BELOW_EMA"
    else:
        signal = "ON_EMA"

    # Optional: detect a crossover (for BUY/SELL)
    prev = df.iloc[-2]
    if prev['close'] <= prev['ema50'] and last_close > ema50:
        crossover = "BUY"
    elif prev['close'] >= prev['ema50'] and last_close < ema50:
        crossover = "SELL"
    else:
        crossover = "NONE"

    # Response
    result = {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "signal": signal, 
        "crossover": crossover,
        "last_close": last_close,
        "ema50": ema50,
        "timestamp": str(df.index[-1])
    }

    return result

@app.get("/")
def home():
    return {"message": "Market Signal API v2 is running successfully"}
