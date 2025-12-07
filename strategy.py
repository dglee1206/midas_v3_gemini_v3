"""
- 진입/청산 로직을 정의한다.
- 고레버리지 스캘핑이므로 짧은 호흡의 로직이 필요하다.
"""
class ScalpingStrategy:
    def __init__(self, leverage = 50):
        self.leverage = leverage

    def get_signal(self, row):
        """
        특정 시점(row)의 데이터를 받아 매매 신호를 반환
        :param row:
        :return: 'LONG', "SHORT' or None
        """

        ema_10, ema_50 = row['EMA_10'], row['EMA_50']
        prev_10, prev_50 = row['prev_EMA_10'], row['prev_EMA_50']
        rsi = row['RSI']
        adx = row['ADX']  # [추가]

        # 🔥 [핵심 필터] ADX가 25 미만이면 '노잼 횡보장' -> 절대 거래 금지
        if adx < 25:
            return None

        # 골든크로스 (매수)
        if (ema_10 > ema_50) and (prev_10 <= prev_50):
            # RSI가 50 이상이고, ADX가 살아있을 때만
            if rsi > 50:
                print(f"🚀 [강력 매수] RSI:{rsi:.1f} | ADX:{adx:.1f} (추세확실)")
                return 'LONG'

        # 데드크로스 (매도)
        elif (ema_10 < ema_50) and (prev_10 >= prev_50):
            # RSI가 50 이하이고, ADX가 살아있을 때만
            if rsi < 50:
                print(f"📉 [강력 매도] RSI:{rsi:.1f} | ADX:{adx:.1f} (하락확실)")
                return 'SHORT'

        return None