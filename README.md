# HR 챗봇 프로토타입

검색 전용(retrieval-only) 구조: 답변을 생성하지 않고 사람이 작성한 Q&A에서 찾아 반환합니다.
외부 API 호출 없음 → 개인정보/사내기밀 유출 위험 없음.

## 실행 방법

```bash
pip install streamlit scikit-learn
# 매칭 정확도를 높이려면 (선택, 용량 큼):
pip install sentence-transformers

streamlit run app.py
```

sentence-transformers가 설치돼 있으면 한국어 임베딩 모델(jhgan/ko-sroberta-multitask)을
자동 사용하고, 없으면 TF-IDF로 폴백합니다. 코드는 동일합니다.

## 테스트 계정

| 사번 | 비밀번호 | 역할 |
|---|---|---|
| 20230101 | 1234 | 직원 |
| 20180501 | 1234 | 직원 |
| 20100301 | admin | 담당자 |

## 보안 설계 — 타인 정보 조회 원천 차단 (4중 방어)

1. **구조적 차단**: 개인정보는 챗봇 지식(qa_data.json)에 아예 존재하지 않음.
   챗봇은 규정·법령만 답하므로 어떤 질문에도 타인 정보가 출력될 수 없음.
2. **세션 기반 조회**: 연차·경조사비 조회는 로그인 세션의 사번으로만 수행.
   조회 대상 사번을 사용자 입력으로 받지 않음 (가장 중요한 원칙).
3. **질문 필터**: 타인 사번·이름·타인 조회 표현이 포함된 질문은 매칭 전에 차단.
4. **감사 로그**: 차단된 시도는 `data/security_log.json`에 기록되어 담당자 페이지에서 확인.

필터 테스트: `python test_security.py` (9개 시나리오)

## 파일 구조

- `data/qa_data.json` — Q&A 데이터 (질문 + 유사표현 + 답변 + 사내규정/법령 매핑 + 관계유형 L1~L3)
- `data/employees.json` — 가상 직원 데이터
- `data/unanswered.json` — 미답변 질문 로그 (자동 생성)
- `data/security_log.json` — 보안 차단 로그 (자동 생성)
- `matcher.py` — 유사도 매칭 엔진 (단독 테스트: `python matcher.py`)
- `test_security.py` — 보안 필터 테스트
- `app.py` — Streamlit 웹앱 (로그인 → 역할 분기 → 버튼/채팅)
- `코드북_초안.docx` — 데이터 구축 기준 문서

## Q&A 추가 방법

`qa_data.json`의 `qa_items`에 항목 추가:

```json
{
  "id": "leave-004",
  "category": "leave",
  "question": "대표 질문",
  "paraphrases": ["유사 표현 1", "유사 표현 2", "..."],
  "answer": "미리 작성한 답변",
  "internal_policy": {"doc": "취업규칙 제n조", "text": "조항 원문"},
  "law": {"doc": "근로기준법 제n조", "text": "조항 원문"},
  "relation": "L1"
}
```

`relation`은 코드북 §4 기준: L1 법정의무, L2 법정기준 상회, L3 법정의무 없음(회사 자체 제도).
유사 표현을 5~10개씩 넣을수록 매칭 정확도가 올라갑니다.

## 유사도 기준치 조정

`matcher.py` 상단의 `THRESHOLD_EMBEDDING`(기본 0.55), `THRESHOLD_TFIDF`(기본 0.4)를
조정하세요. 높이면 오답이 줄고 미매칭이 늘어납니다.
