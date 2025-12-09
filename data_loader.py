"""데이터를 불러오고 보조지표를 생성한다."""

import pandas as pd
import numpy as np

class DataLoader:
    """캔들 데이터를 로드하고 전처리하는 클래스"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def load_data(self):
        self.df = pd.read_csv(self.file_path)
        self.df['Close'] = pd.to_numeric(self.df['Close'], errors='coerce')
        self.df['OpenTime'] = pd.to_datetime(self.df['OpenTime'])
        self.df.set_index('OpenTime', inplace=True)
        self.df.sort_index(ascending=True, inplace=True)

        ohlc_dict = {
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }
        self.df = self.df.resample('4h').agg(ohlc_dict)
        self.df.dropna(inplace=True)
        return self.df

    def add_indicators(self):
        # 1. EMA 200
        self.df['EMA_200'] = self.df['Close'].ewm(span=200, adjust=False).mean()

        # 2. Donchian Channel (20)
        window = 20
        self.df['Donchian_High'] = self.df['High'].rolling(window=window).max().shift(1)
        self.df['Donchian_Low'] = self.df['Low'].rolling(window=window).min().shift(1)

        # 3. ATR (14)
        high_low = self.df['High'] - self.df['Low']
        high_close = np.abs(self.df['High'] - self.df['Close'].shift())
        low_close = np.abs(self.df['Low'] - self.df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        self.df['ATR'] = true_range.ewm(alpha=1 / 14, min_periods=14).mean()

        # 4. ADX (14)
        delta_high = self.df['High'] - self.df['High'].shift(1)
        delta_low = self.df['Low'].shift(1) - self.df['Low']

        plus_dm = np.where((delta_high > delta_low) & (delta_high > 0), delta_high, 0.0)
        minus_dm = np.where((delta_low > delta_high) & (delta_low > 0), delta_low, 0.0)

        def wilders_smoothing(series, window):
            return series.ewm(alpha=1 / window, adjust=False).mean()

        tr_smooth = wilders_smoothing(true_range, 14)
        plus_di = 100 * (wilders_smoothing(pd.Series(plus_dm, index=self.df.index), 14) / tr_smooth)
        minus_di = 100 * (wilders_smoothing(pd.Series(minus_dm, index=self.df.index), 14) / tr_smooth)

        dx = 100 * np.abs((plus_di - minus_di) / (plus_di + minus_di))
        self.df['ADX'] = wilders_smoothing(pd.Series(dx, index=self.df.index), 14)

        self.df.dropna(inplace=True)
        return self.df