"""
- 진입/청산 로직을 정의한다.
- 고레버리지 스캘핑이므로 짧은 호흡의 로직이 필요하다.
"""
class ScalpingStrategy:
    def __init__(self, leverage = 1):
        # [중요] 레버리지 1배로 시작하세요.
        # 이 전략은 승률로 먹는 게 아니라 '손익비'로 먹습니다.
        # 수익이 나면 그때 레버리지를 올리세요.
        self.leverage = leverage
        self.k = 0.5  # 돌파 계수

    def get_signal(self, row):
        """
        특정 시점(row)의 데이터를 받아 매매 신호를 반환
        :param row:
        :return: 'LONG', "SHORT' or None
        """
        current_price = row['Close']
        open_price = row['Open']

        # 목표 매수가 = 시가 + (이전 변동폭 * 0.5)
        # 즉, 오늘 힘이 좋아서 이 가격을 뚫고 올라가면 '상승세'로 간주
        target_price = open_price + (row['Range'] * self.k)

        ma_50 = row['MA_50']

        # [롱 진입 조건]
        # 1. 현재가가 목표가를 돌파했는가?
        # 2. 이동평균선 위에 있는가? (상승장 필터)
        # 3. 양봉인가?
        if current_price > target_price and current_price > ma_50 and current_price > open_price:
            return 'LONG'

        return None