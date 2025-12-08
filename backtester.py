"""고레버리지에서는 수수료를 포함한 BEP(Break-Event Price, 손익분기점) 계산이 필수"""

import pandas as pd

class Backtester:
    def __init__(self, dataframe, strategy, initial_balance=1000, maker_fee=0.0002, taker_fee=0.0005):
        # self.df = dataframe
        self.df = dataframe.copy()  # 원본 보존을 위해 copy 사용
        self.strategy = strategy
        self.balance = initial_balance
        self.maker_fee = maker_fee  # 빙엑스 지정가 기준 (예시)
        self.taker_fee = taker_fee  # 빙엑스 시장가 기준 (예시)
        self.trades = []

    def calculate_break_even_price(self, entry_price, side):
        """
        수수료를 폼하여 본절(손해 0)이 되는 가격을 계산
        고레버리지일수록 수수료 비중이 크다.
        :param entry_price:
        :param side:
        :return:
        """
        # 진입 수수료 + 청산 수수료(예상)를 커버해야 함
        total_fee_rate = self.taker_fee + self.taker_fee    # 보수적으로 둘 다 시장가 지정

        if side == "LONG":
            # 롱은 가격이 올라야 수수료 멘징
            return entry_price * (1 + total_fee_rate)
        else:
            # 숏은 가격이 내려야 수수료 멘징
            return entry_price * (1 - total_fee_rate)

    def run(self):
        position = None
        entry_price = 0
        entry_time = None

        print(f"백테스팅 시작 (4시간봉 변동성 돌파): {len(self.df)}개 캔들")

        for index, row in self.df.iterrows():
            current_price = row['Close']

            # -----------------------------------
            # 1. 포지션이 없을 때 (진입 시도)
            # -----------------------------------
            if position is None:
                signal = self.strategy.get_signal(row)

                if signal == 'LONG':
                    # 자금 관리: 변동성 돌파는 승률이 40~50% 정도입니다.
                    # 대신 터질 때 크게 먹습니다. 시드의 5% 정도만 진입하거나
                    # 레버리지 1배라면 100% 진입해도 안전합니다.
                    bet_ratio = 1.0

                    position = 'LONG'

                    # 진입가는 '현재가'가 아니라 우리가 정한 '목표가'여야 정확하지만
                    # 백테스팅 편의상 종가(Close)로 진입했다고 가정하거나
                    # 보수적으로 High와 Close의 중간값 등을 쓸 수 있습니다.
                    # 여기선 Close로 진입합니다.
                    entry_price = current_price
                    entry_time = index

            # -----------------------------------
            # 2. 포지션 보유 중 (무조건 청산)
            # -----------------------------------
            else:
                # 4시간이 지났으므로 무조건 청산 (Time Cut)
                # 오버나잇 리스크 제거 + 다음 기회 탐색
                self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'Time_Cut')
                position = None

    def _execute_trade(self, entry_time, exit_time, side, entry_price, exit_price, result_type):
        leverage = self.strategy.leverage

        # [수정] 전체 잔고(balance)를 다 쓰는 게 아니라,
        # 잔고의 20%만 증거금(Margin)으로 사용 (Risk Management)
        bet_amount = self.balance * 0.2

        # 수익률 계산
        if side == 'LONG':
            raw_pnl_rate = (exit_price - entry_price) / entry_price
        else:
            raw_pnl_rate = (entry_price - exit_price) / entry_price

        # 레버리지 적용 수익률
        leveraged_pnl_rate = raw_pnl_rate * leverage

        # 수수료 계산 (베팅 금액 기준)
        # 진입(Maker) + 청산(Taker) 가정
        fee_rate = (self.maker_fee + self.taker_fee) * leverage

        # 최종 수익금 (PnL) = 베팅금액 * (수익률 - 수수료)
        pnl_amount = bet_amount * (leveraged_pnl_rate - fee_rate)

        # 잔고 업데이트
        self.balance += pnl_amount

        # 파산 방지 (잔고가 마이너스면 0 처리)
        if self.balance < 0:
            self.balance = 0

        self.trades.append({
            'entry_time': entry_time,
            'exit_time': exit_time,
            'side': side,
            'pnl_rate': (leveraged_pnl_rate - fee_rate) * 100,
            'realized_pnl': pnl_amount,
            'balance': self.balance
        })

    def print_result(self):
        print(f"최종 잔고: {self.balance:.2f}")
        print(f"총 거래 횟수: {len(self.trades)}")
        # 승률 계산 등 추가 가능