"""고레버리지에서는 수수료를 포함한 BEP(Break-Event Price, 손익분기점) 계산이 필수"""
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
        tp_price = 0
        sl_price = 0

        # 데이터 전처리
        self.df['prev_EMA_10'] = self.df['EMA_10'].shift(1)
        self.df['prev_EMA_50'] = self.df['EMA_50'].shift(1)
        self.df.dropna(inplace=True)

        print(f"백테스팅 시작: {len(self.df)}개 데이터")

        for index, row in self.df.iterrows():
            current_price = row['Close']

            # ---------------------------------------
            # 1. 포지션이 없을 때 (진입 탐색)
            # ---------------------------------------
            if position is None:
                signal = self.strategy.get_signal(row)

                if signal:
                    print(f"🔥 [진입] {index} | {signal} | 가격: {current_price}")
                    position = signal
                    entry_price = current_price
                    entry_time = index

                    be_price = self.calculate_break_even_price(entry_price, position)

                    # # 목표가/손절가 설정
                    # target_profit_rate = 0.003  # 0.3%
                    # stop_loss_rate = 0.002  # 0.2%

                    # [수정] 손익비 개선 (TP를 늘리고 SL을 유지)
                    target_profit_rate = 0.005  # 0.5% 익절 (50배 레버리지시 +25% 수익)
                    stop_loss_rate = 0.003  # 0.3% 손절 (50배 레버리지시 -15% 손실)

                    # (수수료 고려해도 익절 시 이득이 훨씬 큼)

                    if position == 'LONG':
                        tp_price = max(entry_price * (1 + target_profit_rate), be_price * 1.001)
                        sl_price = entry_price * (1 - stop_loss_rate)
                    else:
                        tp_price = min(entry_price * (1 - target_profit_rate), be_price * 0.999)
                        sl_price = entry_price * (1 + stop_loss_rate)

                    print(f"   👉 목표가(TP): {tp_price:.2f} | 손절가(SL): {sl_price:.2f}")

            # ---------------------------------------
            # 2. 포지션 보유 중일 때 (청산 탐색)
            # ---------------------------------------
            else:
                # [디버깅] 포지션 보유 중인 첫 3번만 로그 출력 (무한 출력 방지)
                # 만약 이 로그가 안 뜨면 들여쓰기 문제입니다.
                if index == self.df.index[self.df.index.get_loc(entry_time) + 1]:
                    print(f"   ⏳ 포지션 보유중... 현재가: {current_price} (TP까지: {abs(current_price - tp_price):.2f} 남음)")

                if position == 'LONG':
                    if current_price >= tp_price:
                        print(f"   💰 [익절] {index} | 가격: {current_price}")
                        self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'WIN')
                        position = None
                    elif current_price <= sl_price:
                        print(f"   zzz [손절] {index} | 가격: {current_price}")
                        self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'LOSS')
                        position = None

                elif position == 'SHORT':
                    if current_price <= tp_price:
                        print(f"   💰 [익절] {index} | 가격: {current_price}")
                        self._execute_trade(entry_time, index, 'SHORT', entry_price, current_price, 'WIN')
                        position = None
                    elif current_price >= sl_price:
                        print(f"   zzz [손절] {index} | 가격: {current_price}")
                        self._execute_trade(entry_time, index, 'SHORT', entry_price, current_price, 'LOSS')
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