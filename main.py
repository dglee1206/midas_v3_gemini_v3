import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from data_loader import DataLoader
from strategy import ScalpingStrategy
from backtester import Backtester

# ---------------------------------------------------------
# 1. 데이터 로드
# ---------------------------------------------------------
loader = DataLoader('BTCUSDT_5m_2017-08-17_to_2025-10-31.csv')
df = loader.load_data()
print("데이터 컬럼:", df.columns)
print("데이터 샘플:\n", df.head())
# 데이터 인덱스 정렬 확인
is_monotonic = df.index.is_monotonic_increasing
print("데이터 인덱스 정렬 확인:", is_monotonic)

if not is_monotonic:
    print("⚠️ 경고: 데이터 정렬이 올바르지 않습니다. 정렬을 수행합니다.")
    df.sort_index(inplace=True)

df = loader.add_indicators()

# ---------------------------------------------------------
# 2. 전략 설정 (중요: 피라미딩은 3배 레버리지 권장)
# ---------------------------------------------------------
# 50배는 변동성을 못 버티고 터집니다. 3배로 설정하세요.
strategy = ScalpingStrategy(leverage=3)

# ---------------------------------------------------------
# 3. 백테스팅 실행
# ---------------------------------------------------------
# 빙엑스 시장가 수수료 0.05% 가정 (보수적)
backtester = Backtester(df, strategy, maker_fee=0.0005)
backtester.run()

# 기본 결과 출력
# backtester.print_result() # 아래 plot_results에서 더 자세히 나오니 생략 가능


# ---------------------------------------------------------
# 4. 결과 시각화 및 MDD 출력 함수
# ---------------------------------------------------------
def plot_results(backtester):
    # 거래 기록을 데이터프레임으로 변환
    trade_df = pd.DataFrame(backtester.trades)

    if len(trade_df) == 0:
        print("거래 기록이 없습니다.")
        return

    # --- [순서 변경] 통계 계산 및 출력을 먼저 수행 ---
    initial_balance = 1000  # 초기 자금 가정
    final_balance = backtester.balance
    total_return = ((final_balance - initial_balance) / initial_balance) * 100

    # MDD (최대 낙폭) 계산
    # balance 컬럼을 기준으로 누적 최대값(cummax)을 구하고, 현재 값과의 차이를 계산
    trade_df['max_balance'] = trade_df['balance'].cummax()
    trade_df['drawdown'] = (trade_df['balance'] - trade_df['max_balance']) / trade_df['max_balance']
    mdd = trade_df['drawdown'].min() * 100

    print(f"\n========== 🏆 최종 성적표 ==========")
    print(f"초기 잔고: ${initial_balance:,.2f}")
    print(f"최종 잔고: ${final_balance:,.2f}")
    print(f"총 수익률: {total_return:,.2f}%")
    print(f"총 거래수: {len(trade_df)}회")
    print(f"최대 낙폭(MDD): {mdd:.2f}%")
    print(f"====================================\n")

    # --- [그래프 그리기] ---
    plt.figure(figsize=(12, 6))

    # 수익 곡선
    plt.plot(trade_df['time'], trade_df['balance'], label='Account Balance', color='green')

    # MDD 구간 표시 (선택사항: 붉은색 영역으로 표시)
    # plt.fill_between(trade_df['time'], trade_df['balance'], trade_df['max_balance'], color='red', alpha=0.1, label='Drawdown')

    plt.title(f'Trading Bot Equity Curve (MDD: {mdd:.2f}%)')
    plt.xlabel('Date')
    plt.ylabel('Balance ($)')
    plt.yscale('log')  # 로그 스케일 (수익률이 높을 때 필수)
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()

    # 그래프 보여주기 (이 코드가 실행되면 창을 닫을 때까지 멈춤)
    plt.show()


# 함수 실행
plot_results(backtester)