# data/ — 가상 데이터 안내 / About this data

**이 폴더의 데이터는 모두 데모용으로 만든 가상 데이터입니다.**
사내 데이터를 받기 전 기능을 구현하기 위해 임의로 설정한 값이며, 실제 회사·직원·제도와 관련이 없습니다.

| 파일 | 내용 |
|---|---|
| `employees.json` | 가상 직원 10명(이름·사번·부서·연차·경조금 이력). 경조금 종류와 금액은 임의로 설정한 가상 복지제도 |
| `leave_requests.json` | 가상 연차·휴가 신청 내역 |
| `loa_requests.json` | 가상 휴직 신청 내역 |
| `qa_data.json` | 분류 체계와 소분류별 예시 FAQ(내용 없음). `build_qa_data.py`로 생성 |
| `law_updates.json` | 법령 개정 점검 예시. 사내규정 번호(예: 취업규칙-36)도 가상 식별자 |

실행 중 생성되는 `unanswered.json`(미답변 질문), `security_log.json`(차단 기록)과 `reports/`의 리포트에는 질문 원문·사번·이름이 들어갈 수 있으므로 `.gitignore`로 커밋에서 제외합니다.

---

**All data in this folder is fictional, created for the demo.**
The values were set arbitrarily so the features could be built before any company data was available, and they do not relate to any real company, employee or policy.
Files generated at runtime (`unanswered.json`, `security_log.json`, `reports/`) may contain question text, employee numbers and names, so they are excluded via `.gitignore`.
