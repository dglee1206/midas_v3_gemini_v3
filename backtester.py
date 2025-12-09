"""고레버리지에서는 수수료를 포함한 BEP(Break-Event Price, 손익분기점) 계산이 필수"""

import pandas as pd

class Backtester:
    def __init__(self, dataframe, strategy, initial_balance=1000, maker_fee=0.0002, taker_fee=0.0005):
        # self.df = dataframe
        self.df = dataframe.copy()
        self.strategy = strategy
        self.balance = initial_balance
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
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
        avg_entry_price = 0
        qty = 0
        pyramid_count = 0
        last_add_price = 0
        sl_price = 0

        # 이전 캔들의 정보를 저장할 변수
        prev_signal = None
        prev_row = None

        print(f"백테스팅 시작 (수정된 로직): {len(self.df)}개 캔들")

        for index, row in self.df.iterrows():
            # -----------------------------------------------------
            # [수정 1] 현실적인 진입 가격: '현재 캔들의 시가(Open)'
            # -----------------------------------------------------
            current_open = row['Open']
            current_low = row['Low']
            current_high = row['High']
            current_close = row['Close']
            atr = row['ATR']

            # 1. 포지션 관리 (청산 및 불타기 확인)
            if position is not None:
                exit_signal = False
                exit_price = 0

                # [수정 2] 고가/저가(High/Low)로 손절 체크 (Wick Check)
                if position == 'LONG':
                    # 트레일링 스탑 업데이트 (종가 기준 업데이트는 유지하되, 체크는 Low로)
                    new_sl = current_close - (atr * 3.0)
                    if new_sl > sl_price: sl_price = new_sl

                    # 장중 저가가 손절가를 건드렸는가?
                    if current_low <= sl_price:
                        exit_signal = True
                        exit_price = sl_price  # 손절가에 체결 가정 (슬리피지 고려시 더 낮게 잡아야 함)

                elif position == 'SHORT':
                    new_sl = current_close + (atr * 3.0)
                    if new_sl < sl_price: sl_price = new_sl

                    # 장중 고가가 손절가를 건드렸는가?
                    if current_high >= sl_price:
                        exit_signal = True
                        exit_price = sl_price

                # 청산 실행
                if exit_signal:
                    if position == 'LONG':
                        pnl = (exit_price - avg_entry_price) * qty
                    else:
                        pnl = (avg_entry_price - exit_price) * qty

                    # 수수료: 진입(Maker가정) + 청산(Stop은 Taker)
                    # 보수적으로 둘 다 Taker로 계산 권장
                    fee = (avg_entry_price * qty * self.taker_fee) + (exit_price * qty * self.taker_fee)

                    self.balance += (pnl - fee)
                    self.trades.append({'time': index, 'balance': self.balance, 'type': 'Exit'})

                    position = None
                    qty = 0
                    pyramid_count = 0
                    prev_signal = None  # 포지션 종료 시 이전 신호 초기화
                    continue  # 청산했으면 이번 턴 종료

                # [피라미딩 로직] - 여유가 된다면 구현 (단, 종가 기준으로 다음 봉 시가 진입 추천)
                # 여기서는 복잡도를 낮추기 위해 생략하거나,
                # "현재 종가가 조건 만족 시 -> 다음 봉 시가에 추가 진입" 로직으로 바꿔야 함.

            # 2. 신규 진입 (이전 봉에서 신호가 떴다면 이번 봉 시가에 진입)
            if position is None and prev_signal is not None:
                # 자금 관리: 잔고의 2% 리스크
                # 진입가는 현재 봉의 'Open'
                entry_price = current_open
                stop_loss_dist = prev_row['ATR'] * 3.0  # ATR은 신호 뜬 시점 기준

                if stop_loss_dist > 0:
                    risk_amount = self.balance * 0.02
                    qty = risk_amount / stop_loss_dist

                    # 레버리지 3배 제한
                    if (qty * entry_price) > (self.balance * 3):
                        qty = (self.balance * 3) / entry_price

                    position = prev_signal
                    avg_entry_price = entry_price
                    last_add_price = entry_price

                    if position == 'LONG':
                        sl_price = entry_price - stop_loss_dist
                    else:
                        sl_price = entry_price + stop_loss_dist

            # 3. 신호 계산 (다음 봉을 위해 저장)
            # [중요] 신호는 이번 봉의 마감 데이터(Close)로 계산하고, 실제 진입은 다음 루프(Next Open)에서 수행
            signal = self.strategy.get_signal(row)
            prev_signal = signal
            prev_row = row

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