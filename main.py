import matplotlib.pyplot as plt
import pandas as pd

from data_loader import DataLoader
from strategy import ScalpingStrategy
from backtester import Backtester

# 1. 데이터 로드
loader = DataLoader('BTCUSDT_5m_2017-08-17_to_2025-10-31.csv')
df = loader.load_data()
print("데이터 컬럼:", df.columns)
print("데이터 샘플:\n", df.head())
print("데이터 인덱스 정렬 확인:", df.index.is_monotonic_increasing) # True여야 정상

df = loader.add_indicators()

# 2. 전략 설정 (레버리지 50배)
strategy = ScalpingStrategy(leverage=50)

# 3. 백테스팅 실행 (빙엑스 시장가 수수료 0.05% 가정)
backtester = Backtester(df, strategy, maker_fee=0.0005)
backtester.run()
backtester.print_result()


def plot_results(backtester):
    # 거래 기록을 데이터프레임으로 변환
    trade_df = pd.DataFrame(backtester.trades)

    if len(trade_df) == 0:
        print("거래 기록이 없습니다.")
        return

    # 1. 누적 수익 곡선 (Balance History)
    plt.figure(figsize=(12, 6))
    plt.plot(trade_df['time'], trade_df['balance'], label='Account Balance', color='green')
    plt.title('Trading Bot Equity Curve (Pyramiding Strategy)')
    plt.xlabel('Date')
    plt.ylabel('Balance ($)')
    plt.yscale('log')  # 로그 스케일로 봐야 150배 수익이 한눈에 보임
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()
    plt.show()

    # 2. 통계 요약
    initial_balance = 1000  # 가정
    final_balance = backtester.balance
    total_return = ((final_balance - initial_balance) / initial_balance) * 100

    # MDD 계산
    trade_df['max_balance'] = trade_df['balance'].cummax()
    trade_df['drawdown'] = (trade_df['balance'] - trade_df['max_balance']) / trade_df['max_balance']
    mdd = trade_df['drawdown'].min() * 100

    print(f"========== 🏆 최종 성적표 ==========")
    print(f"초기 잔고: ${initial_balance:,.2f}")
    print(f"최종 잔고: ${final_balance:,.2f}")
    print(f"총 수익률: {total_return:,.2f}%")
    print(f"총 거래수: {len(trade_df)}회")
    print(f"최대 낙폭(MDD): {mdd:.2f}% (이만큼 깨질 때 버텨야 함)")
    print(f"====================================")


# 실행
plot_results(backtester)