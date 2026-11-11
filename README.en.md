[한국어](README.md) | **English**

# HR Chatbot Prototype

A **retrieval-only HR chatbot** that answers employee questions about internal HR policies.
It never generates answers. Instead, it finds the closest match among human-written, reviewed Q&A items and returns it together with the supporting policy and legal references.
Everything runs locally with no external API calls, so personal data and confidential company information never leave the machine.

> **About what is published here**
> This repository contains **v1.0 – v4.0** only (v4.0 includes the law-newsletter integration). All employee, leave and leave-of-absence data in these versions is **fictional**. In v4.0, the category tree keeps only statutory programs (those with a legal basis), and every FAQ is replaced with a placeholder that has no real content.
> From v5.0 onward, the chatbot uses real internal company documents as its knowledge source. Under the company's security policy (no external distribution), that code and data are not published.
> The implementation is described instead under [Later versions](#later-versions-private).

## Version history

| Version | Date | Highlights |
|---|---|---|
| v1.0 | 2026-07-26 | Core retrieval chatbot: login → role-based views (employee / HR admin), 4 categories, embedding / TF-IDF similarity matching, unanswered-question log |
| v2.0 | 2026-07-27 | 4-layer protection against viewing other employees' data + 9 security tests, policy-to-law relation types (L1–L3), data-building codebook |
| v3.0 | 2026-07-27 | HR admin dashboard (leave status, leave type × gender stats), automated weekly / monthly reports, law-amendment tracking |
| v4.0 | 2026-07-30 | Redesigned navigation (major category → subcategory → clickable FAQ + free-text question), law-newsletter results in the admin view |
| v5.0 | 2026-08-03 | *(private)* Switched to real internal data — see below |

Each version is a separate commit (`git log`).

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

### v5.0 — Real internal data
- **Document-driven data pipeline**: replaced the hard-coded Q&A with automatic generation from internal policy documents written in a standard template (36 Markdown files)
  - Major categories and subcategories come from each document's metadata, so the category tree is not hard-coded
  - Questions and answers are extracted from each document's FAQ table; answers are used verbatim, never rewritten
  - Internal-policy articles and related laws are extracted from each document's legal-basis section and shown with every answer
  - Result: 36 subcategories and about 200 FAQs built automatically from the documents
- **Hold-back logic**: items flagged as possibly below the legal minimum (L4) or whose legal basis is not yet verified (`verified=false`) are excluded from search; only their count is shown to HR
  - At build time, documents labeled "statutory" but citing no law article are detected automatically and held back
- **Single security filter**: the app and the tests share one filter module
- Law tracking moved out of the chatbot and replaced with a link to the external law-newsletter page; the employee view was simplified

<!-- TODO: add matching improvements from the final version (embedding results, gap gate, etc.) and measured metrics once the final code is confirmed -->

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

## Tuning the similarity thresholds

Adjust `THRESHOLD_EMBEDDING` (default 0.55) and `THRESHOLD_TFIDF` (default 0.5) at the top of `matcher.py`. Higher values mean fewer wrong answers but more unanswered questions.
