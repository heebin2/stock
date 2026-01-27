import re
import requests
from bs4 import BeautifulSoup


def get_stock_code_from_naver(stock_name: str) -> str | None:
    """네이버 검색으로 종목 코드 조회 (최적화된 접근)"""
    try:
        import urllib.parse
        encoded_name = urllib.parse.quote(stock_name)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        def norm(s):
            return re.sub(r'\s+', '', s).lower()

        # 공통 함수: 모든 검색 쿼리에 적용
        def find_code_from_search(search_url):
            try:
                resp = requests.get(search_url, headers=headers, timeout=10)
                resp.encoding = 'utf-8'
                
                # finance.naver.com 링크에서 모든 코드 추출
                codes = set(re.findall(r'finance\.naver\.com/item/.*?code=(\d{6})', resp.text))
                
                # 각 코드 검증 (페이지 제목으로 확인)
                for code in sorted(codes):
                    try:
                        page = requests.get(f"https://finance.naver.com/item/main.naver?code={code}", 
                                          headers=headers, timeout=5)
                        page.encoding = 'utf-8'
                        page_text = page.text.lower()
                        
                        # 제목, h1, h2에서 검색
                        if (f'<title>' in page.text and norm(stock_name) in norm(page.text[page.text.find('<title>'):page.text.find('</title>')]) or
                            f'{norm(stock_name)}' in norm(page_text[:3000])):  # 페이지 상단 3000자에서 확인
                            return code
                    except:
                        continue
                
                # 검증 실패 시 첫 코드 반환 (최후의 수단)
                if codes:
                    return sorted(codes)[0]
            except:
                pass
            
            return None

        # 다양한 검색 쿼리 시도 (우선순위대로)
        search_queries = [
            f"https://search.naver.com/search.naver?where=nexearch&query={encoded_name}&sm=top_sug",
            f"https://search.naver.com/search.naver?where=nexearch&query={encoded_name}+주식&sm=top_sug",
            f"https://search.naver.com/search.naver?where=nexearch&query={encoded_name}+주&sm=top_sug",
            f"https://search.naver.com/search.naver?where=nexearch&query={encoded_name}+stock&sm=top_sug",
        ]

        for search_url in search_queries:
            result = find_code_from_search(search_url)
            if result:
                return result

        return None
    except Exception as e:
        return None
