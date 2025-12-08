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

        # [핵심] 4시간봉(4H)으로 리샘플링
        # 1시간봉 7만 개 -> 4시간봉 약 1.7만 개로 압축
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
        # 변동성 돌파 전략을 위한 'Range(변동폭)' 계산
        # Range = 전 봉의 고가 - 전 봉의 저가
        self.df['Prev_High'] = self.df['High'].shift(1)
        self.df['Prev_Low'] = self.df['Low'].shift(1)
        self.df['Prev_Close'] = self.df['Close'].shift(1)
        self.df['Range'] = self.df['Prev_High'] - self.df['Prev_Low']

        # 노이즈 필터용 이동평균선 (추세장일 때만 진입)
        self.df['MA_50'] = self.df['Close'].rolling(window=50).mean()

        self.df.dropna(inplace=True)
        return self.df