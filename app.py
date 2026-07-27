# -*- coding: utf-8 -*-
"""
HR 챗봇 데모 앱 (Streamlit)
실행: streamlit run app.py
테스트 계정: 직원 20230101/1234, 담당자 20100301/admin

[보안 설계 — 타인 정보 조회 원천 차단]
원칙 1 (구조적 차단): 개인정보는 챗봇 지식(qa_data.json)에 존재하지 않는다.
  챗봇은 규정·법령만 답하므로 어떤 질문이 와도 타인 정보가 출력될 수 없다.
원칙 2 (세션 기반 조회): 개인정보 조회(연차·경조사비)는 로그인 세션의 emp_no로만
  수행한다. 조회 대상 사번을 클라이언트 입력으로 절대 받지 않는다.
원칙 3 (질문 필터): 타인 사번·이름이 포함된 질문은 매칭 전에 차단한다.
원칙 4 (감사 로그): 차단된 시도는 보안 로그에 기록되어 담당자가 확인한다.
"""
import json
import os
import re
from datetime import date, datetime

import streamlit as st

from matcher import QAMatcher, format_answer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EMP_PATH = os.path.join(DATA_DIR, "employees.json")
UNANSWERED_PATH = os.path.join(DATA_DIR, "unanswered.json")
SECURITY_LOG_PATH = os.path.join(DATA_DIR, "security_log.json")

st.set_page_config(page_title="HR 챗봇", page_icon="💬", layout="centered")


# ---------- 데이터 ----------
@st.cache_resource
def get_matcher():
    return QAMatcher()


@st.cache_data
def load_employees():
    with open(EMP_PATH, encoding="utf-8") as f:
        return {e["emp_no"]: e for e in json.load(f)}


def _append_json(path: str, record: dict):
    logs = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            logs = json.load(f)
    logs.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def load_json(path: str):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_unanswered(question: str, emp_no: str, category: str):
    _append_json(UNANSWERED_PATH, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "emp_no": emp_no, "category": category,
        "question": question, "status": "대기",
    })


# ---------- 보안 ----------
def taboo_check(query: str, me: dict) -> str | None:
    """타인 정보 질의 시도 감지. 문제 없으면 None, 있으면 차단 사유 반환"""
    employees = load_employees()
    # 1) 본인이 아닌 사번 패턴
    for token in re.findall(r"\d{6,8}", query):
        if token != me["emp_no"]:
            return f"타인 사번 포함({token})"
    # 2) 본인이 아닌 재직자 이름
    for e in employees.values():
        if e["emp_no"] != me["emp_no"] and e["name"] in query:
            return f"타인 이름 포함({e['name']})"
    # 3) 명시적 타인 조회 표현 + 개인정보 키워드 조합
    person_kw = ["다른 직원", "다른 사람", "동료", "팀원", "그 사람", "옆자리"]
    private_kw = ["연차", "휴가", "경조사", "경조금", "급여", "월급", "연봉", "잔액", "내역", "사번"]
    if any(p in query for p in person_kw) and any(w in query for w in private_kw):
        return "타인 정보 조회 표현"
    return None


def log_security(query: str, emp_no: str, reason: str):
    _append_json(SECURITY_LOG_PATH, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "emp_no": emp_no, "reason": reason, "query": query,
    })


BLOCKED_MSG = ("🚫 본인 외 다른 직원의 정보는 조회할 수 없습니다.\n\n"
               "개인정보 조회는 로그인한 본인 정보만 가능하며, 이 요청은 보안 로그에 기록되었습니다.")


# ---------- 버튼형 기능 (LLM 미경유, 세션 사용자 데이터만 조회) ----------
def calc_annual_leave(emp: dict) -> str:
    remaining = emp["annual_leave_total"] - emp["annual_leave_used"]
    years = (date.today() - date.fromisoformat(emp["hire_date"])).days // 365
    return (f"**{emp['name']}님의 연차 현황**\n\n"
            f"- 근속연수: {years}년 (입사일 {emp['hire_date']})\n"
            f"- 올해 발생 연차: {emp['annual_leave_total']}일\n"
            f"- 사용: {emp['annual_leave_used']}일\n"
            f"- **잔여: {remaining}일**")


def welfare_balance(emp: dict) -> str:
    lines = [f"**{emp['name']}님의 경조사비 수령 내역**\n"]
    if not emp["welfare_history"]:
        lines.append("- 수령 내역이 없습니다.")
    for h in emp["welfare_history"]:
        lines.append(f"- {h['date']} | {h['type']} | {h['amount']:,}원")
    total = sum(h["amount"] for h in emp["welfare_history"])
    lines.append(f"\n**누적 수령액: {total:,}원**")
    return "\n".join(lines)


# ---------- 로그인 ----------
def login_page():
    st.title("💬 HR 챗봇")
    st.caption("사내번호로 로그인하세요")
    with st.form("login"):
        emp_no = st.text_input("사내번호")
        pw = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인", use_container_width=True):
            emp = load_employees().get(emp_no)
            if emp and emp["password"] == pw:
                st.session_state.user = emp
                st.rerun()
            else:
                st.error("사내번호 또는 비밀번호가 올바르지 않습니다.")


# ---------- 직원 화면 ----------
def employee_page(emp: dict):
    matcher = get_matcher()
    st.title("💬 HR 챗봇")
    st.caption(f"{emp['department']} {emp['name']}님, 무엇을 도와드릴까요?")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "category" not in st.session_state:
        st.session_state.category = None

    # 1단계: 카테고리 버튼 (세션 사용자 본인 데이터만 조회 — 원칙 2)
    st.subheader("바로 확인하기")
    c1, c2 = st.columns(2)
    if c1.button("📅 내 연차 조회/계산", use_container_width=True):
        st.session_state.messages.append(("bot", calc_annual_leave(emp)))
    if c2.button("💐 경조사비 내역 조회", use_container_width=True):
        st.session_state.messages.append(("bot", welfare_balance(emp)))

    # 2단계: 문의 카테고리 선택 → 선택해야 채팅 입력창 활성화
    st.subheader("문의하기")
    cats = list(matcher.categories.values())
    cols = st.columns(len(cats))
    for col, cat in zip(cols, cats):
        selected = st.session_state.category == cat["id"]
        if col.button(("✅ " if selected else "") + cat["name"],
                      key=f"cat_{cat['id']}", use_container_width=True):
            st.session_state.category = cat["id"]
            st.rerun()

    # 대화 표시
    for role, msg in st.session_state.messages:
        with st.chat_message("assistant" if role == "bot" else "user"):
            st.markdown(msg)

    # 채팅 입력: 카테고리 선택 후에만 노출
    if st.session_state.category:
        cat_name = matcher.categories[st.session_state.category]["name"]
        query = st.chat_input(f"[{cat_name}] 질문을 입력하세요")
        if query:
            st.session_state.messages.append(("user", query))
            # 보안 필터 (원칙 3, 4): 매칭 전에 검사
            reason = taboo_check(query, emp)
            if reason:
                log_security(query, emp["emp_no"], reason)
                st.session_state.messages.append(("bot", BLOCKED_MSG))
            else:
                result = matcher.match(query, category=st.session_state.category)
                if result["matched"]:
                    st.session_state.messages.append(("bot", format_answer(result["item"])))
                else:
                    save_unanswered(query, emp["emp_no"], cat_name)
                    st.session_state.messages.append(
                        ("bot", "죄송합니다. 등록된 답변을 찾지 못했습니다.\n\n"
                                "질문을 인사팀 담당자에게 전달했습니다. 답변이 등록되면 안내드리겠습니다."))
            st.rerun()
    else:
        st.info("문장형 질문은 위에서 문의 카테고리를 먼저 선택해 주세요.")


# ---------- 대시보드 ----------
def dashboard_tab():
    import pandas as pd
    from report import get_frames, monthly_report, weekly_report

    emps, loa, lv = get_frames()
    today = date.today()
    this_month = today.strftime("%Y-%m")

    # 최신 법령 트래킹
    st.subheader("⚖️ 최신 법령 트래킹")
    law_data = load_json_obj(os.path.join(DATA_DIR, "law_updates.json"))
    st.caption(f"최근 점검일: {law_data.get('last_checked', '-')} | "
               f"추적 법령: {len(law_data.get('tracked_laws', []))}건 "
               "(law_tracker.py가 매일 자동 갱신)")
    for u in law_data.get("updates", []):
        icon = "🔴" if u["status"] == "검토 필요" else "🟢"
        with st.expander(f"{icon} {u['law']} {u['article']} — {u['status']}"):
            st.write(f"변경 내용: {u['change']}")
            st.write(f"시행일: {u['effective_date']}")
            if u["affected_policies"]:
                st.write(f"영향받는 사내규정: {', '.join(u['affected_policies'])}")
                st.write(f"조치 필요: {u['action_needed']}")

    # 이달의 연차/휴가 신청자
    st.subheader(f"📅 이달의 연차/휴가 신청 ({this_month})")
    lv_month = lv[lv["applied"].str.startswith(this_month)]
    if len(lv_month):
        st.dataframe(
            lv_month[["이름", "부서", "type", "start", "end", "days", "status"]].rename(
                columns={"type": "종류", "start": "시작일", "end": "종료일",
                         "days": "일수", "status": "결재상태"}),
            use_container_width=True, hide_index=True)
    else:
        st.info("이번 달 신청 내역이 없습니다.")

    # 휴직 현황
    st.subheader("🏥 휴직 현황")
    loa_view = loa.copy()
    loa_view["구분"] = loa_view.apply(
        lambda r: "휴직 중" if r["start"] <= str(today) <= r["end"] and r["status"] == "승인"
        else ("복직 완료" if r["end"] < str(today)
              else ("휴직 예정" if r["status"] == "승인" else r["status"])), axis=1)
    st.dataframe(
        loa_view[["이름", "부서", "성별", "loa_type", "start", "end", "구분"]].rename(
            columns={"loa_type": "휴직 종류", "start": "시작일", "end": "종료일"}),
        use_container_width=True, hide_index=True)

    # 통계
    st.subheader(f"📊 {today.year}년 휴직 통계")
    loa_year = loa[(loa["status"] == "승인") &
                   (loa["start"] <= f"{today.year}-12-31") &
                   (loa["end"] >= f"{today.year}-01-01")]
    n_loa = loa_year["emp_no"].nunique()
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 재직 인원", f"{len(emps)}명")
    c2.metric("올해 휴직자", f"{n_loa}명")
    c3.metric("휴직자 비율", f"{n_loa / len(emps) * 100:.1f}%")
    if len(loa_year):
        cross = loa_year.groupby(["성별", "loa_type"]).size().unstack(fill_value=0)
        st.caption("성별 × 휴직 종류 (건수)")
        st.bar_chart(cross)

    # 리포트 다운로드 (수작업 대체)
    st.subheader("📄 리포트 생성")
    st.caption("매주 금요일/매월 1일 자동 생성됩니다(report.py + 스케줄러). 수동 생성:")
    c1, c2 = st.columns(2)
    if c1.button("주간 리포트 생성 (휴직/휴가 현황)", use_container_width=True):
        path = weekly_report()
        with open(path, "rb") as f:
            st.download_button("⬇️ " + os.path.basename(path), f, file_name=os.path.basename(path))
    if c2.button("월간 통계 리포트 생성", use_container_width=True):
        path = monthly_report()
        with open(path, "rb") as f:
            st.download_button("⬇️ " + os.path.basename(path), f, file_name=os.path.basename(path))


def load_json_obj(path: str):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ---------- 담당자 화면 ----------
def admin_page(emp: dict):
    matcher = get_matcher()
    st.title("🛠 HR 챗봇 관리자")
    st.caption(f"인사팀 {emp['name']}님")

    tab0, tab1, tab2, tab3 = st.tabs(["대시보드", "미답변 질문", "보안 로그", "Q&A 데이터 현황"])

    with tab0:
        dashboard_tab()

    with tab1:
        logs = load_json(UNANSWERED_PATH)
        if not logs:
            st.info("미답변 질문이 없습니다.")
        for log in reversed(logs):
            st.markdown(
                f"- **{log['question']}**  \n"
                f"  {log['time']} | 사번 {log['emp_no']} | {log['category']} | {log['status']}")
        st.caption("→ 실제 서비스에서는 여기서 답변을 작성해 Q&A로 등록하는 기능을 붙입니다.")

    with tab2:
        logs = load_json(SECURITY_LOG_PATH)
        if not logs:
            st.info("차단된 요청이 없습니다.")
        for log in reversed(logs):
            st.markdown(
                f"- 🚫 **{log['reason']}**  \n"
                f"  {log['time']} | 요청자 사번 {log['emp_no']} | 질문: {log['query']}")

    with tab3:
        st.metric("등록된 Q&A 수", len(matcher.items))
        st.metric("검색 대상 문장 수 (유사표현 포함)", len(matcher.corpus))
        st.metric("매칭 백엔드", matcher.backend)
        for cat in matcher.categories.values():
            n = sum(1 for i in matcher.items if i["category"] == cat["id"])
            st.write(f"- {cat['name']}: {n}건")

    if st.button("직원 화면으로 보기"):
        st.session_state.view_as_employee = True
        st.rerun()


# ---------- 라우팅 ----------
if "user" not in st.session_state:
    login_page()
else:
    user = st.session_state.user
    with st.sidebar:
        st.write(f"**{user['name']}** ({'담당자' if user['role'] == 'admin' else '직원'})")
        if st.button("로그아웃"):
            st.session_state.clear()
            st.rerun()

    if user["role"] == "admin" and not st.session_state.get("view_as_employee"):
        admin_page(user)
    else:
        employee_page(user)
