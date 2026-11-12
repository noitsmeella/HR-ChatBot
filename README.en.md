[한국어](README.md) | **English**

# HR Chatbot Prototype

A **retrieval-only HR chatbot** that answers employee questions about internal HR policies.
It never generates answers. Instead, it finds the closest match among human-written, reviewed Q&A items and returns it together with the supporting policy and legal references.
Everything runs locally with no external API calls, so personal data and confidential company information never leave the machine.

> **About what is published here**
> This repository contains **v1.0 – v4.0** only (v4.0 includes the law-newsletter integration). All employee, leave and leave-of-absence data in these versions is **fictional**. In v4.0, the category tree keeps only statutory programs (those with a legal basis), and every FAQ is replaced with a placeholder that has no real content.
> From v5.0 onward, the chatbot uses real internal company documents as its knowledge source. Under the company's security policy (no external distribution), that code and data are not published.
> The implementation and measured results are described instead under [Later versions](#later-versions-private).

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
| final | 2026-08-13 | *(private)* 18 entry FAQs added, evaluation set C (pilot), root-cause tool for held-back items |

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
- The public repository keeps only statutory programs: Working hours (2) / Statutory leave & leave of absence (13) / Hiring & retirement (3), 18 subcategories in total
- Each subcategory has a single placeholder FAQ (no real FAQ content)
- Entering a subcategory shows its FAQs as buttons. Free-text questions are searched within the selected subcategory first, then across all subcategories as a fallback (showing where the match came from)
- Categories and FAQs are defined in one place (`build_qa_data.py`), which generates `qa_data.json`
- TF-IDF threshold raised from 0.4 to 0.5 as the number of FAQs grew
- **Law updates tab**: shows, read-only, the `change_report.json` produced by a separately built law newsletter (law_newsletter) in the admin view: laws checked, changed articles with before/after text, and HR checkpoints. Without `LAW_NEWSLETTER_PATH`, built-in sample data is shown

## Later versions (private)

From v5.0 onward the code contains internal company data and is not published. This section describes only the implementation and the measured results.

### v5.0 — Real internal data
- **Document-driven data pipeline**: replaced the hard-coded Q&A with automatic generation from internal policy documents written in a standard template (36 Markdown files)
  - Major categories and subcategories come from each document's metadata, so the category tree is not hard-coded
  - Questions and answers are extracted from each document's FAQ table; answers are used verbatim, never rewritten
  - Internal-policy articles and related laws are extracted from each document's legal-basis section and shown with every answer
- **Hold-back logic**: items flagged as possibly below the legal minimum (L4) or whose legal basis is not yet verified (`verified=false`) are excluded from search; only their count is shown to HR
  - At build time, documents labeled "statutory" but citing no law article are detected automatically and held back
- **Single security filter**: the app and the tests share one filter module
- Law tracking moved out of the chatbot and replaced with a link to the external law-newsletter page

### v6.0 — Access control, privacy, data quality
- **Access control**
  - Employee-data access levels (employee / team lead / HR). Access to another person's data is decided in a single function, and HR viewing someone else's conversation is written to an audit log
  - FAQ visibility levels (`member` / `leader` / `staff_only`). `staff_only` items are not just hidden in the UI — they are **left out of the search index** for employee sessions
  - PBKDF2 password hashing, login lockout and session policy
- **Privacy**
  - Conversation history stored in SQLite and deleted automatically after the retention period (default 180 days); the same policy applies to the unanswered queue and the security log
  - One-time privacy consent on first login; separate screen for viewing one's own history and requesting deletion
  - 👍/👎 feedback stored anonymously, without the employee number. A question is forwarded to HR with the employee number only when the employee asks for it
  - Quarterly reports contain keyword counts and sample sizes, never the original questions
- **Data quality**
  - Review results kept in a separate override file, so rebuilding from the documents never loses reviewed content. Answers with unresolved options or blanks are held back automatically
  - Added 1,554 paraphrases and consolidated to 198 FAQs, with automatic checks for copied originals, empty strings and duplicates across FAQs
  - A pre-deployment check (`preflight`) blocks duplicate policy names, duplicate original questions and similar errors
- **Search**: the Korean sentence-embedding model became the default backend, with a safe fallback to TF-IDF if the model cannot load. Added a free-text evaluation set written separately from the FAQs
- **UI**: redesigned as a chat interface (responsive, keyboard-accessible), plus a "find programs by life situation" screen

### v7.0 — Two-tier responses + gap gate
The core principle is unchanged: the bot never generates text. Even the "did you mean" step only shows original FAQ questions.

- **Two-tier responses + gap gate**: instead of a single threshold, each query is decided in this order
  1. top score ≥ 0.75 **and** top − second ≥ 0.08 → automatic answer with references
  2. otherwise, if candidates ≥ 0.55 exist → "Is it one of these?" with up to 3 candidates
  3. no candidates → unanswered queue → HR answers
  - With an absolute threshold alone, the bot confidently picks one item even when the top two are practically tied. In that zone the right answer is often 2nd or 3rd, so asking back improves the resolution rate and the wrong-answer rate together.
- **Closing the unanswered loop**: when HR answers, the employee sees it in their own menu (looked up by session only). HR answers are never added to the FAQ automatically; FAQs change only by editing the documents and rebuilding
- **Always-on input box**: questions can be typed without choosing a category first. Every query goes through the same path, so the security filter always applies
- **Visible fallback**: if the embedding model fails and TF-IDF takes over, a warning appears on screen and in the pre-deployment check
- **Evaluation redesign**
  - Scoring tightened from subcategory level to **individual FAQ items**
  - "Search after choosing a program" and "search everything" measured side by side
  - Outcomes split into correct / correct answer among candidates / unresolved / **confident wrong answer** (answered automatically, but wrong)
  - Hold-out set: two paraphrases per FAQ removed from the index and used as queries (n=386). The correct answer is fixed by construction, so no human judgment is involved; changing the slice gives non-overlapping samples
  - Out-of-scope questions measured by type (no data / needs a personal judgment / another person's data / held-back items)
  - Final thresholds chosen from a grid of 27 combinations (auto threshold × margin × gap)

### v7.5 — Independent re-measurement and limitations
All numbers were re-measured from an unmodified copy of v7.0. The slice used for threshold tuning is excluded from the evidence.

**Search-everything condition, embedding backend**

| Sample | Before gap gate (resolved / confident wrong) | v7.0 (resolved / confident wrong) | Auto-answer rate |
|---|---|---|---|
| Hold-out slice A (n=386) | 78.8% / 21.0% | **93.8% / 2.9%** | 93.8% → 39.9% |
| Hold-out slice B (n=386) | 77.5% / 21.8% | **93.8% / 1.6%** | 93.0% → 35.8% |
| Free-text set (n=30) | 70.0% / 26.7% | **83.3% / 3.3%** | 53.3% → 10.0% |

- Resolved = correct automatic answer + correct answer among the candidates
- Automatic answers to questions that need a personal judgment: 5 → 0 (in both sets)
- Held-back items shown directly: 0 in every condition
- Questions about another person's data: 4/4 blocked by the filter
- Under the same conditions the TF-IDF fallback resolves 23.6 percentage points fewer queries, so fallback is treated as a failure state, not normal operation

**Remaining limitations (measured, or not yet measured)**
- The cost of the gap gate is a lower auto-answer rate. The resolution rates above are **upper bounds that assume the employee clicks a candidate**; the click-through rate on candidates has not been measured yet.
- Topics missing from the FAQs can still get a high top score with a clear gap, so no threshold can stop them. Only adding data fixes this.
- Questions about held-back items no longer get automatic answers, but other FAQs from the same program still appear as candidates. The fix is to finalize those answers, not to change the search.
- The free-text set has only 30 questions, so one question is 3.3 points, and its answer key has not yet been reviewed by HR.
- Multi-turn context is not supported, and performance on colloquial phrasing, abbreviations and typos has not been measured.

**Verification**: 68 automated tests passed; pre-deployment check reported 0 errors and 0 warnings

### final — Data fixes and preparing the next measurement (not yet measured)
Work that addresses the limitations found in v7.5 through data and evaluation. The search code (`matcher.py`) and thresholds are unchanged from v7.0, and the effect of these changes has not been measured yet.

- **18 entry FAQs added**: 18 programs had FAQs only for specific edge cases and no "what is this program and who can use it" entry point; one entry FAQ was added to each
  - 216 FAQs (212 visible, 4 held back), 1,720 paraphrases
  - The coverage check now reports zero programs without an entry FAQ, zero programs without FAQs and zero items with too few paraphrases
  - 68 automated tests pass on the 216-item data
- **Evaluation set C (15-question pilot)**: replaces set B, which always scored 100% and could not tell settings apart
  - Mixes four types — easy / ambiguous / misleading / out of scope — each with its own definition of success, **reported separately**. A single average would let the types that improve with a higher gap cancel out the types that get worse
  - Questions were written from scratch without reusing FAQ wording, and deliberately include colloquial phrasing, abbreviations and typos, which had never been measured
  - To be expanded to 100 questions. Questions and answer keys were written by AI and have not been reviewed by HR yet, so the results are not used as evidence
- **Root-cause tool for held-back items**: when a held-back item is asked, another FAQ from the same program shows up instead; the tool classifies each case by "what it lost to"
  - Policy (search was right; the hold-back rule removed the answer) / embedding (sentences within one program are not distinguishable) / compound question (the query spans two programs) / metadata (the question text does not represent the query)
  - Runs on a temporary copy with held-back items included in the index; production data and matching code are not modified


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
- `data/` — fictional employee / leave data, Q&A data, sample law-tracking data
- `코드북_초안.docx`, `make_codebook.js` — data-building codebook (Korean) and its generator script

## Tuning the similarity thresholds (v4.0)

Adjust `THRESHOLD_EMBEDDING` (default 0.55) and `THRESHOLD_TFIDF` (default 0.5) at the top of `matcher.py`. Higher values mean fewer wrong answers but more unanswered questions.
