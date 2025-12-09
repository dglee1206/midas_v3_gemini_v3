"""
- 진입/청산 로직을 정의한다.
- 고레버리지 스캘핑이므로 짧은 호흡의 로직이 필요하다.
"""
class ScalpingStrategy:
    def __init__(self, leverage=3):
        self.leverage = leverage

    def get_signal(self, row):
        current_price = row['Close']
        ema_200 = row['EMA_200']
        donchian_high = row['Donchian_High']
        donchian_low = row['Donchian_Low']
        adx = row['ADX']

        # [수정] ADX 필터 완화: 25 -> 20 (너무 깐깐해서 수익 기회 놓침 방지)
        if adx < 20:
            return None

        if current_price > donchian_high and current_price > ema_200:
            return 'LONG'
        elif current_price < donchian_low and current_price < ema_200:
            return 'SHORT'

        return None