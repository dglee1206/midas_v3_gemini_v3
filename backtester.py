"""고레버리지에서는 수수료를 포함한 BEP(Break-Event Price, 손익분기점) 계산이 필수"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, dataframe, strategy, initial_balance=1000, maker_fee=0.0002, taker_fee=0.0005):
        self.df = dataframe.copy()
        self.strategy = strategy
        self.balance = initial_balance
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.trades = []

    def run(self):
        position = None
        avg_entry_price = 0
        qty = 0
        sl_price = 0

        prev_signal = None
        prev_row = None

        print(f"백테스팅 시작 (Final ver): {len(self.df)}개 캔들")

        for index, row in self.df.iterrows():
            current_open = row['Open']
            current_low = row['Low']
            current_high = row['High']
            current_close = row['Close']
            atr = row['ATR']

            # ---------------------------
            # 1. 포지션 관리 (Only 청산)
            # ---------------------------
            if position is not None:
                exit_signal = False
                exit_price = 0

                # [수정] 트레일링 스탑: ATR 3.0 (809% 수익 냈던 설정값으로 복구!)
                if position == 'LONG':
                    new_sl = current_close - (atr * 3.0)
                    if new_sl > sl_price: sl_price = new_sl

                    if current_low <= sl_price:
                        exit_signal = True
                        exit_price = sl_price

                elif position == 'SHORT':
                    new_sl = current_close + (atr * 3.0)
                    if new_sl < sl_price: sl_price = new_sl

                    if current_high >= sl_price:
                        exit_signal = True
                        exit_price = sl_price

                if exit_signal:
                    if position == 'LONG':
                        pnl = (exit_price - avg_entry_price) * qty
                    else:
                        pnl = (avg_entry_price - exit_price) * qty

                    fee = (avg_entry_price * qty * self.taker_fee) + (exit_price * qty * self.taker_fee)
                    self.balance += (pnl - fee)
                    self.trades.append({'time': index, 'balance': self.balance, 'type': 'Exit'})

                    position = None
                    qty = 0
                    prev_signal = None
                    continue

            # ---------------------------
            # 2. 신규 진입
            # ---------------------------
            if position is None and prev_signal is not None:
                entry_price = current_open
                stop_loss_dist = prev_row['ATR'] * 3.0  # 여기도 3.0으로 통일

                if stop_loss_dist > 0:
                    # [공격적 자금 관리] 잔고의 4% 베팅 (809% 달성 핵심)
                    risk_amount = self.balance * 0.04
                    qty = risk_amount / stop_loss_dist

                    if (qty * entry_price) > (self.balance * 3):
                        qty = (self.balance * 3) / entry_price

                    position = prev_signal
                    avg_entry_price = entry_price

                    if position == 'LONG':
                        sl_price = entry_price - stop_loss_dist
                    else:
                        sl_price = entry_price + stop_loss_dist

            # 신호 저장
            signal = self.strategy.get_signal(row)
            prev_signal = signal
            prev_row = row

    def plot_results(self):
        if not self.trades:
            print("거래 기록이 없습니다.")
            return

        trade_df = pd.DataFrame(self.trades)
        final_balance = self.balance
        initial_balance = 1000
        total_return = ((final_balance - initial_balance) / initial_balance) * 100

        trade_df['max_balance'] = trade_df['balance'].cummax()
        trade_df['drawdown'] = (trade_df['balance'] - trade_df['max_balance']) / trade_df['max_balance']
        mdd = trade_df['drawdown'].min() * 100

        print(f"\n========== 🏆 최종 성적표 (Final) ==========")
        print(f"초기 잔고: ${initial_balance:,.2f}")
        print(f"최종 잔고: ${final_balance:,.2f}")
        print(f"총 수익률: {total_return:,.2f}%")
        print(f"총 거래수: {len(trade_df)}회")
        print(f"최대 낙폭(MDD): {mdd:.2f}%")
        print(f"============================================\n")

        plt.figure(figsize=(12, 6))
        plt.plot(trade_df['time'], trade_df['balance'], label='Balance', color='red')
        plt.title(f'Equity Curve (Return: {total_return:.0f}%, MDD: {mdd:.1f}%)')
        plt.yscale('log')
        plt.grid(True, which="both", alpha=0.3)
        plt.show()