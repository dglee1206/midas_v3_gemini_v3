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
        avg_entry_price = 0  # 평단가
        qty = 0  # 총 보유 수량

        entry_time = None
        sl_price = 0

        # 피라미딩 관련 변수
        pyramid_count = 0  # 불타기 횟수 (0: 최초진입, 1: 1차추가...)
        last_add_price = 0  # 마지막으로 진입한 가격

        self.df.dropna(inplace=True)
        print(f"백테스팅 시작 (피라미딩 불타기 🔥): {len(self.df)}개 캔들")

        for index, row in self.df.iterrows():
            current_price = row['Close']
            atr = row['ATR']

            # ---------------------------
            # 1. 포지션 없을 때 (신규 진입)
            # ---------------------------
            if position is None:
                signal = self.strategy.get_signal(row)

                if signal:
                    # 최초 진입: 시드의 2% 리스크 (ATR 3배 손절 기준)
                    risk_amount = self.balance * 0.02
                    stop_loss_dist = atr * 3.0

                    if stop_loss_dist == 0: continue

                    # 수량 계산
                    qty = risk_amount / stop_loss_dist

                    # (안전장치) 레버리지 3배 초과 금지
                    if (qty * current_price) > (self.balance * 3):
                        qty = (self.balance * 3) / current_price

                    position = signal
                    avg_entry_price = current_price
                    last_add_price = current_price
                    entry_time = index
                    pyramid_count = 0  # 카운트 초기화

                    # 손절가 설정
                    if position == 'LONG':
                        sl_price = avg_entry_price - stop_loss_dist
                    else:
                        sl_price = avg_entry_price + stop_loss_dist

            # ---------------------------
            # 2. 포지션 보유 중 (관리: 불타기 & 청산)
            # ---------------------------
            else:
                exit_signal = False
                exit_type = None

                # --- [피라미딩 로직: 불타기] ---
                # 조건: 현재가가 마지막 진입가보다 1 ATR 이상 유리해졌고, 3번 미만으로 불타기 했으면 추가 진입
                if pyramid_count < 3:
                    should_add = False
                    if position == 'LONG' and current_price > last_add_price + (atr * 1.0):
                        should_add = True
                    elif position == 'SHORT' and current_price < last_add_price - (atr * 1.0):
                        should_add = True

                    if should_add:
                        # 추가 진입은 최초 진입 수량의 50%만 (피라미드 구조)
                        add_qty = qty * 0.5

                        # 평단가 갱신
                        new_total_qty = qty + add_qty
                        avg_entry_price = ((avg_entry_price * qty) + (current_price * add_qty)) / new_total_qty
                        qty = new_total_qty

                        last_add_price = current_price
                        pyramid_count += 1

                        # [중요] 손절 라인 끌어올리기 (Trailing)
                        # 불타기를 했으니 이미 수익권임. 손절 라인을 평단가 근처로 올려서 리스크 제거
                        if position == 'LONG':
                            sl_price = avg_entry_price - (atr * 1.5)  # 손절폭을 3.0 -> 1.5로 좁힘
                        else:
                            sl_price = avg_entry_price + (atr * 1.5)

                        # print(f"🔥 [불타기 {pyramid_count}차] {index} | 평단가: {avg_entry_price:.2f}")

                # --- [청산 로직: 트레일링 스탑] ---
                if position == 'LONG':
                    # 트레일링 스탑: ATR 3배 거리 유지
                    new_sl = current_price - (atr * 3.0)
                    if new_sl > sl_price: sl_price = new_sl

                    if current_price <= sl_price:
                        exit_signal = True;
                        exit_type = 'Exit'

                elif position == 'SHORT':
                    new_sl = current_price + (atr * 3.0)
                    if new_sl < sl_price: sl_price = new_sl

                    if current_price >= sl_price:
                        exit_signal = True;
                        exit_type = 'Exit'

                if exit_signal:
                    # 수익 계산
                    if position == 'LONG':
                        pnl_amount = (current_price - avg_entry_price) * qty
                    else:
                        pnl_amount = (avg_entry_price - current_price) * qty

                    # 수수료 차감 (진입/청산 0.1% 가정)
                    notional_value = avg_entry_price * qty
                    fee = (notional_value + (current_price * qty)) * 0.001
                    final_pnl = pnl_amount - fee

                    self.balance += final_pnl

                    self.trades.append({
                        'time': index,
                        'pnl_amount': final_pnl,
                        'balance': self.balance,
                        'pyramids': pyramid_count  # 몇 번 불탔는지 기록
                    })

                    position = None
                    qty = 0
                    pyramid_count = 0

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