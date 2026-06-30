import json
import os
import time

GEMINI_MODEL = "gemini-2.5-flash"

_ROLE = (
    "너는 미국 거시경제 지표, 연방/주정부 정책, 글로벌 테크 인프라(AI/데이터센터/반도체/우주항공) 트렌드를 "
    "종합 분석하는 전문 경제 애널리스트야. "
    "지정한 날짜 범위 내에서 발생한 핵심 뉴스를 단 하나도 누락 없이(Zero-Leakage) 추출하고 "
    "상호 연관성을 분석해 요약 리포트를 제공해라.\n\n"
)

_OUTPUT_RULES = """
# 출력 규칙
- 도입 문장 없이 첫 줄부터 바로 - 로 시작
- 항목 2개 목표. 논리적으로 연결된 사실(인과관계, 조건-결과, 맥락-행동)은 하나의 항목으로 통합. 내용이 너무 많아 2개로 압축 불가한 경우에만 3개까지 허용
- 각 항목: 핵심 사실 한 줄 헤드라인(- 로 시작, 기업명 + 핵심 사건/수치 위주, 15단어 이내) + 세부내용/시사점 1개(공백 2칸 + - 로 시작, 1~2줄 허용). 세부내용이 반드시 2개 필요한 경우에만 최대 2개까지 허용
- 모든 내용은 반드시 - 와 같은 줄에 작성. - 다음 줄에 별도 문단으로 내용 작성 금지
- 한국어, 기술 용어·기업명·수치는 영어/숫자 유지
- 구체적 수치·날짜 반드시 포함
- 명사형/동사 어근 어미 사용 (합니다/입니다/있습니다 금지), 조사 최소화
- 마크다운 헤더(#) 및 볼드(**) 사용 금지

출력 예시:
- Intel·SpaceX, 美정부 공급망 다변화 요청 대응 100% 미국산 Memory 및 Substrate 내재화 노력 가속화
  - USG, 국가 안보 이유로 Intel·SpaceX·Tesla 연합의 Terafab Project에 Micron 등 미국 내 핵심 Memory 및 기판 제조사와의 협업 공식 요청
  - Intel EMIB Packaging Line과 미국산 HBM/DRAM Value Chain 단일 부지 통합, 'Made in USA' AI Infra 자립화 구축 촉진
- Intel, 최첨단 공정 '18A-P' Risk Production 개시 및 Apple 수주 가능성 모색
  - 기존 18A 대비 성능 9% 향상 / 전력 18% 절감 홍보 중이나, 90% 이상 수율 달성 및 EMIB 패키징 기술 상업 계약 체결 여부가 핵심 성패
"""


def _gemini_generate(client, prompt: str, max_retries: int = 4) -> str:
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"tools": [{"google_search": {}}]},
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait = [10, 20, 30][min(attempt, 2)]
                print(f"  Gemini error (retry {attempt + 1}/{max_retries - 1}, {wait}s): {e}")
                time.sleep(wait)
            else:
                raise


def main():
    with open("request.json", encoding="utf-8") as f:
        req = json.load(f)

    week_start = req["week_start"]
    week_end = req["week_end"]
    run_id = req["run_id"]

    api_key = os.environ["GEMINI_API_KEY"]

    from google import genai
    client = genai.Client(api_key=api_key)

    print(f"Generating Section 1 ({week_start} ~ {week_end})...")
    s1 = _gemini_generate(client, (
        _ROLE
        + f"기간: {week_start} ~ {week_end}\n\n"
        + "# 필수 분석 카테고리\n\n"
        + "1. [거시경제 (Macro)]\n"
        + "- 고용(비농업 고용, 실업률 등), 물가(CPI/PPI/PCE), 소비 지표\n"
        + "- 통화 정책(Fed 연준 금리 결정, FOMC 의사록, 위원 발언) 및 국채 금리 동향\n\n"
        + "2. [행정부/연방 및 주정부 정책]\n"
        + "- 백악관 행정명령, 반도체법(Chips Act) 보조금 및 대중국 수출 규제 변동\n"
        + "- 주정부 단위의 데이터센터 신설 제동, 전력망(Grid) 및 용수 규제 이슈\n"
        + _OUTPUT_RULES
    ))
    print("  Done.")

    print("Generating Section 2...")
    s2 = _gemini_generate(client, (
        _ROLE
        + f"기간: {week_start} ~ {week_end}\n\n"
        + "# 필수 분석 카테고리\n\n"
        + "3. [빅테크 & 프런티어 랩 동향]\n"
        + "- 주요 빅테크(MS, Google, Meta, Apple, Amazon)의 신규 자본지출(CAPEX) 및 가이던스 조정\n"
        + "- 프런티어 랩스(OpenAI, Anthropic 등)의 신규 AI 모델/서비스 발표\n"
        + "- AI 서비스 수익성(구독료 변동) 및 빅테크 간 API 가격 전쟁 동향\n\n"
        + "4. [반도체 & 하드웨어 인프라]\n"
        + "- GPU 및 AI 반도체 밸류체인(NVIDIA, AMD, TSMC, SK하이닉스, 인텔 등) 신제품 론칭 및 공급망 동향\n"
        + "- 데이터센터 전문 투자사 및 리츠(DigitalBridge, Blackstone 등)의 대규모 부지 확보 및 인프라 투자 뉴스\n\n"
        + "5. [우주/항공 테크 및 인프라]\n"
        + "- SpaceX(Starlink 포함) 및 주요 우주항공 업체의 발사 스케줄, 신기술 테스트 결과\n"
        + "- 위성 인터넷 인프라 확장 및 정부 계약/규제 관련 핵심 뉴스\n"
        + _OUTPUT_RULES
    ))
    print("  Done.")

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump({
            "run_id": run_id,
            "week_start": week_start,
            "week_end": week_end,
            "section1": s1,
            "section2": s2,
        }, f, ensure_ascii=False, indent=2)
    print("result.json written.")


if __name__ == "__main__":
    main()
