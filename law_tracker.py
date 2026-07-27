# -*- coding: utf-8 -*-
"""
최신 법령 트래킹
- 실제 운영: 국가법령정보센터 Open API(law.go.kr)에서 추적 대상 법령의
  개정 이력을 주기적으로 조회 → data/law_updates.json 갱신
- API 키(OC)는 https://open.law.go.kr 에서 이메일 아이디로 무료 발급
- 프로토타입: API 키가 없으면 data/law_updates.json의 예시 데이터를 그대로 사용

자동화: report.py와 같은 방식으로 크론 등록 (예: 매일 08시)
    0 8 * * *  cd /path/to/hr-chatbot && python law_tracker.py
"""
import json
import os
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
LAW_PATH = os.path.join(BASE, "data", "law_updates.json")

OC_KEY = os.environ.get("LAW_OC_KEY", "")  # export LAW_OC_KEY=이메일아이디

TRACKED = ["근로기준법", "남녀고용평등과 일ㆍ가정 양립 지원에 관한 법률",
           "근로자퇴직급여 보장법", "최저임금법", "고용보험법"]


def fetch_from_api() -> list[dict]:
    """법령 검색 API로 추적 대상 법령의 최신 시행일 확인"""
    import urllib.parse
    import urllib.request
    updates = []
    for law in TRACKED:
        url = ("https://www.law.go.kr/DRF/lawSearch.do?"
               + urllib.parse.urlencode({
                   "OC": OC_KEY, "target": "law", "type": "JSON", "query": law}))
        with urllib.request.urlopen(url, timeout=10) as res:
            data = json.load(res)
        # 응답에서 법령명·시행일자 추출 (API 응답 구조에 맞춰 파싱)
        for item in data.get("LawSearch", {}).get("law", []):
            updates.append({
                "law": item.get("법령명한글"),
                "article": "-",
                "change": f"현행 시행일 {item.get('시행일자')}",
                "effective_date": item.get("시행일자"),
                "affected_policies": [],
                "action_needed": "시행일이 최근이면 개정 내용 확인",
                "status": "확인 필요",
            })
    return updates


def check():
    with open(LAW_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if OC_KEY:
        try:
            data["updates"] = fetch_from_api()
            data["_comment"] = "국가법령정보센터 Open API 수집 결과"
        except Exception as e:
            print(f"API 조회 실패, 기존 데이터 유지: {e}")
    else:
        print("LAW_OC_KEY 미설정 → 예시 데이터 유지 (open.law.go.kr에서 무료 발급)")
    data["last_checked"] = date.today().isoformat()
    with open(LAW_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"법령 트래킹 갱신 완료: last_checked={data['last_checked']}")


if __name__ == "__main__":
    check()
