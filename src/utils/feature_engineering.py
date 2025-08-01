import pandas as pd
import numpy as np
import talib

def add_technical_indicators(df):
    # Ensure required columns
    if 'close' not in df.columns:
        if 'Close' in df.columns:
            df.rename(columns={'Close': 'close'}, inplace=True)
        else:
            df['close'] = (df['bid'] + df['ask'])/2 if 'bid' in df else df['last']
    
    # Calculate indicators
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(20).std()
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    df['macd'], df['macd_signal'], _ = talib.MACD(df['close'])
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['sma20'] = talib.SMA(df['close'], timeperiod=20)
    df['sma50'] = talib.SMA(df['close'], timeperiod=50)
    
    if 'volume' in df.columns:
        df['obv'] = talib.OBV(df['close'], df['volume'])
    
    return df.dropna()