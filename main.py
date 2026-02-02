import sys
import re
from datetime import datetime
from dotenv import load_dotenv
from app.search import get_stock_code_from_naver
from app.crawl import get_naver_finance_data, compute_summary, localize_key
from app.gemini_client import run_gemini_analysis

# .env 파일 로드
load_dotenv()

def print_crawled_data(stock_name, stock_code, stock_data):
    print(f"{stock_name}({stock_code})")
    
    for key, value in stock_data.items():
        # 키를 한글로 변환
        display_key = localize_key(key)
        # 값 포맷 조정(퍼센트 표시)
        display_val = value
        if key in ('change_pct', 'div_yield') and isinstance(value, str) and not value.endswith('%'):
            display_val = f"{value}%"
        print(f" - {display_key}: {display_val}")

    # 요약 정보
    summary = compute_summary(stock_data)
    if summary:
        print("\n요약 정보:")
        for k, v in summary.items():
            print(f" - {k}: {v}")


def analyze_stock_with_gemini(stock_input: str):
    stock_code: str | None = None

    if stock_input.isdigit() and len(stock_input) == 6:
        stock_code = stock_input
    else:
        stock_code = get_stock_code_from_naver(stock_input)

    if not stock_code:
        print(f"'{stock_input}' 종목을 찾을 수 없습니다.")
        print("\n종목명 또는 코드가 올바른지 확인해주세요.")
        print("예시:")
        print("  - 정확한 종목명: python main.py '삼성전자'")
        print("  - 종목 코드: python main.py '005930'")
        print("  - 영문 티커: python main.py 'AAPL'")
        return


    stock_data = get_naver_finance_data(stock_code)
    if not stock_data:
        print("데이터를 수집할 수 없습니다.")
        return

    company_name = stock_data.get('name', stock_input)
    if 'name' in stock_data and len(stock_data['name']) > 20:
        company_name = stock_input
    elif 'name' in stock_data:
        company_name = re.sub(r'\(.+?\)', '', stock_data['name']).strip() or stock_input

    print_crawled_data(company_name, stock_code, stock_data)

    # Gemini 호출 분리 모듈 사용
    run_gemini_analysis(company_name, stock_code, stock_data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python main.py <종목명 또는 티커>")
        print("예: python main.py 삼성전자")
        print("    python main.py AAPL")
        print("    python main.py 005930")
        sys.exit(1)
    
    stock_input = sys.argv[1]
    analyze_stock_with_gemini(stock_input)