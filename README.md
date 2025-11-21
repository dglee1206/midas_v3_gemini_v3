# 일지

## 2025.11.20

> 요구사항
> - 코인 선물 자동매매 프로그램을 만들려고 하고 있다.
> - 거래소는 바이낸스와 빙엑스를 사용할거다.
> - 추세추종 전략을 사용할거고, 스캘핑으로 수익을 극대화 하려고 하고 있다.

### 답변

스캘핑은 '**속도**'와 '**정확성**'이 생명이며, 선물 거래는 '**리스트 관리**'가 핵심.

- **아키텍처 및 전략가이드** 5단계
  1. **기술 스택 및 아키텍처 (Speed & Stability)**
     - 스캘핑은 0.1초 차이로 수익과 손실이 갈린다.
     - **언어: Python** (데이터 분석 및 거래 라이브러리가 가장 풍부함)
     - **핵심 라이브러리**: `CCXT` (Async 버전)
       - 바이낸스와 빙엑스 API를 통합 관리하기 위해 필수.
       - 동기(Sync) 방식이 아닌 **비동기(Async/Await)** 방식을 사용하여 논블로킹 주문 처리를 구현해야 함.
     - **데이터 통신: WebSockets**
       - REST API는 폴링 방식이라 느림
       - 실시간 호가창(Orderbook)과 체결 내역(Trade)을 받기 위해 반드시 웹소켓을 사용해야 함.
  2. **전략 설계: 추세 추종 + 스캘핑 (Logic)**
     - "추세를 따르면서 짧게 먹는다"는 모순될 수 있지만, **멀티 타임프레임(Multi-Timeframe)** 전략을 쓰면 가능함.
     - **A. 추세 판단 (상위 시간봉: 15분/1시간)**
       - 큰 흐름이 상승인지 하락인지 먼저 파악한다.
       - **도구**: EMA(지수 이동 평균) 200선, MACD
       - **로직**: 가격이 EMA 200 위에 있으면 **Long(매수)만** 진입, 아래에 있으면 **Short(매도)만** 진입한다. (역추세 매매 금지)
     - **B. 진입 타이밍 (하위 시간봉: 1분/5분)**
       - 큰 추세가 정해진 상태에서, 일시적인 눌림목(Pullback)이나 돌파(Breakout)를 노린다.
       - **도구**: RSI(상대 강도지수), 볼리저 밴드
       - **로직예시(Long 기준)**:
         1. 1시간봉 추세가 상승(EMA 200위)이다.
         2. 1분봉에서 RSI가 30 이하(과매도)를 찍고 다시 올라올때 진입.
         3. 또는 볼린저 밴드 하단을 터치하고 양봉이 나올 때 진입
  3. **거래소별 특성 및 대응 (Exchange Handling)**
     - 두 거래소를 동시에 사용하는 이유 (차익거래인지, 분산 투자인지)에 따라 대응이 다름.
       - **Binance**: 유동성이 풍부하여 슬리피지가 적음. 메인 거래용으로 적합
       - **BingX**: 펀딩비나 수수료 이벤트가 있을때 유리함.
       - **주의점**: 두 거래소의 API 속도 제한(Rate Limit)이 다름. 봇이 멈추지 않도록 `RateLimit` 에러 핸들링을 철저히 해야 함.
  4. **리스크 관리 (Risk management - 생존의 핵심)**
     - 선물 스캘핑에서 봇이 망가지는 가장 큰 이유는 ***한 번의 큰 손실*** 임.
       - **손익비(Risk Reward Ratio)**: 스캘핑은 승률이 중요하지만, 손익비가 1:1 이상은 되어야 함. (예: 익절 0.5%, 손절 0.3%)
       - **수수료 계산**: 스캘핑은 거래 횟수가 많음. `(진입 수수료 + 청산 수수료) > 기대 수익` 이면 100번 이겨도 잔고는 줄어든다. 반드시 **메이커(Maker, 지정가) 주문**을 활용하여 수수료를 낮추는 로직을 짜야 함.
       - **최대 손실 제한(Drawdown Limit)**: 하루 누적 손실이 시드의 5%에 도달하면 봇이 자동으로 24시간동안 꺼지도록 설계함.
  5. **개발 로드맵 (Next Steps)**
     1. **환경 설정** : Python, 가상 환경, CCXT 설치 및 API Key 보안 설정 (`.env`)
     2. **데이터 수집기 구현**: 바이낸스/빙엑스 웹소켓 연결 및 실시간 가격 수신
     3. **전략 알고리즘 구현**: EMA, RSI 등을 계산하고 매수/매도 신호를 생성하는 함수 작성.
     4. **주문 집행 엔젠**: 신호 발생 시 실제로 주문을 넣고, 익절/손절을 거는 기능
     5. **백테스팅 & 페이퍼 트레이딩**: 과거 데이터로 검증하고, 가상 자금으로 실전 테스트.

---

## 2025.11.21

> 요구사항
> **기본 골격 코드 작성**
> **"Python"과 "CCXT"를 이용해서 바이낸스와 빙엑스의 현재 가격을 실시간으로 가져오고, 간단한 이동평균선(EMA)을 계산하는 기초 코드를 먼저 작성하라.**

### 답변

**Python의 비동기(Async) 기능**을 활용하여 바이낸스와 빙엑스의 선물 시장 데이터를 가져오고, 추세 판단의 핵심인 **EMA(지수이동평균)**를 계산하는 기본골격코들 작성.

#### 1. 사전 준비 (라이브러리 설치)

터미널에서 아래 명령어로 필수 라이브러리 설치

- `ccxt`: 암호화폐 거래소 통합 라이브러리 (비동기 지원)
- `pandas`: 데이터 분석 및 지표(EMA) 계산
- `python-dotenv`: API 키 보안 관리

```bash
pip install ccxt pandas python-dotenv
```

#### 2. 보안 설정(.env 파일)

프로젝트 폴더에 `.env` 파일을 만들고 아래와 같이 채워줌.

```bash
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
BINGX_API_KEY=your_bingx_api_key
BINGX_SECRET=your_bingx_secret
```

#### 3. 봇 핵심 코드 (bot_core.py)

```python
import asyncio
import ccxt.async_support as ccxt   # 비동기 모듈 사용
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# 1. 환경 변수 로드
load_dotenv()

class CryptoBot:
    def __init__(self):
        # 거래소 객체 초기화 (비동기 방식)
        self.exchanges = {
            "binance": ccxt.binance({
                "apiKey": os.getenv("BINANCE_API_KEY"),
                "secret": os.getenv("BINANCE_SECRET"),
                "enableRateLimit": True,    # API 차단 방지
                "options": {'defaultType': 'future'}    # 선물 거래 설정
            }),
            "bingx": ccxt.bingx({
                "apiKey": os.getenv("BINGX_API_KEY"),
                "secret": os.getenv("BINGX_SECRET"),
                "enableRateLimit": True,
                "options": {'defaultType': 'swap'}
            }),
        }
```