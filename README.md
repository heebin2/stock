# 한국 주식 분석 도구

네이버 금융에서 웹 크롤링으로 수집한 한국 주식 데이터를 Gemini AI가 분석해주는 도구입니다.

## 기능

- **종목 검색**: 한국 주식 이름으로 자동으로 종목 코드 검색 (네이버 검색 기반)
- **웹 크롤링**: 네이버 금융에서 종목 정보 실시간 수집
  - 현재가, 전일가, 시가, 고가, 저가
  - 거래량, 거래대금
  - PER, PBR, ROE, EPS, BPS, 배당수익률
  - 시가총액, 52주 고가/저가, 상한가/하한가
  - 시장(코스피/코스닥)
- **AI 분석**: Google Gemini 2.5 Flash Lite를 활용한 투자 의견 제공
  - 기본 정보 분석
  - 기술적 평가
  - 매수/매도/보유 의견 및 이유

## 요구사항

- Python 3.13+
- Google Gemini API 키

## 설치

### 1. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate  # Windows
```

### 2. 패키지 설치
```bash
pip install beautifulsoup4 requests google-genai
```

### 3. Gemini API 키 설정
환경변수로 `GEMINI_API_KEY` 설정:
```bash
export GEMINI_API_KEY="your-api-key"
```

## 사용법

### 기본 사용
```bash
python main.py 종목명
```

### 예시
```bash
# 회사명으로 검색
python main.py 삼성전자
python main.py 다날
python main.py 휴림로봇

# 종목 코드로 직접 검색 (6자리 숫자)
python main.py 005930

# 여러 단어 포함 (따옴표 사용)
python main.py "KODEX 200선물인버스2X"
```

## 출력 형식

```
종목명(코드)
 - 현재가: 값
 - 전일가: 값
 - 시가: 값
 ...

요약 정보:
 - 일변화(원): 값
 - 일변화(%): 값
 - 장중변동폭(%): 값
 - 52주내 위치(%): 값
 ...

[Gemini 분석 결과]
의견: 매수/매도/보유
사유: 투자 근거
```

## 프로젝트 구조

```
stock/
├── main.py                 # 메인 진입점
├── README.md              # 이 파일
└── app/
    ├── search.py          # 종목 검색 (네이버 기반)
    ├── crawl.py           # 웹 크롤링 (네이버 금융)
    └── gemini_client.py   # Gemini AI 분석
```

## 모듈 설명

### `app/search.py`
- `get_stock_code_from_naver(stock_name)`: 종목 이름으로 6자리 코드 반환
- 네이버 검색 결과에서 자동 추출, 페이지 제목으로 검증
- 여러 검색 쿼리 시도로 높은 정확도 보장

### `app/crawl.py`
- `get_naver_finance_data(stock_code)`: 네이버 금융 페이지에서 데이터 추출
- `compute_summary(stock_data)`: 일변화, 장중변동폭, 52주 위치 등 계산
- `localize_key(key)`: 영문 필드명을 한글로 변환

### `app/gemini_client.py`
- `run_gemini_analysis()`: Gemini API로 투자 분석 요청
- 크롤링한 모든 데이터를 JSON으로 전달
- 429 에러(쿼터 초과) 친화적 처리

## 주의사항

- 네이버 금융 페이지 레이아웃 변경 시 크롤링 로직 수정 필요
- Gemini API 쿼터 제한 있을 수 있음
- 실제 투자 결정 전 추가 분석 권장

## 라이선스

개인 학습용
