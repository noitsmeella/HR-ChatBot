# -*- coding: utf-8 -*-
"""법령 뉴스레터 결과를 챗봇 관리자 화면에 제공하는 읽기 전용 서비스.

- 법령 수집/비교/메일 발송 코드는 수정하지 않습니다.
- LAW_NEWSLETTER_PATH 환경변수로 외부 law_newsletter 폴더를 연결합니다.
- 연결되지 않으면 챗봇 내부 data/law_updates.json 예시 데이터를 사용합니다.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

CHATBOT_ROOT = Path(__file__).resolve().parents[1]
FALLBACK_PATH = CHATBOT_ROOT / "data" / "law_updates.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"JSON 최상위 형식이 객체가 아닙니다: {path}")
    return data


def _resolve_report_path() -> tuple[Path, str]:
    configured = os.getenv("LAW_NEWSLETTER_PATH", "").strip().strip('"')
    if configured:
        base = Path(configured).expanduser()
        report_path = base / "change_report.json"
        if report_path.exists():
            return report_path, "external"
        return report_path, "missing_external"
    return FALLBACK_PATH, "fallback"


def _fmt_timestamp(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "-"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text


def _article_label(article: dict[str, Any]) -> str:
    number = str(article.get("article_number") or article.get("article") or "조문 미상").strip()
    title = str(article.get("title") or "").strip()
    return f"{number}({title})" if title else number


def _normalize_change_report(raw: dict[str, Any], source_path: Path) -> dict[str, Any]:
    laws: list[dict[str, Any]] = []
    for law in raw.get("changed_laws", []) or []:
        analysis = law.get("analysis") if isinstance(law.get("analysis"), dict) else {}
        changes: list[dict[str, Any]] = []
        groups = (
            ("추가", law.get("added_articles", []) or []),
            ("삭제", law.get("removed_articles", []) or []),
            ("수정", law.get("modified_articles", []) or []),
        )
        for change_type, items in groups:
            for item in items:
                if not isinstance(item, dict):
                    continue
                changes.append({
                    "type": change_type,
                    "label": _article_label(item),
                    "effective_date": item.get("effective_date") or law.get("effective_date") or "-",
                    "before": item.get("previous_content") or "-",
                    "after": item.get("current_content") or "-",
                })

        laws.append({
            "law_name": law.get("law_name") or "법령명 미상",
            "effective_date": law.get("effective_date") or "-",
            "summary": analysis.get("summary") or "요약이 아직 생성되지 않았습니다.",
            "analysis_status": analysis.get("analysis_status") or "미생성",
            "analysis_notice": analysis.get("analysis_notice") or "",
            "hr_checkpoints": analysis.get("hr_checkpoints") or [],
            "changes": changes,
            "metadata_changes": law.get("metadata_changes") or {},
        })

    return {
        "mode": "change_report",
        "source_path": str(source_path),
        "generated_at": _fmt_timestamp(raw.get("generated_at")),
        "checked_law_count": int(raw.get("checked_law_count", 0) or 0),
        "changed_law_count": int(raw.get("changed_law_count", len(laws)) or 0),
        "total_change_count": int(raw.get("total_change_count", 0) or 0),
        "analysis_mode": raw.get("analysis_mode") or "-",
        "laws": laws,
        "skipped_laws": raw.get("skipped_laws") or [],
    }


def _normalize_fallback(raw: dict[str, Any], source_path: Path) -> dict[str, Any]:
    laws: list[dict[str, Any]] = []
    for item in raw.get("updates", []) or []:
        status = str(item.get("status", ""))
        laws.append({
            "law_name": item.get("law") or "법령명 미상",
            "effective_date": item.get("effective_date") or "-",
            "summary": item.get("change") or "-",
            "analysis_status": status or "예시 데이터",
            "analysis_notice": "챗봇 내부 예시 데이터입니다.",
            "hr_checkpoints": [item.get("action_needed")] if item.get("action_needed") not in (None, "", "-") else [],
            "changes": [],
            "metadata_changes": {},
            "affected_policies": item.get("affected_policies") or [],
        })
    return {
        "mode": "fallback",
        "source_path": str(source_path),
        "generated_at": str(raw.get("last_checked") or "-"),
        "checked_law_count": len(raw.get("tracked_laws", []) or []),
        "changed_law_count": sum(1 for x in raw.get("updates", []) or [] if x.get("status") == "검토 필요"),
        "total_change_count": len(laws),
        "analysis_mode": "내부 예시 데이터",
        "laws": laws,
        "skipped_laws": [],
    }


def load_legal_update_data() -> dict[str, Any]:
    path, source_mode = _resolve_report_path()
    if source_mode == "missing_external":
        return {
            "error": (
                "LAW_NEWSLETTER_PATH가 설정되어 있지만 change_report.json을 찾지 못했습니다. "
                f"확인 경로: {path}"
            ),
            "source_path": str(path),
            "laws": [],
        }
    try:
        raw = _load_json(path)
        if "changed_laws" in raw or "total_change_count" in raw:
            return _normalize_change_report(raw, path)
        return _normalize_fallback(raw, path)
    except FileNotFoundError:
        return {"error": f"법령 데이터 파일이 없습니다: {path}", "source_path": str(path), "laws": []}
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        return {"error": f"법령 데이터 파일을 읽지 못했습니다: {error}", "source_path": str(path), "laws": []}
