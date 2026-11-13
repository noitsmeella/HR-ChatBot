# -*- coding: utf-8 -*-
"""
qa_data.json 생성 스크립트 (v4.0)
- 분류 체계: 중분류(major) → 소분류(sub, 제도명) → FAQ(qa_items)
- 공개 저장소용: FAQ는 소분류마다 내용 없는 예시 항목 1건만 생성한다.
  (시연 버전의 FAQ 질문·답변과 근거 규정은 포함하지 않음)
- 실제 FAQ를 넣으려면 아래 build_placeholder_items() 대신 qa_items를 직접 채우면 된다.
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "data", "qa_data.json")

# ---------------- 분류 체계 (중분류 → 소분류) ----------------
# 공개 저장소용: 시연 버전 분류 구조의 일부만 포함
TAXONOMY = [
    ("work", "근무제도", [
        ("overtime", "초과근무"), ("night", "야간휴일근무"),
    ]),
    ("statutory", "법정 휴가·휴직", [
        ("annual", "연차휴가"), ("official", "공가"),
        ("maternity", "출산전후휴가"), ("checkup", "태아검진"),
        ("miscarriage", "유·사산휴가"), ("infertility", "난임치료휴가"),
        ("spouse", "배우자출산휴가"), ("famcare-lv", "가족돌봄휴가"),
        ("childcare", "육아휴직"), ("famcare-loa", "가족돌봄휴직"),
        ("injury", "공상휴직"), ("military", "군복무휴직"),
        ("reduced", "근로단축"),
    ]),
    ("hire", "채용·퇴직", [
        ("retire-age", "정년퇴직"), ("retire", "일반퇴직"), ("certificate", "제증명 발급 안내"),
    ]),
]

items = []


def build_placeholder_items():
    """소분류마다 예시 FAQ 1건 생성 — 탐색 구조(중분류 → 소분류 → FAQ) 시연용.
    질문·답변에 실제 제도 내용은 들어 있지 않다."""
    for major, _mname, subs in TAXONOMY:
        for sub, sname in subs:
            items.append({
                "id": f"{major}-{sub}-001",
                "major": major,
                "sub": sub,
                "question": f"{sname} 안내 (예시 FAQ)",
                "paraphrases": [sname, f"{sname} 알려줘", f"{sname} 문의", f"{sname} 신청"],
                "answer": (f"[예시 데이터] '{sname}' 소분류의 FAQ 자리입니다.\n"
                           "실제 FAQ 질문·답변은 사내 데이터라 이 저장소에 포함하지 않았습니다. "
                           "운영 버전에서는 이 자리에 사내 제도 문서의 FAQ 답변과 근거 규정이 표시됩니다."),
                "internal_policy": {"doc": "비공개 (예시 데이터)", "text": ""},
                "law": {"doc": "비공개 (예시 데이터)", "text": ""},
                "relation": None,
            })


build_placeholder_items()

# ---------------- 저장 ----------------
taxonomy = [
    {"id": mid, "name": mname,
     "subs": [{"id": f"{mid}-{sid}", "name": sname} for sid, sname in subs]}
    for mid, mname, subs in taxonomy_src
] if (taxonomy_src := TAXONOMY) else []

# item의 sub id를 전체 id(major-sub)로 통일
for it in items:
    it["sub"] = f"{it['major']}-{it['sub']}"

data = {"version": "4.0", "taxonomy": taxonomy, "qa_items": items}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

n_subs = sum(len(m["subs"]) for m in taxonomy)
print(f"저장 완료: {OUT}")
print(f"중분류 {len(taxonomy)}개 / 소분류 {n_subs}개 / FAQ {len(items)}건")
