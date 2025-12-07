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