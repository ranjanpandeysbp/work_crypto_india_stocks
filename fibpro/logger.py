import pandas as pd
import os

FILE = "trades.csv"

def log_trade(data):
    df = pd.DataFrame([data])

    if not os.path.exists(FILE):
        df.to_csv(FILE, index=False)
    else:
        df.to_csv(FILE, mode='a', header=False, index=False)

def load_trades():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    return pd.DataFrame()