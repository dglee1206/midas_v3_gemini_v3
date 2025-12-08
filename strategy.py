"""
- 진입/청산 로직을 정의한다.
- 고레버리지 스캘핑이므로 짧은 호흡의 로직이 필요하다.
"""
class ScalpingStrategy:
    def __init__(self, leverage = 1):
        self.leverage = leverage

    def get_signal(self, row):
        current_price = row['Close']
        ema_200 = row['EMA_200']
        donchian_high = row['Donchian_High']
        donchian_low = row['Donchian_Low']

        # [롱 진입] 신고가 돌파 + 상승 추세
        if current_price > donchian_high and current_price > ema_200:
            return 'LONG'

        # [숏 진입] 신저가 이탈 + 하락 추세
        elif current_price < donchian_low and current_price < ema_200:
            return 'SHORT'

        return None