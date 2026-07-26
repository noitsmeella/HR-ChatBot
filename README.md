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

## 파일 구조

- `data/qa_data.json` — Q&A 데이터 (질문 + 유사표현 + 답변 + 사내규정/법령 매핑). **여기에 데이터를 추가하는 게 곧 챗봇을 똑똑하게 만드는 일입니다.**
- `data/employees.json` — 가상 직원 데이터
- `data/unanswered.json` — 미답변 질문 로그 (자동 생성)
- `matcher.py` — 유사도 매칭 엔진 (단독 실행하면 테스트: `python matcher.py`)
- `app.py` — Streamlit 웹앱 (로그인 → 역할 분기 → 버튼/채팅)

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
  "law": {"doc": "근로기준법 제n조", "text": "조항 원문"}
}
```

유사 표현을 5~10개씩 넣을수록 매칭 정확도가 올라갑니다.

## 유사도 기준치 조정

`matcher.py` 상단의 `THRESHOLD_EMBEDDING`(기본 0.55), `THRESHOLD_TFIDF`(기본 0.25)를
조정하세요. 높이면 오답이 줄고 미매칭이 늘어납니다.
