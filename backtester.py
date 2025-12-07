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
        # position = None # None, 'LONG', 'SHORT'
        # entry_price = 0
        # entry_time = None
        #
        # tp_price = 0
        # sl_price = 0
        #
        # # 전 봉이 데이터 접근을 위해 shift 활용
        # self.df['prev_EMA_10'] = self.df['EMA_10'].shift(1)
        # self.df['prev_EMA_50'] = self.df['EMA_50'].shift(1)
        #
        # # [중요] NaN 값(계산 불가 구간) 제거. 앞부분 50개 날리기
        # self.df.dropna(inplace=True)
        #
        # print(f"백테스팅 시작: 유효 데이터 {len(self.df)}개")
        #
        # # [디버깅] 첫 번째 데이터의 지표 값이 정상인지 출력
        # first_row = self.df.iloc[0]
        # print(f"첫 데이터 확인 | Close: {first_row['Close']} | EMA10: {first_row['EMA_10']:.2f} | EMA50: {first_row['EMA_50']:.2f}")
        #
        # for index, row in self.df.iterrows():
        #     current_price = row['Close']
        #
        #     if position is None:
        #         signal = self.strategy.get_signal(row)
        #
        #         if signal:
        #             # position = signal
        #             # entry_price = row['Close']
        #             # entry_time = index
        #             #
        #             # # [리스크 관리] 최소 익절 목표가 (수수료 포함 본절가)
        #             # be_price = self.calculate_break_even_price(entry_price, position)
        #             #
        #             # # 스캘핑 목표가 설정 (예: 본절가 대비 0.3% 수익 목표)
        #             # target_profit_rate = 0.003
        #             # stop_loss_rate = 0.002  # 0.2% 손절
        #             #
        #             # if position == 'LONG':
        #             #     tp_price = entry_price * (1 + target_profit_rate)
        #             #     sl_price = entry_price * (1 - 0.002) # 짧은 손절
        #             # else:
        #             #     tp_price = entry_price * (1 - target_profit_rate)
        #             #     sl_price = entry_price * (1 + 0.002)
        #
        #             # [디버깅] 신호가 잡히면 무조건 출력
        #             # print(f"🔥 신호 발생! {index} : {signal} (가격: {current_price})")
        #
        #             position = signal
        #             entry_price = current_price
        #             entry_time = index
        #             be_price = self.calculate_break_even_price(entry_price, position)
        #
        #             target_profit_rate = 0.003
        #             stop_loss_rate = 0.002
        #
        #             if position == 'LONG':
        #                 tp_price = max(entry_price * (1 + target_profit_rate), be_price * 1.001)
        #                 sl_price = entry_price * (1 - stop_loss_rate)
        #             else:
        #                 tp_price = min(entry_price * (1 - target_profit_rate), be_price * 0.999)
        #                 sl_price = entry_price * (1 + stop_loss_rate)
        #
        #         else:
        #             # # 포지션 보유 중 -> 청산 로직 (TP or SL)
        #             # current_price = row['Close']
        #             #
        #             # # 1. 롱 포지션 청산 체크
        #             # if position == 'LONG':
        #             #     if current_price >= tp_price: # 익절
        #             #         self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'WIN')
        #             #         position = None
        #             #     elif current_price <= sl_price: # 손절
        #             #         self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'LOSS')
        #             #         position = None
        #             #
        #             # # 2. 숏 포지션 청산 체크
        #             # elif position == 'SHORT':
        #             #     if current_price <= tp_price: # 익절
        #             #         self._execute_trade(entry_time, index, 'SHORT', entry_price, current_price, 'WIN')
        #             #         position = None
        #             #     elif current_price >= sl_price: # 손절
        #             #         self._execute_trade(entry_time, index, 'SHORT', entry_price, current_price, 'LOSS')
        #             #         position = None
        #
        #             # 포지션 보유 중
        #             if position == 'LONG':
        #                 if current_price >= tp_price:
        #                     self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'WIN')
        #                     position = None
        #                 elif current_price <= sl_price:
        #                     self._execute_trade(entry_time, index, 'LONG', entry_price, current_price, 'LOSS')
        #                     position = None
        #
        #             elif position == 'SHORT':
        #                 if current_price <= tp_price:
        #                     self._execute_trade(entry_time, index, 'SHORT', entry_price, current_price, 'WIN')
        #                     position = None
        #                 elif current_price >= sl_price:
        #                     self._execute_trade(entry_time, index, 'SHORT', entry_price, current_price, 'LOSS')
        #                     position = None

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

                    # 목표가/손절가 설정
                    target_profit_rate = 0.003  # 0.3%
                    stop_loss_rate = 0.002  # 0.2%

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
        # # 실제 수익금 계산 (레버리지 적용, 수수료 차감)
        # leverage = self.strategy.leverage
        #
        # # 수익률 (롱: 출-진 / 진, 숏: 진-출 / 진)
        # raw_pnl_rate = (exit_price - entry_price) / entry_price if side == 'LONG' else (
        #                                                                                            entry_price - exit_price) / entry_price
        #
        # # 레버리지 반영 수익률
        # leveraged_pnl_rate = raw_pnl_rate * leverage
        #
        # # 수수료 차감 (진입 + 청산, 레버리지 전체 금액에 대해 부과됨에 주의)
        # # 수수료는 (진입금액 * 레버리지 * 요율) + (청산금액 * 레버리지 * 요율)
        # # 약식 계산: 전체 포지션 규모에 대해 약 2배의 수수료 발생
        # total_fee = (self.taker_fee + self.taker_fee) * leverage
        #
        # final_pnl_rate = leveraged_pnl_rate - total_fee
        #
        # self.balance = self.balance * (1 + final_pnl_rate)
        # self.trades.append({
        #     'entry_time': entry_time,
        #     'exit_time': exit_time,
        #     'side': side,
        #     'pnl_rate': final_pnl_rate,
        #     'balance': self.balance
        # })

        leverage = self.strategy.leverage

        if side == 'LONG':
            raw_pnl_rate = (exit_price - entry_price) / entry_price
        else:
            raw_pnl_rate = (entry_price - exit_price) / entry_price

        leveraged_pnl_rate = raw_pnl_rate * leverage
        total_fee = (self.taker_fee * 2) * leverage
        final_pnl_rate = leveraged_pnl_rate - total_fee

        self.balance = self.balance * (1 + final_pnl_rate)

        self.trades.append({
            'entry_time': entry_time,
            'exit_time': exit_time,
            'side': side,
            'pnl_rate': final_pnl_rate,
            'balance': self.balance
        })

    def print_result(self):
        print(f"최종 잔고: {self.balance:.2f}")
        print(f"총 거래 횟수: {len(self.trades)}")
        # 승률 계산 등 추가 가능