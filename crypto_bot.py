import asyncio
import ccxt.async_support as ccxt   # 비동기 모듈 사용
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# 1. 환경 변수 로드
load_dotenv()

class CryptoBot:
    def __init__(self):
        # 거래소 객체 초기화 (비동기 방식)
        self.exchanges = {
            "binance": ccxt.binance({
                "apiKey": os.environ.get("BINANCE_API_KEY", ""),
                "secret": os.environ.get("BINANCE_SECRET_KEY", ""),
                "enableRateLimit": True,  # API 차단 방지
                "options": {"defaultType": "future"}  # 선물 거래 설정
            }),
            "bingx": ccxt.bingx({
                "apiKey": os.environ.get("BINGX_API_KEY", ""),
                "secret": os.environ.get("BINGX_SECRET_KEY", ""),
                "enableRateLimit": True,
                "options": {"defaultType": "future"}
            })
        }
        self.symbol = "BTC/USDT"
        self.timeframe = '1m'   # 스캘핑용 1분봉

    async def fetch_data(self, exchange_name):
        """가격 데이터 및 캔들 데이터를 가져옴."""
        exchange = self.exchanges[exchange_name]
        try:
            # 현재가 조회 (Ticker)
            ticker = await exchange.fetch_ticker(self.symbol)
            current_price = ticker['last']

            # 과거 캔들 조회 (OHLCV) -EMA 계산용 (최근 30개만)
            ohlcv = await exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=30)

            return current_price, ohlcv
        except Exception as e:
            print(f"[{exchange_name}] Error: {e}")
            return None, None

    def calculate_ema(self, ohlcv, span=20):
        """Pandas를 이용해 EMA(지수이동평균)를 계산함."""
        if not ohlcv:
            return None

        # CCXT 데이터를 DataFrame으로 변환
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # EMA 계산 (close 가격 기준)
        df['ema'] = df['close'].ewm(span=span, adjust=False).mean()

        # 가장 최근의 EMA 값 변환
        return df['ema'].iloc[-1]

    async def run_cycle(self):
        """메인 실행 루프"""
        print(f"--- 봇 시작: {self.symbol} 감시 중 ---")

        try:
            while True:
                tasks = [self.process_exchange(name) for name in self.exchanges]
                await asyncio.gather(*tasks)

                print("-" * 50)
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\n봇을 종료함.")
        finally:
            # 거래소 연결 종료 (필수)
            for exchange in self.exchanges.values():
                await exchange.close()

    async def process_exchange(self, exchange_name):
        """개별 거래소 로직 처리"""
        price, ohlcv = await self.fetch_data(exchange_name)

        if price and ohlcv:
            ema = self.calculate_ema(ohlcv, span=20)    # 20EMA

            # 추세 판단 로직 (간단 예시)
            trend = "상승 🚀" if price > ema else "하락 📉"

            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] {exchange_name.upper():<7} | 현재가: {price: .2f} | EMA(20): {ema:.2f} | 추세: {trend}")
