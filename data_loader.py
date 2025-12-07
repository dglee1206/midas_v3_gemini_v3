"""데이터를 불러오고 보조지표를 생성한다."""

import pandas as pd

class DataLoader:
    """캔들 데이터를 로드하고 전처리하는 클래스"""
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def load_data(self):
        # CSV 파일 로드 (컬럼명은 상황에 맞게 조정 필요: timestamp, open, high, low, close, volume)
        self.df = pd.read_csv(self.file_path)

        # # self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        # self.df['OpenTime'] = pd.to_datetime(self.df['OpenTime'])
        # # set_index() Pandas DataFrame에서 특정 열을 인덱스로 설정하는데 사용된다.
        # # 이 함수를 사용하면 DataFrame의 기존 인덱스가 지정한 열로 대체된다.
        # # inplace: DataFrame을 직접 수정할지 여부를 나타내는 불리언 값. True로 설정하면 DataFrame이 직접 수정된다.
        # self.df.set_index('OpenTime', inplace=True)
        # return self.df

        # try:
        #     self.df['Close'] = self.df['Close'].astype(float)
        # except KeyError:
        #     print("🚨 오류: CSV 파일에 'Close' 컬럼이 없습니다. 'close'인지 확인해보세요.")
        #     return None
        #
        # self.df['OpenTime'] = pd.to_datetime(self.df['OpenTime'])
        # self.df.set_index('OpenTime', inplace=True)
        #
        # # [수정] **매우 중요**: 데이터를 과거->현재 순으로 정렬
        # self.df.sort_index(ascending=True, inplace=True)
        #
        # return self.df

        # [핵심 수정] Close 컬럼을 강제로 숫자(float)로 변환 (에러 발생 시 NaN 처리)
        self.df['Close'] = pd.to_numeric(self.df['Close'], errors='coerce')

        self.df['OpenTime'] = pd.to_datetime(self.df['OpenTime'])
        self.df.set_index('OpenTime', inplace=True)
        self.df.sort_index(ascending=True, inplace=True)
        return self.df

    def add_indicators(self):
        """스캘핑에 필요한 보조지표 추가"""
        # # # [수정] 데이터가 충분한지 확인
        # # if len(self.df) < 50:
        # #     print("🚨 데이터가 너무 적어서 EMA 50을 계산할 수 없습니다.")
        # #     return self.df
        # #
        # # # 예시: EMA (지수이동평균) 및 RSI
        # # self.df['EMA_10'] = self.df['Close'].ewm(span=10, adjust=False).mean()
        # # self.df['EMA_50'] = self.df['Close'].ewm(span=50, adjust=False).mean()
        #
        # # 데이터가 비었는지 확인
        # if self.df is None or len(self.df) < 50:
        #     print("데이터가 부족합니다.")
        #     return self.df
        #
        # self.df['EMA_10'] = self.df['Close'].ewm(span=10, adjust=False).mean()
        # self.df['EMA_50'] = self.df['Close'].ewm(span=50, adjust=False).mean()
        #
        # # [추가] 지표가 잘 만들어졌는지 NaN 제거 전 확인
        # # print(self.df[['Close', 'EMA_10', 'EMA_50']].head(60))
        #
        # # RSI 계산 등 추가 가능
        # return self.df

        # 데이터가 너무 적으면 계산 불가
        if len(self.df) < 50:
            return self.df

        # 1. EMA (지수이동평균) 계산
        self.df['EMA_10'] = self.df['Close'].ewm(span=10, adjust=False).mean()
        self.df['EMA_50'] = self.df['Close'].ewm(span=50, adjust=False).mean()

        # 2. RSI (상대강도지수, 14일 기준) 계산 코드 추가
        delta = self.df['Close'].diff()

        # 상승분(up)과 하락분(down) 분리
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)

        # Wilder's Smoothing 방식을 적용한 이동평균 (RSI 표준 공식)
        # com=13은 alpha=1/14와 같음 (14일 기간)
        ma_up = up.ewm(com=13, adjust=False).mean()
        ma_down = down.ewm(com=13, adjust=False).mean()

        rs = ma_up / ma_down
        self.df['RSI'] = 100 - (100 / (1 + rs))

        # [디버깅] RSI가 잘 생성되었는지 확인하려면 아래 주석 해제
        # print(self.df[['Close', 'RSI']].tail())

        return self.df