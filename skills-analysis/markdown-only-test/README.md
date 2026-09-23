# The markdown-only test: 50 finance, legal, HR and operations skills

Question: could real, published business skills work in an upload UI that accepts **at most 20 files, all markdown**?

Interactive page: `../report/markdown-only-test.html`

## Result

| | Skills |
|---|---|
| Works the same when uploaded as markdown only | **18 / 50** |
| Degraded (runs, but loses accuracy, validation, formatting or policy context) | **26 / 50** |
| Breaks (can't produce its core output) | **6 / 50** |
| Skills that deliver an Excel, Word or PowerPoint file and still work | **0 / 13** |
| Skills that run code (Python, SQL, shell) and still work | **1 / 22** |
| Fit ≤20 markdown files: folder alone → with what the skill reads and invokes | **36 → 28** |

- Of the 32 skills that fall short, **22** are missing a non-markdown file: a script, a template or data file, or the document generator behind an Office deliverable. The other 10 lose markdown context (plugin-level playbooks, sibling skills) or need a connector.
- All 18 skills that work are checklist, framework or template skills whose output is text in the chat, or connector calls written out in the markdown.
- Anthropic's document skills, which the markdown-only finance and legal skills rely on for Office output: docx 61 files, xlsx 53, pptx 56. Most of those files are scripts and XML schemas.

By domain (works / degraded / breaks): Finance & accounting 6/3/1; Investing & banking 1/11/0; Legal & compliance 2/8/4; HR & people 5/2/0; Operations 4/2/1.

## What real skills in these domains carry (census of 329)

| Domain | Skills | Folder fits UI | Scripts | Templates (any format) | Data files | Binary assets | Delivers Office file | Reads files outside folder |
|---|---|---|---|---|---|---|---|---|
| Finance & accounting | 55 | 84% | 13% | 9% | 5% | 0% | 29% | 25% |
| Investing & banking | 76 | 64% | 30% | 32% | 12% | 0% | 79% | 29% |
| Legal & compliance | 154 | 84% | 14% | 5% | 3% | 0% | 20% | 77% |
| HR & people | 18 | 94% | 6% | 11% | 0% | 0% | 17% | 50% |
| Operations | 26 | 54% | 46% | 31% | 8% | 0% | 12% | 38% |
| All five domains | 329 | 78% | 20% | 14% | 6% | 0% | 34% | 53% |

## Method

- **Sample:** 50 skills drawn from 329 real finance, legal, HR and operations skills (the census from the main analysis, with demos, routers and duplicates already removed). 10 finance and accounting, 12 investing and banking, 14 legal and compliance, 7 HR, 7 operations. Picks follow SKILL.md hash order, with at most 4 per repo per domain.
- **Counting (`focus.py`):** every file in the skill folder, in exclusive roles: md, script, template (non-markdown), data, asset, packaging/license/other. The script also counts code blocks embedded in the markdown and references to files outside the folder.
- **Verdicts (`../workflows/md-only-dependency-audit.js`, `focus_audit.json`):** 5 agents each read 10 skills in full, including the files they point to, and judged each one uploaded as markdown only. 5 skeptic agents then re-opened every skill to refute each verdict. They changed 1 of 50.
- **As-published footprint (`focus_effective.py`):** folder files, plus the plugin-level files the skill reads, the sibling skills it invokes, and the document skill for each Office format it outputs. Connectors and installed libraries add no files.

Files: `focus_50.csv` (per-skill table), `focus_rows.json`, `focus_audit.json` (full agent analyses with quoted evidence), `focus_page_data.json`.
