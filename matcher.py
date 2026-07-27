# -*- coding: utf-8 -*-
"""
유사도 매칭 엔진 (retrieval-only)
- 사용자 질문을 벡터화하여 미리 작성된 Q&A와 유사도 비교
- 답변을 생성하지 않고, 사람이 작성한 답변을 그대로 반환 → 환각/유출 위험 없음
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
THRESHOLD_TFIDF = 0.4        # TF-IDF는 임베딩보다 점수 분포가 낮음

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
        self.categories = {c["id"]: c for c in data["categories"]}
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

    def match(self, query: str, category: str | None = None, top_k: int = 3):
        """
        Returns: {"matched": bool, "item": dict|None, "score": float, "candidates": [...]}
        category를 주면 해당 카테고리 문항만 검색 (카테고리 진입 후 질문하는 UX와 일치)
        """
        if self.backend == "embedding":
            q_emb = self.model.encode([query], normalize_embeddings=True)
            scores = (self.corpus_emb @ q_emb.T).ravel()
            threshold = THRESHOLD_EMBEDDING
        else:
            from sklearn.metrics.pairwise import cosine_similarity
            q_vec = self.vectorizer.transform([normalize(query)])
            scores = cosine_similarity(self.corpus_vec, q_vec).ravel()
            threshold = THRESHOLD_TFIDF

        # 문항(item) 단위 최고 점수로 집계
        best_per_item: dict[int, float] = {}
        for idx, score in zip(self.corpus_item_idx, scores):
            item = self.items[idx]
            if category and item["category"] != category:
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


def format_answer(item: dict) -> str:
    """답변 + 근거(사내규정/현행법규 매핑)를 함께 표시. L3은 회사 자체 제도임을 명시"""
    lines = [item["answer"], ""]
    lines.append(f"📘 사내규정: {item['internal_policy']['doc']}")
    if item.get("relation") == "L3":
        lines.append("⚖️ 관련법규: 법정 제도가 아닌 회사 자체 제도입니다.")
    else:
        lines.append(f"⚖️ 관련법규: {item['law']['doc']}")
    return "\n".join(lines)


if __name__ == "__main__":
    matcher = QAMatcher()
    print(f"[백엔드: {matcher.backend}]")
    tests = [
        "연차 몇 개 생겨요?",
        "부모님이 돌아가셨는데 회사에서 지원되는 게 있나요?",
        "야근하면 수당 얼마나 받아요?",
        "주차장 등록은 어떻게 하나요?",   # 데이터에 없는 질문 → 미매칭이어야 정상
    ]
    for q in tests:
        r = matcher.match(q)
        print(f"\nQ: {q}")
        if r["matched"]:
            print(f"  → [{r['score']}] {r['item']['id']}: {r['item']['question']}")
        else:
            print(f"  → 미매칭 (최고점수 {r['score']}) → 담당자 전달")
