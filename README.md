# HR 챗봇 프로토타입 v4.0

검색 전용(retrieval-only) 구조: 답변을 생성하지 않고 사람이 작성한 Q&A에서 찾아 반환합니다.
외부 API 호출 없음 → 개인정보/사내기밀 유출 위험 없음.

## v4.0 변경사항 — 문의 탐색 구조 개편

문의하기가 3단계 탐색으로 바뀌었습니다:

**중분류(3) → 소분류/제도명(18) → FAQ 질문 버튼(클릭형) + 기타문의(문장형)**

| 중분류 | 소분류 |
|---|---|
| 근무제도 (2) | 초과근무, 야간휴일근무 |
| 법정 휴가·휴직 (13) | 연차휴가, 공가, 출산전후휴가, 태아검진, 유·사산휴가, 난임치료휴가, 배우자출산휴가, 가족돌봄휴가, 육아휴직, 가족돌봄휴직, 공상휴직, 군복무휴직, 근로단축 |
| 채용·퇴직 (3) | 정년퇴직, 일반퇴직, 제증명 발급 안내 |

> 공개 저장소에는 법령 근거가 있는 법정 제도만 소분류로 포함했습니다 (회사 자체 제도는 제외).

- 소분류 진입 시 해당 제도의 FAQ가 버튼으로 표시되고, 클릭하면 답변이 바로 출력됩니다.
- 기타문의(문장형)는 선택한 소분류 안에서 우선 검색하고, 없으면 전체에서 폴백 검색합니다
  (다른 분류에서 찾으면 출처를 표시).
- 이 저장소의 FAQ는 소분류마다 **내용 없는 예시 항목 1건(총 18건)**뿐입니다.
  실제 FAQ 질문·답변과 근거 규정은 사내 데이터라 포함하지 않았습니다.
  분류·FAQ 수정은 `build_qa_data.py` 수정 후 `python build_qa_data.py` 실행
  (또는 `data/qa_data.json` 직접 수정).

## 법령 업데이트 탭 (담당자)

담당자 화면의 "법령 업데이트" 탭은 별도로 구현한 법령 뉴스레터(law_newsletter)가 만든
`change_report.json`을 읽기 전용으로 표시합니다 (점검 법령 수, 변경 조문, 변경 전후 비교, HR 체크포인트).

- `LAW_NEWSLETTER_PATH` 환경변수에 law_newsletter 폴더 경로를 지정하면 연결됩니다.
- 지정하지 않으면 챗봇 내부 예시 데이터(`data/law_updates.json`)로 표시됩니다.
- 화면 코드: `legal_updates_page.py`, 데이터 읽기: `services/legal_update_service.py`

## 실행 방법

```bash
pip install -r requirements.txt   # streamlit scikit-learn pandas openpyxl
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

## 관리자 대시보드 + 리포트 자동화

담당자 로그인 → "대시보드" 탭:

- ⚖️ 최신 법령 트래킹 — 추적 법령의 개정사항과 영향받는 사내규정 표시
- 📅 이달의 연차/휴가 신청자
- 🏥 휴직 현황 — 누가 언제부터 언제까지 어떤 휴직인지 (관련부서 공유용)
- 📊 올해 휴직자 비율, 성별×휴직종류 차트
- 📄 주간/월간 리포트 수동 생성 + 다운로드 버튼

### 자동화 (수작업 대체)

| 작업 | 명령 | 주기 |
|---|---|---|
| 주간 리포트 (휴직/휴가 현황 → 관련부서) | `python report.py weekly` | 매주 금요일 09:00 |
| 월간 통계 (휴직자 비율, 성별×휴직종류) | `python report.py monthly` | 매월 1일 09:00 |
| 법령 개정 점검 | `python law_tracker.py` | 매일 08:00 |

크론 등록 예 (`crontab -e`):

```
0 8 * * *  cd /path/to/hr-chatbot && python law_tracker.py
0 9 * * 5  cd /path/to/hr-chatbot && python report.py weekly
0 9 1 * *  cd /path/to/hr-chatbot && python report.py monthly
```

Windows는 작업 스케줄러에 동일 명령 등록. 리포트는 `reports/`에 xlsx로 생성되며,
`report.py`의 `send_email()`에 사내 SMTP를 설정하면 관련부서 자동 발송까지 됩니다.
법령 트래킹은 `LAW_OC_KEY` 환경변수(open.law.go.kr 무료 발급)를 설정하면
국가법령정보센터 Open API에서 실데이터를 수집합니다. 미설정 시 예시 데이터로 동작합니다.

## 파일 구조

- `data/qa_data.json` — 분류 체계(taxonomy) + FAQ 데이터 (질문 + 유사표현 + 답변 + 사내규정/법령 매핑 + 관계유형 L1~L3)
- `build_qa_data.py` — qa_data.json 생성 스크립트 (분류/FAQ 일괄 수정용)
- `data/employees.json` — 가상 직원 데이터 (성별 포함)
- `data/leave_requests.json` — 연차/휴가 신청 내역
- `data/loa_requests.json` — 휴직 신청 내역
- `data/law_updates.json` — 법령 트래킹 데이터 (law_tracker.py가 갱신)
- `data/unanswered.json` — 미답변 질문 로그 (자동 생성)
- `data/security_log.json` — 보안 차단 로그 (자동 생성)
- `matcher.py` — 유사도 매칭 엔진 (단독 테스트: `python matcher.py`)
- `test_security.py` — 보안 필터 테스트
- `report.py` — 주간/월간 리포트 생성 (+이메일 발송 스텁)
- `law_tracker.py` — 법령 개정 자동 점검
- `legal_updates_page.py`, `services/legal_update_service.py` — 법령 업데이트 탭 (law_newsletter 결과 연동)
- `requirements.txt` — 의존성 목록
- `app.py` — Streamlit 웹앱 (로그인 → 역할 분기 → 버튼/채팅/대시보드)
- `reports/` — 생성된 리포트 (xlsx)
- `코드북_초안.docx` — 데이터 구축 기준 문서

## Q&A 추가 방법

`qa_data.json`의 `qa_items`에 항목 추가 (`major`/`sub`는 taxonomy의 id):

```json
{
  "id": "statutory-annual-004",
  "major": "statutory",
  "sub": "statutory-annual",
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

`matcher.py` 상단의 `THRESHOLD_EMBEDDING`(기본 0.55), `THRESHOLD_TFIDF`(기본 0.5)를
조정하세요. 높이면 오답이 줄고 미매칭이 늘어납니다.
