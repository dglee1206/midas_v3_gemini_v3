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

        # SL/TP 가격
        sl_price = 0

        # 진입 수량 (코인 개수)
        qty = 0

        self.df.dropna(inplace=True)
        print(f"백테스팅 시작 (돈키안 돌파 + 2% 룰): {len(self.df)}개 캔들")

        for index, row in self.df.iterrows():
            current_price = row['Close']
            atr = row['ATR']

            # ---------------------------
            # 1. 진입 (포지션 없을 때)
            # ---------------------------
            if position is None:
                signal = self.strategy.get_signal(row)

                if signal:
                    # [핵심] 자금 관리 로직
                    # 내 잔고의 2%만 리스크로 건다 (Risk per Trade = 2%)
                    risk_amount = self.balance * 0.02

                    # 손절폭은 ATR의 3배로 넉넉하게 잡음 (휩소 방지)
                    stop_loss_dist = atr * 3.0

                    if stop_loss_dist == 0: continue

                    # 내가 감당할 수 있는 수량 계산
                    # 수량 = 리스크 금액 / 코인당 손절폭
                    qty = risk_amount / stop_loss_dist

                    # 진입 금액 (Notional Value)
                    position_value = qty * current_price

                    # (옵션) 최대 레버리지 제한 (예: 3배까지만 허용)
                    if position_value > self.balance * 3:
                        qty = (self.balance * 3) / current_price

                    position = signal
                    entry_price = current_price
                    entry_time = index

                    # 손절가 설정
                    if position == 'LONG':
                        sl_price = entry_price - stop_loss_dist
                    else:
                        sl_price = entry_price + stop_loss_dist

            # ---------------------------
            # 2. 청산 (트레일링 스탑)
            # ---------------------------
            else:
                exit_signal = False
                exit_type = None

                # 트레일링 스탑: ATR 2배만큼 이익을 따라가며 손절 라인을 올림
                if position == 'LONG':
                    # 현재가 기준 ATR 3배 밑을 새로운 손절라인으로 계속 업데이트
                    new_sl = current_price - (atr * 3.0)
                    if new_sl > sl_price:
                        sl_price = new_sl

                    # 손절가 건드리면 청산 (익절일 수도 있고 손절일 수도 있음)
                    if current_price <= sl_price:
                        exit_signal = True;
                        exit_type = 'Exit'

                elif position == 'SHORT':
                    new_sl = current_price + (atr * 3.0)
                    if new_sl < sl_price:
                        sl_price = new_sl

                    if current_price >= sl_price:
                        exit_signal = True;
                        exit_type = 'Exit'

                if exit_signal:
                    # 수익 계산 로직 수정 (수량 기준)
                    # PnL = (출구가 - 입구가) * 수량
                    if position == 'LONG':
                        pnl_amount = (current_price - entry_price) * qty
                    else:
                        pnl_amount = (entry_price - current_price) * qty

                    # 수수료 차감 (진입/청산 0.1% 가정, 전체 포지션 크기 기준)
                    fee = (entry_price * qty + current_price * qty) * 0.001
                    final_pnl = pnl_amount - fee

                    self.balance += final_pnl

                    # 거래 기록
                    self.trades.append({
                        'time': index,
                        'pnl_amount': final_pnl,
                        'balance': self.balance
                    })

                    position = None
                    qty = 0

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