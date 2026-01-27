import re
import requests
from bs4 import BeautifulSoup


def _clean_number(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r'[\d,]+', str(text).strip())
    if m:
        return m.group().replace(',', '')
    return None


def _to_float(value):
    try:
        return float(str(value).replace(',', '').strip())
    except:
        return None


def localize_key(key: str) -> str:
    mapping = {
        'current_price': '현재가',
        'name': '회사명',
        'open': '시가',
        'high': '고가',
        'low': '저가',
        'per': 'PER',
        'pbr': 'PBR',
        'roe': 'ROE',
        'eps': 'EPS',
        'bps': 'BPS',
        'div_yield': '배당수익률',
        'market_cap': '시가총액',
        'volume': '거래량',
        'prev_close': '전일가',
        'change_pct': '등락률',
        'upper_limit': '상한가',
        'lower_limit': '하한가',
        '52w_high': '52주 최고',
        '52w_low': '52주 최저',
        'trading_value_million': '거래대금(백만)',
        'market': '시장',
    }
    return mapping.get(key, key)


def compute_summary(stock_data: dict) -> dict:
    cur = _to_float(stock_data.get('current_price'))
    prev = _to_float(stock_data.get('prev_close'))
    high = _to_float(stock_data.get('high'))
    low = _to_float(stock_data.get('low'))
    h52 = _to_float(stock_data.get('52w_high'))
    l52 = _to_float(stock_data.get('52w_low'))

    summary = {}

    if cur is not None and prev is not None:
        summary['일변화(원)'] = f"{cur - prev:.0f}"
        if not stock_data.get('change_pct') and prev:
            summary['일변화(%)'] = f"{(cur - prev) / prev * 100:.2f}%"

    if prev and high and low:
        summary['장중변동폭(%)'] = f"{(high - low) / prev * 100:.2f}%"

    if cur and h52 and l52 and (h52 - l52) > 0:
        pos = (cur - l52) / (h52 - l52) * 100
        summary['52주내 위치(%)'] = f"{pos:.2f}%"
        summary['52주고점까지 거리(%)'] = f"{(h52 - cur) / h52 * 100:.2f}%"

    if stock_data.get('trading_value_million'):
        summary['거래대금(백만)'] = stock_data['trading_value_million']

    return summary


def get_naver_finance_data(stock_code: str) -> dict | None:
    try:
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        data: dict = {}

        # 제목에서 회사명 추출
        try:
            title = soup.select_one("title")
            if title:
                text = title.text
                match = re.search(r'(.+?)\s*\((\d{6})', text)
                if match:
                    company_name = match.group(1).strip()
                    company_name = re.sub(r'\s+', ' ', company_name)
                    if company_name and 1 < len(company_name) < 30:
                        data['name'] = company_name
        except:
            pass

        blind_text = " ".join(elem.get_text(" ", strip=True) for elem in soup.select(".blind"))
        try:
            m = re.search(r'전일가\s([0-9,]+)', blind_text)
            if m:
                data['prev_close'] = m.group(1).replace(',', '')
            m = re.search(r'등락률\s([\-0-9.,]+)%', blind_text)
            if m:
                data['change_pct'] = m.group(1)
            m = re.search(r'시가\s([0-9,]+)', blind_text)
            if m:
                data['open'] = m.group(1).replace(',', '')
            m = re.search(r'고가\s([0-9,]+)', blind_text)
            if m:
                data['high'] = m.group(1).replace(',', '')
            m = re.search(r'저가\s([0-9,]+)', blind_text)
            if m:
                data['low'] = m.group(1).replace(',', '')
            m = re.search(r'상한가\s([0-9,]+)', blind_text)
            if m:
                data['upper_limit'] = m.group(1).replace(',', '')
            m = re.search(r'하한가\s([0-9,]+)', blind_text)
            if m:
                data['lower_limit'] = m.group(1).replace(',', '')
            m = re.search(r'거래량\s([0-9,]+)', blind_text)
            if m:
                data['volume'] = m.group(1)
            m = re.search(r'거래대금\s([0-9,]+)백만', blind_text)
            if m:
                data['trading_value_million'] = m.group(1)
            m = re.search(r'52주\s?(?:최고|고가)\s([0-9,]+)', blind_text)
            if m:
                data['52w_high'] = m.group(1).replace(',', '')
            m = re.search(r'52주\s?(?:최저|저가)\s([0-9,]+)', blind_text)
            if m:
                data['52w_low'] = m.group(1).replace(',', '')
            m = re.search(r'종목코드\s\d+\s(코스피|코스닥)', blind_text)
            if m:
                data['market'] = m.group(1)
        except:
            pass

        html_text = response.text
        try:
            match = re.search(r'현재가[^<]*?(\d{2,},[0-9,]*)', html_text)
            if match:
                data['current_price'] = match.group(1).replace(',', '')
        except:
            pass

        try:
            for row in soup.select("table tbody tr"):
                cells = row.select("td")
                if len(cells) >= 2:
                    label_text = cells[0].get_text(strip=True)
                    value_text = cells[1].get_text(strip=True)
                    if '시가' == label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['open'] = v
                    elif '고가' == label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['high'] = v
                    elif '저가' == label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['low'] = v
                    elif 'PER' in label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['per'] = v
                    elif 'PBR' in label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['pbr'] = v
                    elif 'ROE' in label_text:
                        v = re.search(r'[\-0-9.]+', value_text)
                        if v:
                            data['roe'] = v.group()
                    elif 'EPS' in label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['eps'] = v
                    elif 'BPS' in label_text:
                        v = _clean_number(value_text)
                        if v:
                            data['bps'] = v
                    elif '배당수익률' in label_text:
                        m2 = re.search(r'([0-9.]+)%', value_text)
                        if m2:
                            data['div_yield'] = m2.group(1)
                    elif '시가총액' in label_text:
                        data['market_cap'] = value_text
                    elif '거래량' in label_text and '주' in value_text:
                        v = _clean_number(value_text)
                        if v:
                            data['volume'] = v
        except:
            pass

        return data

    except Exception as e:
        print(f"네이버 금융 크롤링 실패: {e}")
        return None
