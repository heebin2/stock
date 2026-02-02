import os
import re
import json
from datetime import datetime
from google import genai
from .crawl import localize_key, compute_summary


def build_prompt(company_name: str, stock_code: str, stock_data: dict, current_time: str) -> str:
    data_str = "\n".join([f"- {localize_key(k)}: {v}" for k, v in stock_data.items()])
    basic_info_str = "\n".join([f" - {localize_key(k)}: {v}" for k, v in stock_data.items()])
    summary = compute_summary(stock_data)
    summary_str = "\n".join([f" - {k}: {v}" for k, v in summary.items()]) if summary else " - (요약 없음)"

    return f"""
현재 시점: {current_time}

다음은 '{company_name}'(코드: {stock_code}) 종목의 네이버 금융에서 수집한 현재 데이터입니다:

{data_str}

위의 현재 데이터를 바탕으로 다음을 분석해주세요:

1. 기본 정보 분석 (위의 데이터 활용)
2. 최근 주가 동향 및 기술적 평가
3. 투자 의견 (매수/매도/보유 중 선택)
4. 선택 이유를 100자 이내로 간결하게

분석 형식:
[{company_name}]

기본 정보
{basic_info_str}

[요약 정보]
{summary_str}

[분석 결과]
────────────────────────────────────────────────────────────
의견: [매수/매도/보유 중 하나]
사유: [100자 이내 이유]
"""


def run_gemini_analysis(company_name: str, stock_code: str, stock_data: dict):
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\nGemini API 키가 설정되지 않았습니다.")
        print("환경변수 GEMINI_API_KEY를 설정해주세요.")
        print("예: export GEMINI_API_KEY='your-api-key'")
        return
    
    client = genai.Client(api_key=api_key)
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    prompt = build_prompt(company_name, stock_code, stock_data, current_time)
    print(" ")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        if response and response.text:
            # ** 기호 제거
            text = response.text.replace('**', '')
            print(text)
        else:
            print("응답이 없습니다.")
    except Exception as e:
        emsg = str(e)
        # 오류 메시지 추출 (response_json 우선, 없으면 문자열에서 파싱)
        resp_msg = None
        try:
            if hasattr(e, 'response_json') and e.response_json:
                resp_msg = e.response_json.get('error', {}).get('message')
        except:
            pass
        if not resp_msg:
            m = re.search(r"'message':\s*'([^']+)'", emsg) or re.search(r'"message":\s*"([^"]+)"', emsg)
            if m:
                resp_msg = m.group(1)

        if ('429' in emsg) or ('RESOURCE_EXHAUSTED' in emsg) or ('quota' in emsg.lower()):
            print("Gemini 쿼터 초과: 잠시 후 다시 시도해주세요.")
        else:
            print("Gemini API 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")