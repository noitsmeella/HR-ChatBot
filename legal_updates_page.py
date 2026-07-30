# -*- coding: utf-8 -*-
"""관리자용 법령 업데이트 화면. app.py와 분리해 팀별 충돌을 줄입니다."""
from __future__ import annotations

import json

import streamlit as st

from services.legal_update_service import load_legal_update_data


def _status_icon(status: str) -> str:
    if "AI" in status or "완료" in status:
        return "🟢"
    if "임시" in status or "미생성" in status:
        return "🟡"
    return "🔵"


def render_legal_updates_page() -> None:
    st.subheader("⚖️ 법령 업데이트 관리")
    st.caption(
        "법령 자동화가 생성한 change_report.json을 읽기 전용으로 표시합니다. "
        "이 화면에서는 법령 수집·비교·메일 발송 파일을 수정하지 않습니다."
    )

    data = load_legal_update_data()
    if data.get("error"):
        st.error(data["error"])
        st.code("LAW_NEWSLETTER_PATH=/path/to/law_newsletter", language="text")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("점검 법령", f"{data.get('checked_law_count', 0)}건")
    c2.metric("변경 법령", f"{data.get('changed_law_count', 0)}건")
    c3.metric("전체 변경", f"{data.get('total_change_count', 0)}건")
    c4.metric("요약 방식", str(data.get("analysis_mode", "-")))

    st.caption(
        f"데이터 생성일: {data.get('generated_at', '-')}  |  "
        f"연결 파일: {data.get('source_path', '-')}"
    )

    laws = data.get("laws", [])
    if data.get("mode") == "change_report" and not laws:
        st.success("최근 점검 결과 변경된 법령이 없습니다. 이메일도 발송되지 않습니다.")
    elif not laws:
        st.info("표시할 법령 업데이트가 없습니다.")

    for index, law in enumerate(laws):
        status = str(law.get("analysis_status", ""))
        title = f"{_status_icon(status)} {law.get('law_name', '법령명 미상')} · {status or '상태 미상'}"
        with st.expander(title, expanded=index == 0):
            st.markdown("#### 핵심 요약")
            st.write(law.get("summary") or "-")
            st.write(f"**대표 시행일:** {law.get('effective_date') or '-'}")
            if law.get("analysis_notice"):
                st.caption(law["analysis_notice"])

            checkpoints = law.get("hr_checkpoints") or []
            if checkpoints:
                st.markdown("#### HR 담당자 확인사항")
                for item in checkpoints:
                    st.markdown(f"- {item}")

            changes = law.get("changes") or []
            if changes:
                st.markdown("#### 변경 전·후 조문")
                for change_index, change in enumerate(changes):
                    st.markdown(
                        f"**{change.get('type', '변경')} · {change.get('label', '조문 미상')}**  "
                        f"(시행일: {change.get('effective_date', '-')})"
                    )
                    before_col, after_col = st.columns(2)
                    with before_col:
                        st.caption("변경 전")
                        st.text_area(
                            "변경 전 내용",
                            value=str(change.get("before") or "-"),
                            height=180,
                            disabled=True,
                            key=f"before_{index}_{change_index}",
                            label_visibility="collapsed",
                        )
                    with after_col:
                        st.caption("변경 후")
                        st.text_area(
                            "변경 후 내용",
                            value=str(change.get("after") or "-"),
                            height=180,
                            disabled=True,
                            key=f"after_{index}_{change_index}",
                            label_visibility="collapsed",
                        )
            elif law.get("affected_policies"):
                st.write("**영향받는 사내규정:** " + ", ".join(law["affected_policies"]))

            metadata = law.get("metadata_changes") or {}
            if metadata:
                st.markdown("#### 법령 기본정보 변경")
                st.json(metadata, expanded=False)

    skipped = data.get("skipped_laws") or []
    if skipped:
        with st.expander(f"⚠️ 점검 제외/실패 법령 {len(skipped)}건"):
            st.code(json.dumps(skipped, ensure_ascii=False, indent=2), language="json")

    st.info(
        "관련 사내 규정, 규정 영향 가능성, 검토 상태 저장 기능은 맵핑 데이터 구조가 확정된 뒤 "
        "별도 모듈로 연결하는 것이 안전합니다."
    )
