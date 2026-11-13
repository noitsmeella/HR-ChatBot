[한국어](README.md) | **English**

# HR Chatbot Prototype

A **retrieval-only HR chatbot** that answers employee questions about internal HR policies.
It never generates answers. Instead, it finds the closest match among human-written, reviewed Q&A items and returns it together with the supporting policy and legal references.
Query matching runs locally, and no employee data or question text is sent to external services.
The only outbound connections are the one-time embedding model download and the optional law-amendment check (Korean National Law Information Center Open API).

> **Project background**
> This project was built in a university students' extracurricular program, on the theme of a company's HR operations. It is not a chatbot that the company runs or uses, although the company may adopt the ideas in the future.

> **About what is published here**
> This repository contains **v1.0 – v4.0** only (v4.0 includes the law-newsletter integration). All employee, leave and leave-of-absence data and benefit programs in these versions are **fictional**, set arbitrarily before any company data was available ([data/README.md](data/README.md)). In v4.0, only part of the category tree is kept, and every FAQ is replaced with a placeholder that has no real content.
> From v5.0 onward, the chatbot uses internal company documents provided through the program as its knowledge source. Because they may not be distributed externally, that code and data are not published.
> The techniques, design and evaluation metrics are described instead under [Later versions](#later-versions-private).

## Version history

| Version | Date | Highlights |
|---|---|---|
| v1.0 | 2026-07-26 | Core retrieval chatbot: login → role-based views (employee / HR admin), 4 categories, embedding / TF-IDF similarity matching, unanswered-question log |
| v2.0 | 2026-07-27 | 4-layer protection against viewing other employees' data + 9 security tests, policy-to-law relation types (L1–L3), data-building codebook |
| v3.0 | 2026-07-27 | HR admin dashboard (leave status, leave type × gender stats), automated weekly / monthly reports, law-amendment tracking |
| v4.0 | 2026-07-30 | Redesigned navigation (major category → subcategory → clickable FAQ + free-text question), law-newsletter results in the admin view |
| v5.0 | 2026-08-03 | *(private)* Real internal data: document-driven data pipeline |
| v6.0 | 2026-08-07 | *(private)* Access control, privacy handling, persistent review data, embedding as default backend, chat UI |
| v7.0 | 2026-08-08 | *(private)* Two-tier responses + gap gate, unanswered-question loop, evaluation redesign |
| v7.5 | 2026-08-10 | *(private)* Independent re-measurement of v7.0 and limitations |
| final | 2026-08-13 | *(private)* Entry FAQs, typed evaluation set (pilot), root-cause tool for held-back items |

Each public version (v1.0–v4.0) is a separate commit (`git log`).

### v1.0 — Core structure
- Streamlit web app; employee-number login, then separate employee and HR-admin views
- 4 categories (annual leave, benefits / family events, pay / allowances, other) with 8 fictional Q&A items
- Uses the Korean sentence-embedding model `jhgan/ko-sroberta-multitask` when installed, otherwise falls back to TF-IDF
- Below the similarity threshold, the bot does not answer; the question is logged and routed to HR

### v2.0 — Security and data standards
- 4-layer protection against looking up other employees' data (structural isolation / session-based lookup / query filter / audit log)
- Relation coding between internal policy and current law: L1 legal obligation, L2 exceeds the legal minimum, L3 company-only program
- L3 answers state explicitly that the program is a company policy, not a statutory one
- Data-building codebook (`코드북_초안.docx`, Korean) and its generator script (`make_codebook.js`)
- TF-IDF threshold raised from 0.25 to 0.4 to cut wrong answers

### v3.0 — Automating HR admin work
- Dashboard: this month's leave requests, current leaves of absence, share of employees on leave this year, leave type × gender chart
- `report.py`: weekly leave status and monthly leave statistics exported as xlsx (email sending stub included)
- `law_tracker.py`: checks for law amendments via the Korean National Law Information Center Open API (falls back to sample data without an API key)

### v4.0 — Navigation redesign + law newsletter
- Replaced the 4 flat categories with a 3-step tree: major category → subcategory (policy name) → FAQ
- The public repository keeps only part of the category tree (3 major categories, 18 subcategories). The demo version had the full tree, including company-specific programs
- Each subcategory has a single placeholder FAQ (no real FAQ content)
- Entering a subcategory shows its FAQs as buttons. Free-text questions are searched within the selected subcategory first, then across all subcategories as a fallback (showing where the match came from)
- Categories and FAQs are defined in one place (`build_qa_data.py`), which generates `qa_data.json`
- TF-IDF threshold raised from 0.4 to 0.5 as the number of FAQs grew
- **Law updates tab**: shows, read-only, the `change_report.json` produced by a separately built law newsletter (law_newsletter) in the admin view: laws checked, changed articles with before/after text, and HR checkpoints. Without `LAW_NEWSLETTER_PATH`, built-in sample data is shown

## Later versions (private)

From v5.0 onward the project uses the company's internal documents, so the code and data are not published. This section describes the techniques and design, and the metrics measured on the project's evaluation samples.

### v5.0 — Document-driven data pipeline
- Instead of hard-coded Q&A, the Q&A data is generated automatically by parsing policy documents written in a standard Markdown template
  - Major categories and subcategories come from each document's metadata, so the category tree is not hard-coded
  - Questions and answers are extracted from each document's FAQ table; answers are used verbatim, never rewritten
  - Policy articles and related laws are extracted from each document's legal-basis section and shown with the answer
- **Hold-back logic**: items flagged as possibly below the legal minimum (L4) or whose legal basis is not yet verified (`verified=false`) are excluded from search and shown only to HR
  - At build time, documents labeled "statutory" but citing no law article are detected automatically and held back
- The security filter was consolidated into one module shared by the app and the tests

### v6.0 — Access control, privacy, data quality
- **Access control design**
  - Access to employee data is split by role, and access to another person's data is decided in a single function
  - FAQs a user is not allowed to see are not just hidden in the UI — they are **left out of that session's search index**
  - Password hashing, login lockout
- **Privacy design**
  - Conversation history is deleted automatically after a retention period; the same rule applies to unanswered-question records and the security log
  - Users can view their own history and request deletion; consent is collected on first use
  - Answer feedback (👍/👎) is stored anonymously, and statistical reports never include the original questions
- **Data quality**
  - Review results are kept in a separate file, so rebuilding from the documents never loses reviewed content. Answers with unresolved content are held back automatically
  - Paraphrases were expanded, with automatic checks for copied originals, empty strings and duplicates across FAQs
  - A pre-deployment check (`preflight`) blocks data errors
- **Search**: Korean sentence embeddings are the default backend, with a fallback to TF-IDF if the model cannot load
- **UI**: chat interface, plus a "find programs by life situation" screen

### v7.0 — Two-tier responses + gap gate
The core principle is unchanged: the bot never generates text. Even the "did you mean" step only shows original FAQ questions.

- **Two-tier responses + gap gate**: instead of a single threshold, each query is decided in this order
  1. top score ≥ the auto-answer threshold **and** the gap between the top two scores ≥ the gap threshold → automatic answer with references
  2. otherwise, if items above the candidate threshold exist → "Is it one of these?" with up to 3 candidates
  3. no candidates → unanswered queue → HR answers
  - With an absolute threshold alone, the bot confidently picks one item even when the top two are practically tied. In that zone the right answer is often 2nd or 3rd, so asking back reduces wrong answers.
- **Closing the unanswered loop**: the employee sees HR's answer in their own menu (looked up by session). HR answers are never added to the FAQ automatically; FAQs change only by editing the documents and rebuilding
- **Always-on input box**: questions can be typed without choosing a category. Every query goes through the same path, so the security filter always applies
- **Visible fallback**: running on TF-IDF instead of embeddings triggers a warning on screen and in the pre-deployment check
- **Evaluation design**
  - Strict scoring at the level of individual FAQ items, not subcategories
  - "Search after choosing a program" and "search everything" measured side by side
  - Outcomes split into correct / correct answer among candidates / unresolved / **confident wrong answer** (answered automatically, but wrong)
  - Hold-out samples: some paraphrases of each FAQ are removed from the index and used as queries, so the correct answer is fixed without human judgment
  - Out-of-scope questions measured by type (no data / needs a personal judgment / another person's data / held-back items)
  - Thresholds chosen from a grid of auto-answer threshold × margin × gap combinations

### v7.5 — Independent re-measurement and limitations
v7.0 was re-measured from an unmodified copy, and the samples used for threshold tuning were excluded from the evidence.

> The numbers below were measured **on the project's limited evaluation samples** and are not production performance. The evaluation questions were written by the team, and the answer key for the free-text set was not reviewed by the company's HR staff.

**Conditions**: search everything (no category selected), embedding backend, before the gap gate (gap 0) vs. v7.0 (gap 0.08)

| Sample | Resolution rate | Confident wrong rate | Auto-answer rate |
|---|---|---|---|
| Hold-out slice A (n=386) | 78.8% → **93.8%** | 21.0% → **2.9%** | 93.8% → 39.9% |
| Hold-out slice B (n=386) | 77.5% → **93.8%** | 21.8% → **1.6%** | 93.0% → 35.8% |
| Free-text set (n=30) | 70.0% → **83.3%** | 26.7% → **3.3%** | 53.3% → 10.0% |

- **Resolution rate** = correct automatic answer + correct answer among the 3 "did you mean" candidates
- **Confident wrong rate** = answered automatically, but not with the correct item
- Hold-out samples use two paraphrases per FAQ, removed from the index, as queries. Slices A and B do not overlap.

**Out-of-scope questions (number of automatic answers; identical in two separate sets)**

| Type | Questions per set | gap 0 | v7.0 |
|---|---|---|---|
| Needs a personal judgment | 6 | 5 answered automatically | **0** (all 6 asked back) |
| Original question of a held-back item | 4 | 2 answered automatically | **0** (all 4 asked back) |
| Another person's data | 4 | 0 (4 blocked by the filter) | 0 (4 blocked by the filter) |
| Topic not in the data | 8 | set A 1 / set B 0 | set A 1 / set B 0 |

**Backend comparison (hold-out slice A, search everything, v7.0 settings)**: resolution rate 93.8% with embeddings vs. 70.2% with TF-IDF. The TF-IDF fallback is treated as a failure state, not normal operation.

**Caveats**
- The cost of the gap gate is a lower auto-answer rate (last column above). The resolution rate is an **upper bound that assumes the employee clicks a candidate**; the click-through rate was not measured.
- The free-text set has only 30 questions, so one question is 3.3 percentage points.
- Topics missing from the data can still get through the gap gate (1 case in set A). Only adding data fixes this, not thresholds.
- Questions about held-back items no longer get automatic answers, but other FAQs from the same program appear as candidates. The fix is to finalize those answers.
- Multi-turn context is not supported.

### final — Data fixes and preparing the next measurement (not yet measured)
The search code and thresholds are unchanged from v7.0, and the effect of these changes has not been measured yet.
- **Entry FAQs**: programs that had only edge-case FAQs and no "what is this program and who can use it" entry point got an entry FAQ
- **Typed evaluation set (pilot)**: mixes easy / ambiguous / misleading / out-of-scope questions, each with its own definition of success, **reported separately**. A single average would let the types that improve with a higher gap cancel out the types that get worse. Deliberately includes colloquial phrasing, abbreviations and typos
- **Root-cause tool for held-back items**: classifies why another FAQ shows up when a held-back item is asked, by "what it lost to": policy / embedding / compound question / metadata. Runs on a temporary copy without touching production data

## Getting started (v4.0)

```bash
pip install -r requirements.txt
# Optional, for better matching accuracy (large download):
pip install sentence-transformers

python build_qa_data.py   # (optional) regenerate data/qa_data.json from build_qa_data.py
streamlit run app.py

# (optional) connect law-newsletter results
export LAW_NEWSLETTER_PATH=/path/to/law_newsletter
```

The UI and data are in Korean.

## Test accounts (demo only)

| Employee no. | Password | Role |
|---|---|---|
| 20230101 | 1234 | Employee |
| 20180501 | 1234 | Employee |
| 20100301 | admin | HR admin |

> These are fictional demo accounts. The prototype compares plain-text passwords, so a real deployment would need proper company authentication (e.g. SSO).

## Security design — 4 layers against viewing other employees' data

1. **Structural isolation**: personal data never exists in the chatbot's knowledge base (`qa_data.json`). The bot only answers about policies and laws, so no question can surface another person's data.
2. **Session-based lookup**: personal lookups (remaining leave, family-event payments) use only the employee number of the logged-in session. The target employee number is never taken from user input — the most important rule.
3. **Query filter**: questions containing another employee's number, a name, or phrasing that asks about someone else are blocked before matching.
4. **Audit log**: blocked attempts are written to `data/security_log.json` and shown on the HR admin page.

Filter tests: `python test_security.py` (9 scenarios)

## HR admin dashboard + report automation

| Task | Command | Suggested schedule |
|---|---|---|
| Weekly report (leave status) | `python report.py weekly` | Fridays 09:00 |
| Monthly statistics (share on leave, leave type × gender) | `python report.py monthly` | 1st of each month 09:00 |
| Law-amendment check | `python law_tracker.py` | Daily 08:00 |

Reports are saved as xlsx files under `reports/`. Fill in the SMTP settings in `send_email()` in `report.py` to send them automatically.
Law tracking collects real data when the `LAW_OC_KEY` environment variable is set (free key from open.law.go.kr); otherwise it uses sample data.

## Project structure

- `app.py` — Streamlit web app (login → role-based views → navigation / chat / dashboard)
- `matcher.py` — similarity matching engine (standalone test: `python matcher.py`)
- `build_qa_data.py` — category tree and FAQ definitions → generates `data/qa_data.json`
- `test_security.py` — security filter tests
- `report.py` — weekly / monthly report generation
- `law_tracker.py` — law-amendment checks
- `legal_updates_page.py`, `services/legal_update_service.py` — law updates tab (law_newsletter integration)
- `data/` — fictional employee / leave data, Q&A data, sample law-tracking data (see `data/README.md`)
- `코드북_초안.docx`, `make_codebook.js` — data-building codebook (Korean) and its generator script

## Tuning the similarity thresholds (v4.0)

Adjust `THRESHOLD_EMBEDDING` (default 0.55) and `THRESHOLD_TFIDF` (default 0.5) at the top of `matcher.py`. Higher values mean fewer wrong answers but more unanswered questions.
