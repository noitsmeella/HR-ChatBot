# -*- coding: utf-8 -*-
"""
유사도 매칭 엔진 (retrieval-only) — v4.0
- 분류 체계: 중분류(major) → 소분류(sub) → FAQ(qa_items)
- 사용자 질문을 벡터화하여 미리 작성된 Q&A와 유사도 비교
- 답변을 생성하지 않고, 사람이 작성한 답변을 그대로 반환 → 생성형 모델의 환각(없는 내용 지어내기)이 구조적으로 생기지 않음
  (단, 데이터에 들어간 답변 자체의 오류나 접근 권한 관리는 별도로 점검해야 함)
- 임베딩 백엔드:
    1) sentence-transformers (jhgan/ko-sroberta-multitask) — 로컬 실행, 권장
    2) TF-IDF (문자 n-gram) — 라이브러리가 없을 때 폴백. 데모 용도로는 충분
"""
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
QA_PATH = os.path.join(DATA_DIR, "qa_data.json")

# 유사도 기준치: 이 값 미만이면 "답변 없음" 처리 → 담당자 전달
THRESHOLD_EMBEDDING = 0.55   # sentence-transformers 코사인 유사도 기준
THRESHOLD_TFIDF = 0.5        # TF-IDF는 임베딩보다 점수 분포가 낮음 (v4.0: FAQ 증가로 0.4→0.5 상향)

# 매칭에 정보가 없는 질문 관용구 — TF-IDF 오매칭 방지용으로 제거
_BOILERPLATE = [
    "어떻게 하나요", "어떻게 되나요", "어떻게 해요", "어떻게 하는지",
    "알려주세요", "알려줘", "궁금해요", "궁금합니다", "있나요", "인가요",
    "일까요", "될까요", "되나요", "하나요", "해요", "예요", "에요",
]


def normalize(text: str) -> str:
    text = text.strip().rstrip("?!.")
    for p in _BOILERPLATE:
        text = text.replace(p, " ")
    return re.sub(r"\s+", " ", text).strip()


class QAMatcher:
    def __init__(self, qa_path: str = QA_PATH):
        with open(qa_path, encoding="utf-8") as f:
            data = json.load(f)

        # 분류 체계: 중분류 → 소분류
        self.taxonomy = data["taxonomy"]                       # 순서 보존 리스트
        self.majors = {m["id"]: m for m in self.taxonomy}
        self.subs = {s["id"]: {**s, "major": m["id"]}
                     for m in self.taxonomy for s in m["subs"]}

        self.items = data["qa_items"]

        # (질문 텍스트, item 인덱스) — 대표 질문 + 유사 표현 전부를 검색 대상으로
        self.corpus = []
        self.corpus_item_idx = []
        for i, item in enumerate(self.items):
            for q in [item["question"]] + item.get("paraphrases", []):
                self.corpus.append(q)
                self.corpus_item_idx.append(i)

        self.backend = self._init_backend()

    def _init_backend(self) -> str:
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("jhgan/ko-sroberta-multitask")
            self.corpus_emb = self.model.encode(self.corpus, normalize_embeddings=True)
            return "embedding"
        except ImportError:
            from sklearn.feature_extraction.text import TfidfVectorizer
            # 한국어는 형태소 분석 없이도 문자 n-gram이 잘 동작함
            self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 3))
            self.corpus_vec = self.vectorizer.fit_transform(
                [normalize(q) for q in self.corpus])
            return "tfidf"

    def faq_items(self, sub: str) -> list[dict]:
        """소분류의 FAQ 목록 (클릭형 버튼용)"""
        return [i for i in self.items if i["sub"] == sub]

    def _scores(self, query: str):
        if self.backend == "embedding":
            q_emb = self.model.encode([query], normalize_embeddings=True)
            return (self.corpus_emb @ q_emb.T).ravel(), THRESHOLD_EMBEDDING
        from sklearn.metrics.pairwise import cosine_similarity
        q_vec = self.vectorizer.transform([normalize(query)])
        return cosine_similarity(self.corpus_vec, q_vec).ravel(), THRESHOLD_TFIDF

    def match(self, query: str, major: str | None = None,
              sub: str | None = None, top_k: int = 3):
        """
        Returns: {"matched": bool, "item": dict|None, "score": float, "candidates": [...]}
        sub을 주면 해당 소분류만, major만 주면 해당 중분류 전체에서 검색.
        """
        scores, threshold = self._scores(query)

        # 문항(item) 단위 최고 점수로 집계
        best_per_item: dict[int, float] = {}
        for idx, score in zip(self.corpus_item_idx, scores):
            item = self.items[idx]
            if sub and item["sub"] != sub:
                continue
            if major and item["major"] != major:
                continue
            best_per_item[idx] = max(best_per_item.get(idx, 0.0), float(score))

        ranked = sorted(best_per_item.items(), key=lambda x: -x[1])[:top_k]
        candidates = [
            {"item": self.items[i], "score": round(s, 3)} for i, s in ranked
        ]

        if ranked and ranked[0][1] >= threshold:
            return {"matched": True, "item": self.items[ranked[0][0]],
                    "score": round(ranked[0][1], 3), "candidates": candidates}
        return {"matched": False, "item": None,
                "score": round(ranked[0][1], 3) if ranked else 0.0,
                "candidates": candidates}

    def match_with_fallback(self, query: str, sub: str):
        """
        기타문의(문장형)용 2단계 매칭:
        1) 선택한 소분류 안에서 검색
        2) 실패 시 전체에서 검색 — 다른 소분류에서 찾으면 출처를 함께 반환
        Returns: (result, found_in_other_sub: dict|None)
        """
        result = self.match(query, sub=sub)
        if result["matched"]:
            return result, None
        g = self.match(query)
        if g["matched"] and g["item"]["sub"] != sub:
            return g, self.subs[g["item"]["sub"]]
        return result, None


def format_answer(item: dict) -> str:
    """답변 + 근거(사내규정/현행법규 매핑)를 함께 표시. L3은 회사 자체 제도임을 명시"""
    lines = [item["answer"], ""]
    lines.append(f"📘 사내규정: {item['internal_policy']['doc']}")
    if item.get("relation") == "L3":
        lines.append("⚖️ 관련법규: 법정 제도가 아닌 회사 자체 제도입니다.")
    else:
        lines.append(f"⚖️ 관련법규: {item.get('law', {}).get('doc', '매핑 예정')}")
    return "\n".join(lines)


if __name__ == "__main__":
    matcher = QAMatcher()
    print(f"[백엔드: {matcher.backend}]")
    print(f"중분류 {len(matcher.majors)} / 소분류 {len(matcher.subs)} / FAQ {len(matcher.items)}")

    tests = [
        ("연차휴가 알려줘", None, "statutory-annual"),
        ("육아휴직 신청하고 싶어요", None, "statutory-childcare"),
        ("정년퇴직 문의", "hire", None),
        ("주차장 등록은 어떻게 하나요?", None, None),  # 데이터에 없음 → 미매칭이어야 정상
    ]
    for q, major, sub in tests:
        r = matcher.match(q, major=major, sub=sub)
        print(f"\nQ: {q}  (범위: major={major}, sub={sub})")
        if r["matched"]:
            print(f"  → [{r['score']}] {r['item']['id']}: {r['item']['question']}")
        else:
            print(f"  → 미매칭 (최고점수 {r['score']}) → 담당자 전달")

    # 폴백 테스트: 소분류를 잘못 골라도 전체에서 찾아줌
    r, other = matcher.match_with_fallback("연차휴가 알려줘", "work-overtime")
    print(f"\n[폴백] 초과근무에서 연차 질문 → matched={r['matched']}, "
          f"다른 소분류={other['name'] if other else None}")
