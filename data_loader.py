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

        # 4시간봉 리샘플링
        ohlc_dict = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }
        self.df = self.df.resample('4h').agg(ohlc_dict)
        self.df.dropna(inplace=True)
        return self.df

    def add_indicators(self):
        # 1. EMA 200 (추세 필터)
        self.df['EMA_200'] = self.df['Close'].ewm(span=200, adjust=False).mean()

        # [수정] 돈키안 채널 기간 단축
        # 기존 120 (20일) -> 20 (약 3.3일)
        # 이제 3일간의 고점을 뚫으면 바로 진입합니다. 더 민첩하게 반응합니다.
        window = 20
        self.df['Donchian_High'] = self.df['High'].rolling(window=window).max().shift(1)
        self.df['Donchian_Low'] = self.df['Low'].rolling(window=window).min().shift(1)

        # 3. ATR (변동성 계산)
        # 반응 속도를 높이기 위해 ATR 기간도 살짝 줄입니다 (20 -> 14)
        high_low = self.df['High'] - self.df['Low']
        high_close = np.abs(self.df['High'] - self.df['Close'].shift())
        low_close = np.abs(self.df['Low'] - self.df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        self.df['ATR'] = true_range.ewm(alpha=1 / 14, min_periods=14).mean()

        self.df.dropna(inplace=True)
        return self.df