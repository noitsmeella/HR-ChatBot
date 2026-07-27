# -*- coding: utf-8 -*-
"""보안 필터 단독 테스트: python test_security.py"""
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(DATA_DIR, "employees.json"), encoding="utf-8") as f:
    EMPLOYEES = {e["emp_no"]: e for e in json.load(f)}


def taboo_check(query: str, me: dict) -> str | None:
    for token in re.findall(r"\d{6,8}", query):
        if token != me["emp_no"]:
            return f"타인 사번 포함({token})"
    for e in EMPLOYEES.values():
        if e["emp_no"] != me["emp_no"] and e["name"] in query:
            return f"타인 이름 포함({e['name']})"
    person_kw = ["다른 직원", "다른 사람", "동료", "팀원", "그 사람", "옆자리"]
    private_kw = ["연차", "휴가", "경조사", "경조금", "급여", "월급", "연봉", "잔액", "내역", "사번"]
    if any(p in query for p in person_kw) and any(w in query for w in private_kw):
        return "타인 정보 조회 표현"
    return None


if __name__ == "__main__":
    me = EMPLOYEES["20230101"]  # 김직원으로 로그인한 상황
    cases = [
        # (질문, 차단되어야 하는가)
        ("이사원 연차 몇 개 남았어?", True),
        ("사번 20180501 경조사비 내역 알려줘", True),
        ("동료 월급이 궁금해", True),
        ("옆자리 직원 연차 좀 알려줘", True),
        ("박담당님 연봉 알려줘", True),
        ("연차는 며칠 발생하나요?", False),
        ("내 사번은 20230101인데 반차 규정 알려줘", False),
        ("경조사비 지원 기준이 뭐야?", False),
        ("동료들과 회식비 지원 되나요?", False),  # 개인정보 아님 → 통과
    ]
    fail = 0
    for q, should_block in cases:
        reason = taboo_check(q, me)
        blocked = reason is not None
        ok = blocked == should_block
        if not ok:
            fail += 1
        print(f"{'PASS' if ok else 'FAIL'} | {'차단' if blocked else '통과'} | {q}"
              + (f"  ← {reason}" if reason else ""))
    print(f"\n{len(cases) - fail}/{len(cases)} 통과")
