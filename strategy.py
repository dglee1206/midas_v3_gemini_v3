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

        # # [전략 예시] 골든크로스 스캘핑
        # # EMA 10이 EMA 50을 상향 돌파하면 롱
        # if row['EMA_10'] > row['EMA_50'] and row['prev_EMA_10'] <= row['prev_EMA_50']:
        #     return 'LONG'
        # # 데드크로스 숏
        # elif row['EMA_10'] < row['EMA_50'] and row['prev_EMA_10'] >= row['prev_EMA_50']:
        #     return "SHORT"
        #
        # return None

        # 1. 데이터가 정상인지 확인 (디버깅용)
        # EMA 값이 서로 같은지, 혹은 NaN인지 체크
        ema_10 = row['EMA_10']
        ema_50 = row['EMA_50']
        prev_ema_10 = row['prev_EMA_10']
        prev_ema_50 = row['prev_EMA_50']

        # [테스트] 봇이 작동하는지 확인하기 위해,
        # 100번째 캔들에서 무조건 매수 신호를 보내봅니다. (작동 여부 확인용)
        # 나중에 실제 돌릴 땐 이 2줄을 지우세요.
        # if row.name.minute == 0 and row.name.hour == 0:  # 매일 0시 0분에 강제 매수 시도 (테스트)
        #     return 'LONG'

        # 2. 골든크로스 (매수) 조건 상세 체크
        # 조건: 10이 50보다 크고 + 이전에는 10이 50보다 작거나 같았어야 함
        is_golden_cross = (ema_10 > ema_50) and (prev_ema_10 <= prev_ema_50)

        # 3. 데드크로스 (매도) 조건 상세 체크
        is_dead_cross = (ema_10 < ema_50) and (prev_ema_10 >= prev_ema_50)

        # [디버깅 로그] 교차하려는 움직임이 보이면 출력 (값이 너무 비슷하면 출력)
        diff = abs(ema_10 - ema_50)
        if diff > 0 and diff < 1.0:  # 차이가 1달러 미만일 때만 출력 (너무 자주 출력 방지)
            print(f"[{row.name}] 🔍 접전 중.. E10:{ema_10:.2f} / E50:{ema_50:.2f} (차이: {diff:.4f})")

        if is_golden_cross:
            print(f"🔥 [매수 신호 발견] {row.name} | E10이 E50을 돌파! ({prev_ema_10:.2f} -> {ema_10:.2f})")
            return 'LONG'

        elif is_dead_cross:
            print(f"💧 [매도 신호 발견] {row.name} | E10이 E50 하향 돌파! ({prev_ema_10:.2f} -> {ema_10:.2f})")
            return 'SHORT'

        return None