# What's inside a real knowledge-work skill folder?

A survey of **100 audited, production knowledge-work Agent Skills** (folders containing a `SKILL.md`) published by Anthropic, OpenAI, other vendors and a few large community repos. It is cross-checked against a **census of all 987 eligible skills** in those repos. Repos were cloned on 23 Sep 2026; the exact commits are in `repos_pinned.txt`.

Interactive report: `report/skill-folder-anatomy.html`

> **New: the markdown-only test.** 50 real finance, legal, HR and operations skills were each uploaded as markdown only, the way a 20-file, markdown-only UI would take them. See `markdown-only-test/README.md` and `report/markdown-only-test.html`.

## Checking a "max 20 files, all markdown" rule

Every file inside the skill folder counts, including `references/` and any other subfolder. Tested on the census of 987 real knowledge-work skills; the audited 100-skill sample is shown as a check.

| Rule | Census (987) | Sample (100) | Verdict |
|---|---|---|---|
| 20 files or fewer | **96%** (38 exceed) | 96% | Matches the field. 95% of skills have ≤18 files. |
| Markdown only (ignoring OpenAI UI metadata and licenses) | **60%** (53% strict) | 66% (54% strict) | Stricter than the field |
| Markdown only, among skills with more than one file | **24%** | 31% | Stricter than the field. Once a skill grows past SKILL.md, most add code or data. |
| More than 20 **markdown** files | 4 skills | 0 | Markdown count alone almost never hits 20 |

By publisher (census): ≤20 files: Anthropic 98%, OpenAI 95%, other vendors 99%, community 94%. Markdown-only: Anthropic 93%, OpenAI 40%, other vendors 69%, community 33%.

**What breaks the markdown-only rule.** 400 of 987 skills ship non-markdown content. 78% of those include scripts or code (mostly Python) and 21% add only data (JSON/YAML/CSV schemas, lookup tables, templates). Binary assets appear in just 12 skills.

An agent opened every non-markdown file in 36 skills spread across publishers (largest included) and asked whether markdown alone could do the same job:
- **23 of 36: no.** The files recalculate models, validate output (e.g. Word XML against 39 OOXML schemas), edit Office/PDF files, call APIs, or measure things the model can't (audio length).
- **6: partly.** YAML state stores, an HTML template.
- **7: yes.** Evaluation rubrics and catalog metadata that nothing reads at run time.

**Official guidance.** Each quote was verified word for word against the live source by a separate agent; see `guidance.json`.
- Anthropic: no file-count limit; the only hard limit is 30 MB per skill. The Agent Skills overview says "A Skill can include dozens of reference files" and "No practical limit on bundled content". The authoring best practices recommend pre-made scripts ("More reliable than generated code … Prefer scripts for deterministic operations") and "Keep SKILL.md body under 500 lines".
- The open spec (agentskills.io): "A skill directory may contain any files and directories beyond the required SKILL.md."
- OpenAI: "Instruction-only is the default. … Prefer instructions over scripts unless you need deterministic behavior or external tooling." The plugins docs say "Use scripts/ when the workflow needs deterministic computation or file processing. … Do not add a script when instructions and existing tools can complete the task reliably." Hard caps: 500 files per skill (API) and 100 per skill (MCP import). The skill-creator bans README/CHANGELOG-style clutter.

**A rule that matches the field.**
1. Default to markdown (SKILL.md + `references/*.md`).
2. Allow `scripts/` when a step must be exact (calculations, validation, Office/PDF editing, API calls), and require SKILL.md to call every script.
3. Allow small data and templates (schemas, lookup tables, output templates).
4. Put the size rule on SKILL.md (under 500 lines, references one level deep, a table of contents for reference files over 100 lines), not on the folder.
5. Use 20 files as a review trigger, not a hard ban. Anthropic's own docx, pptx and xlsx skills are 53–61 files.
6. Ban clutter (README, CHANGELOG, eval files shipped at run time), not file types.

## Answer

**Markdown files per skill folder: mean 2.96, median 1** (90th percentile 8, max 16). The full census gives mean 3.21, median 1.

| Markdown files in the folder (incl. SKILL.md) | Skills (of 100) |
|---|---|
| 1 | 61 |
| 2 | 8 |
| 3–5 | 14 |
| 6–10 | 11 |
| 11–20 | 6 |
| 21+ | 0 |

**What else ships in the folder** (share of the 100 skills with at least one such file, and mean files per skill):

| File type | Skills containing it | Mean files per skill |
|---|---|---|
| Extra markdown beyond SKILL.md (almost always `references/`) | 39% | 1.96 extra (2.96 total) |
| OpenAI UI packaging (`agents/openai.yaml` + icons it references) | 32% | 0.49 |
| Scripts & code (.py .js .sh .sql, HTML/CSS) | 27% | 1.29 |
| Data & config (.json .yaml .csv .xsd .txt) | 17% | 1.14 |
| License file | 6% | 0.06 |
| Binary assets (images, fonts, Office/PDF) | 1% | 0.32 |

- **51%** of skills contain nothing but SKILL.md once packaging and license files are ignored. **45%** are literally a single file.
- Means are pulled up by a few big folders. `fraud-detection` (104 files), `produce` (78) and `docx` (61) hold 39% of all sampled files. Use the medians and the per-skill percentages.
- 12% of skills have an `assets/` folder, but it almost always holds icons, markdown or JSON rather than binary templates.

### By publisher

Columns: mean, median and 90th percentile of markdown files; share of skills with nothing but SKILL.md; share with extra .md, scripts, data/config, binary assets, and OpenAI packaging.

Sample (100):

| Publisher | n | Mean .md | Median .md | P90 .md | SKILL.md only | Extra .md | Scripts | Data/config | Binary assets | Packaging |
|---|---|---|---|---|---|---|---|---|---|---|
| Anthropic | 40 | 1.93 | 1 | 6 | 80% | 18% | 5% | 5% | 0% | 0% |
| OpenAI | 35 | 4.09 | 2 | 11 | 23% | 57% | 54% | 23% | 3% | 91% |
| Other vendors | 15 | 2.40 | 1 | 5 | 60% | 27% | 13% | 20% | 0% | 0% |
| Community | 10 | 4.00 | 3 | 7 | 20% | 80% | 40% | 40% | 0% | 0% |
| **All** | **100** | **2.96** | **1** | **8** | **51%** | **39%** | **27%** | **17%** | **1%** | **32%** |

Census (987), which gives firmer per-publisher numbers:

| Publisher | n | Mean .md | Median .md | P90 .md | SKILL.md only | Extra .md | Scripts | Data/config | Binary assets | Packaging |
|---|---|---|---|---|---|---|---|---|---|---|
| Anthropic | 368 | 1.79 | 1 | 5 | 77% | 20% | 5% | 4% | 1% | 0% |
| OpenAI | 176 | 3.51 | 1 | 12 | 29% | 39% | 50% | 18% | 4% | 90% |
| Other vendors | 72 | 2.75 | 1 | 5 | 58% | 36% | 7% | 24% | 0% | 0% |
| Community | 371 | 4.57 | 4 | 8 | 23% | 75% | 53% | 25% | 0% | 0% |
| **All** | **987** | **3.21** | **1** | **7** | **47%** | **45%** | **32%** | **16%** | **1%** | **16%** |

### Robustness

| Cut | Mean .md | Median | Exactly 1 .md | Scripts |
|---|---|---|---|---|
| Sample | 2.96 | 1 | 61% | 27% |
| Sample, reweighted to the census publisher mix | 3.13 | — | 51% | 28% |
| Census | 3.21 | 1 | 55% | 32% |
| Census without K-Dense | 2.74 | 1 | 60% | 27% |
| Census without claude-for-legal | 3.46 | 1 | 50% | 35% |

### Caveats

- **Only the skill folder is counted.** Anthropic's plugin skills often lean on shared context kept at plugin level (a `CLAUDE.md` playbook, `CONNECTORS.md`, a practice profile). About 56% of Anthropic's single-file skills reference such a file. A thin folder does not mean thin context.
- **anthropics/skills is the exception** inside Anthropic. Its document skills (docx/pptx/xlsx/pdf) ship dozens of Python helpers and OOXML schemas: 55% have scripts and only 9% are single-file.
- **The sample quotas centre the two labs** (40 Anthropic / 35 OpenAI / 15 other vendors / 10 community). The census is dominated by claude-for-legal and the two big community repos, so the pooled sample and census numbers weight publishers differently. The robustness table shows the answer holds either way.
- **Community is illustrative, not representative:** 4 hand-picked large repos.
- **The census was LLM-labelled, not hand-audited.** In the audit, 7 of 138 non-Google picks (5%) were rejected as routers, settings helpers or thin stubs.

## Method

1. **Sources.** 31 repos were cloned:
   - Official Anthropic: skills, knowledge-work-plugins, financial-services-plugins, claude-for-legal, claude-for-financial-advisors, healthcare, life-sciences, k12-teacher-skills, claude-plugins-official, claude-plugins-community, claude-cookbooks.
   - Official OpenAI: skills, plugins, role-specific-plugins.
   - Other vendors: Intuit, HubSpot ×2, Zapier, Atlassian, Canva, Box, Notion, Google Workspace CLI, Gemini CLI workspace.
   - Community: K-Dense scientific skills, coreyhaines31/marketingskills, phuryn/pm-skills, alirezarezvani/claude-skills, kepano/obsidian-skills.
   - Context only (developer-focused): microsoft/skills, huggingface/skills.
2. **Inventory (`inventory.py`).** Every directory containing SKILL.md is a skill. Each file is attributed to its nearest ancestor skill, so nested skills are not double-counted. OpenAI Codex UI metadata (`agents/openai.yaml`, the icons it references, `maintainers.yml`, `.sig`) is tagged as *packaging*.
3. **Candidate pool.** Developer-only repos and plugins, repo tooling, byte-identical copies and `v1/` or `inactive` folders were dropped. `dedup.py` then removed 31 near-duplicates (≥90% identical SKILL.md text), keeping the canonical source.
4. **Labelling.** 9 LLM classifier agents (`workflows/classify-*.js`) labelled 1,441 candidates for knowledge work, domain, role (task / router / setup / meta / example) and real vs toy. Eligible means knowledge work, real and a task skill. The OpenAI life-science database-skill family was labelled as one unit (`overrides.json`). Google Workspace CLI was excluded: all 6 of its audited picks were auto-generated stubs.
5. **Sampling (`sample_and_stats.py`).** Publisher quotas, then allocation proportional to plugin size (cap 6 per plugin; each vendor repo is one stratum). Within each stratum, skills are ordered by SKILL.md hash, so the draw is deterministic.
6. **Audit (`workflows/audit-*.js`).** Agents read every sampled SKILL.md in full and recounted every file by hand. On all 144 skills audited, their counts matched the script with 0 mismatches. 6 rejected picks were replaced from pre-drawn reserves by a fixed rule (`finalize.py`).
7. **Adversarial review (`workflows/verify-and-critic.js`, `critic.json`).** A reviewer re-counted 18 skills (all matched) and tested the headline claims. It flagged outlier-driven pooled shares, over-strong wording on "single SKILL.md", inconsistent labels in one template family, fragmented vendor strata and near-duplicates. All of those were fixed before the final draw. Three near-duplicate pairs it named measured only 11–54% similar and were not merged.

## Files

| File | What it is |
|---|---|
| `final_sample.csv` | The 100 skills: counts per file type, SKILL.md length, audit rating, what the extra files are |
| `final_stats.json` | All statistics: sample, per publisher, per domain, census, robustness cuts |
| `report/skill-folder-anatomy.html` | The interactive report |
| `labels_*.json`, `overrides.json` | Classifier labels (ids map to `pool.json` / `pool_add.json`) |
| `audit*.json`, `critic.json` | Audit verdicts and hand counts; the adversarial review |
| `near_dups.json` | Near-duplicate pairs and which copy was kept |
| `guidance.json` | Verified quotes from Anthropic and OpenAI docs, plus why 36 skills ship non-markdown files |
| `*.py`, `report_template.html` | Pipeline: `inventory.py` → `dedup.py` → `sample_and_stats.py` → `finalize.py` → `build_report.py` |

To reproduce: `./clone_repos.sh && python3 inventory.py && python3 dedup.py && python3 sample_and_stats.py && python3 finalize.py && python3 build_report.py`. The labels and audits are checked in, so no LLM calls are needed. Re-clones fetch each repo's current HEAD, so counts drift as the repos change.
