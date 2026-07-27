# -*- coding: utf-8 -*-
"""
주간/월간 HR 리포트 자동 생성
사용법:
    python report.py weekly    # 주간 리포트 (매주 금요일 자동 실행 대상)
    python report.py monthly   # 월간 통계 리포트 (매월 1일 자동 실행 대상)
출력: reports/ 폴더에 xlsx 생성

[자동화 등록]
Linux/Mac (crontab -e):
    0 9 * * 5  cd /path/to/hr-chatbot && python report.py weekly
    0 9 1 * *  cd /path/to/hr-chatbot && python report.py monthly
Windows (작업 스케줄러):
    트리거 '매주 금요일 09:00' / '매월 1일 09:00' → 동작 python report.py weekly|monthly
이메일 발송까지 자동화하려면 아래 send_email() 의 SMTP 설정을 채우면 됩니다.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
REPORT_DIR = os.path.join(BASE, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def get_frames():
    emps = pd.DataFrame(load("employees.json"))
    emp_map = emps.set_index("emp_no")
    loa = pd.DataFrame(load("loa_requests.json"))
    lv = pd.DataFrame(load("leave_requests.json"))
    for df in (loa, lv):
        df["이름"] = df["emp_no"].map(emp_map["name"])
        df["부서"] = df["emp_no"].map(emp_map["department"])
        df["성별"] = df["emp_no"].map(emp_map["gender"])
    return emps, loa, lv


def autofit(ws):
    for col in ws.columns:
        width = max(len(str(c.value)) if c.value else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(width * 1.8 + 2, 40)


def style_header(ws):
    from openpyxl.styles import Font, PatternFill
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E79")


def write_sheets(path, sheets: dict):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            style_header(ws)
            autofit(ws)


# ---------- 주간 리포트 (매주 금요일) ----------
def weekly_report(today: date | None = None) -> str:
    today = today or date.today()
    week_start = today - timedelta(days=today.weekday())  # 월요일
    week_end = week_start + timedelta(days=6)
    _, loa, lv = get_frames()

    # 1) 휴직 현황: 현재 휴직 중 + 예정 + 검토중 — 관련부서 공유용
    loa_view = loa.copy()
    loa_view["구분"] = loa_view.apply(
        lambda r: "휴직 중" if r["start"] <= str(today) <= r["end"] and r["status"] == "승인"
        else ("복직 완료" if r["end"] < str(today)
              else ("휴직 예정" if r["status"] == "승인" else r["status"])), axis=1)
    loa_out = loa_view[["이름", "부서", "loa_type", "start", "end", "status", "구분", "note"]].rename(
        columns={"loa_type": "휴직 종류", "start": "시작일", "end": "종료일", "status": "결재상태", "note": "비고"})

    # 2) 이번 주 연차/휴가 신청
    lv_week = lv[(lv["applied"] >= str(week_start)) & (lv["applied"] <= str(week_end))]
    lv_out = lv_week[["이름", "부서", "type", "start", "end", "days", "status"]].rename(
        columns={"type": "종류", "start": "시작일", "end": "종료일", "days": "일수", "status": "결재상태"})

    # 3) 이번 주 실제 휴가 사용자 (부서 인력 운영 참고용)
    lv_using = lv[(lv["start"] <= str(week_end)) & (lv["end"] >= str(week_start)) & (lv["status"] == "승인")]
    lv_using_out = lv_using[["이름", "부서", "type", "start", "end", "days"]].rename(
        columns={"type": "종류", "start": "시작일", "end": "종료일", "days": "일수"})

    path = os.path.join(REPORT_DIR, f"주간리포트_{today.isoformat()}.xlsx")
    write_sheets(path, {
        "휴직 현황(관련부서 공유)": loa_out,
        "금주 연차휴가 신청": lv_out,
        "금주 휴가 사용자": lv_using_out,
    })
    return path


# ---------- 월간 리포트 (매월 1일) ----------
def monthly_report(today: date | None = None) -> str:
    today = today or date.today()
    year = str(today.year)
    emps, loa, _ = get_frames()

    # 올해 휴직자 (기간이 올해와 겹치는 승인 건)
    loa_year = loa[(loa["status"] == "승인") &
                   (loa["start"] <= f"{year}-12-31") & (loa["end"] >= f"{year}-01-01")]
    n_emp = len(emps)
    n_loa_emp = loa_year["emp_no"].nunique()

    summary = pd.DataFrame([
        {"항목": "전체 재직 인원", "값": n_emp},
        {"항목": f"{year}년 휴직자 수(승인 기준)", "값": n_loa_emp},
        {"항목": f"{year}년 휴직자 비율", "값": f"{n_loa_emp / n_emp * 100:.1f}%"},
        {"항목": "기준일", "값": today.isoformat()},
    ])

    # 성별 × 휴직종류 (건수 + 성별 내 비율)
    if len(loa_year):
        cross = loa_year.groupby(["성별", "loa_type"]).size().reset_index(name="건수")
        cross["성별 내 비율"] = cross.apply(
            lambda r: f"{r['건수'] / cross[cross['성별'] == r['성별']]['건수'].sum() * 100:.1f}%", axis=1)
        cross = cross.rename(columns={"loa_type": "휴직 종류"})
    else:
        cross = pd.DataFrame(columns=["성별", "휴직 종류", "건수", "성별 내 비율"])

    detail = loa_year[["이름", "부서", "성별", "loa_type", "start", "end"]].rename(
        columns={"loa_type": "휴직 종류", "start": "시작일", "end": "종료일"})

    path = os.path.join(REPORT_DIR, f"월간휴직통계_{year}-{today.month:02d}.xlsx")
    write_sheets(path, {"요약": summary, "성별x휴직종류": cross, "휴직자 명단": detail})
    return path


# ---------- 이메일 발송 (선택) ----------
def send_email(attachment: str, to: list[str]):
    """SMTP 설정을 채우면 리포트 생성 후 자동 발송됩니다."""
    import smtplib
    from email.message import EmailMessage
    SMTP_HOST, SMTP_PORT = "smtp.company.co.kr", 587   # ← 사내 SMTP로 변경
    SMTP_USER, SMTP_PASS = "hr-bot@company.co.kr", "비밀번호"
    msg = EmailMessage()
    msg["Subject"] = f"[HR] {os.path.basename(attachment)}"
    msg["From"], msg["To"] = SMTP_USER, ", ".join(to)
    msg.set_content("자동 생성된 HR 리포트를 첨부합니다.")
    with open(attachment, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="xlsx",
                           filename=os.path.basename(attachment))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    path = weekly_report() if mode == "weekly" else monthly_report()
    print(f"리포트 생성 완료: {path}")
    # 자동 발송하려면 주석 해제 후 SMTP 설정:
    # send_email(path, to=["dept-lead@company.co.kr"])
