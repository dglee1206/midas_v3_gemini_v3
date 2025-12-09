import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from data_loader import DataLoader
from strategy import ScalpingStrategy
from backtester import Backtester

# 파일명은 본인 환경에 맞게 수정하세요
loader = DataLoader('BTCUSDT_5m_2017-08-17_to_2025-10-31.csv')
df = loader.load_data()
df = loader.add_indicators()

strategy = ScalpingStrategy(leverage=3)
backtester = Backtester(df, strategy)
backtester.run()
backtester.plot_results()