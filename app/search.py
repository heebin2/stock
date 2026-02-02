import re
import requests
from bs4 import BeautifulSoup


def _get_krx_data():
    """FinanceDataReader에서 한국 주식 데이터 로드"""
    try:
        import FinanceDataReader as fdr
        return fdr.StockListing("KRX")
    except Exception as e:
        return None


def get_stock_code_from_naver(stock_name: str) -> str | None:
    """종목 코드 조회 - FinanceDataReader + 네이버 검색"""
    try:
        # 1. FinanceDataReader에서 동적 검색
        result = _search_from_finance_data_reader(stock_name)
        if result:
            return result
        
        # 2. 네이버 파이낸스에서 직접 검색
        result = _search_from_naver_finance(stock_name)
        if result:
            return result
        
        return None
    except Exception as e:
        return None


def _search_from_finance_data_reader(stock_name: str) -> str | None:
    """FinanceDataReader에서 종목 검색"""
    try:
        krx = _get_krx_data()
        if krx is None:
            return None
        
        # 정확한 일치
        exact_match = krx[krx['Name'] == stock_name]
        if len(exact_match) > 0:
            return exact_match.iloc[0]['Code']
        
        # 포함 검색 (대소문자 무시)
        partial_match = krx[krx['Name'].str.contains(stock_name, na=False, case=False)]
        if len(partial_match) > 0:
            return partial_match.iloc[0]['Code']
        
        return None
    except Exception as e:
        return None


def _search_from_naver_finance(stock_name: str) -> str | None:
    """네이버 파이낸스에서 직접 종목명 검색"""
    try:
        import urllib.parse
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        # 1. 네이버 파이낸스 종목 검색 URL
        search_url = f"https://finance.naver.com/search/searchList.naver?keyword={urllib.parse.quote(stock_name)}"
        
        resp = requests.get(search_url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        
        # HTML에서 종목 코드 추출 - 여러 패턴 시도
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 패턴 1: 일반 검색 결과 테이블
        stock_rows = soup.find_all('tr')
        for row in stock_rows:
            # 셀 추출
            cells = row.find_all('td')
            if len(cells) >= 2:
                # 종목명이 포함된 셀 찾기
                name_cell = cells[0].get_text(strip=True)
                if stock_name in name_cell:
                    # 링크에서 코드 추출
                    link = cells[0].find('a', href=re.compile(r'code=\d{6}'))
                    if link:
                        code_match = re.search(r'code=(\d{6})', link.get('href', ''))
                        if code_match:
                            return code_match.group(1)
        
        # 패턴 2: 직접 링크에서 추출
        links = soup.find_all('a', href=re.compile(r'code=\d{6}'))
        for link in links:
            text = link.get_text(strip=True)
            if stock_name.lower() in text.lower():
                code_match = re.search(r'code=(\d{6})', link.get('href', ''))
                if code_match:
                    return code_match.group(1)
        
        # 패턴 3: 첫 번째 검색 결과 반환 (부분 매칭)
        if links:
            code_match = re.search(r'code=(\d{6})', links[0].get('href', ''))
            if code_match:
                # 최후의 수단 - 정확한 이름 확인 후
                code = code_match.group(1)
                # 검색된 코드로 실제 종목 정보 확인
                verify_url = f"https://finance.naver.com/item/main.naver?code={code}"
                verify_resp = requests.get(verify_url, headers=headers, timeout=5)
                verify_resp.encoding = 'utf-8'
                if stock_name in verify_resp.text:
                    return code
        
        return None
    except Exception as e:
        return None
