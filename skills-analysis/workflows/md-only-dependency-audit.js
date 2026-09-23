export const meta = {
  name: 'md-only-ui-dependency-audit',
  description: 'For 50 finance/legal/HR/ops skills: what they produce, what they depend on outside SKILL.md, and whether they work uploaded alone into a 20-file markdown-only UI; then adversarially verify',
  phases: [
    { title: 'Analyse', detail: '5 agents x 10 skills' },
    { title: 'Verify', detail: 'a skeptic per batch re-checks every verdict and dependency' },
  ],
}

const SP = '/tmp/claude-0/-home-user-2048/52a1ea60-b7a7-54b2-835a-a72ec8f4e1e5/scratchpad'
const CONTEXT = `CONTEXT. A company's internal product lets users upload an Agent Skill (a folder with SKILL.md) through a UI that accepts AT MOST 20 FILES and ONLY MARKDOWN files. There is no bundled code, templates, data or binary files, and there is no guarantee that other skills, plugin-level files, or built-in document skills are present. We are measuring whether real, published finance/legal/HR/operations skills could do their job under that constraint. Be fair in BOTH directions. Many skills are genuinely fine as markdown only (for example review checklists or drafting guidance that output text). Others silently depend on things outside their folder.
Reference sizes for Anthropic's built-in document skills (anthropics/skills, local clone at ${SP}/repos/anthropics__skills/skills/<name>): docx = 61 files (1 md, 15 scripts, 5 templates, 39 XSD schemas/data, 1 license); xlsx = 53 (1 md, 12 scripts, 39 data); pptx = 56 (1 md, 15 scripts, 39 data); pdf = 12 (3 md, 8 scripts).`

const ANALYSIS = {
  type: 'object',
  properties: {
    skills: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          outputs: { type: 'array', items: { type: 'string', enum: ['chat-text', 'markdown-or-text-doc', 'xlsx', 'docx', 'pptx', 'pdf', 'html', 'csv-json-data', 'writes-to-external-system', 'image-media'] } },
          needs_code_execution: { type: 'boolean', description: 'The skill tells the agent to write/run code (python, bash, node, sql) or run bundled scripts' },
          code_evidence: { type: 'string', description: '<=20 words quoting or naming the instruction, or "none"' },
          bundled_non_md: { type: 'array', items: { type: 'object', properties: { files: { type: 'string', description: 'path or glob' }, role: { type: 'string', enum: ['script', 'template', 'data-schema', 'lookup-data', 'asset', 'test-eval', 'packaging', 'other'] }, purpose: { type: 'string', description: '<=15 words' } }, required: ['files', 'role', 'purpose'] } },
          external_deps: { type: 'array', items: { type: 'object', properties: {
            kind: { type: 'string', enum: ['plugin-level-file', 'other-skill', 'built-in-doc-skill', 'mcp-connector-or-api', 'cli-or-library', 'referenced-file-missing'] },
            name: { type: 'string' },
            resolved_path: { type: 'string', description: 'actual path in the repo if it exists, else "not found"' },
            file_count: { type: 'integer', description: 'number of files that dependency adds if it had to be bundled (0 if unknown/not a file)' },
            evidence: { type: 'string', description: '<=20 words quoted from SKILL.md or a reference file' } },
            required: ['kind', 'name', 'resolved_path', 'file_count', 'evidence'] } },
          md_only_ui_verdict: { type: 'string', enum: ['works', 'degraded', 'breaks'], description: 'If ONLY the markdown files in this folder were uploaded (<=20 files), with no code files, no other skills, no plugin-level files: works = same result; degraded = runs but loses accuracy, formatting, validation or policy context; breaks = cannot produce its core output' },
          verdict_reason: { type: 'string', description: '<=30 words, concrete' },
        },
        required: ['id', 'outputs', 'needs_code_execution', 'code_evidence', 'bundled_non_md', 'external_deps', 'md_only_ui_verdict', 'verdict_reason'],
      },
    },
  },
  required: ['skills'],
}

const VERIFY = {
  type: 'object',
  properties: {
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          verdict_agrees: { type: 'boolean' },
          corrected_verdict: { type: 'string', enum: ['works', 'degraded', 'breaks'] },
          deps_wrong: { type: 'array', items: { type: 'string' }, description: 'names of listed external_deps that are false or not actually required' },
          deps_missed: { type: 'array', items: { type: 'string' }, description: 'real dependencies the analyst missed' },
          code_execution_correct: { type: 'boolean' },
          note: { type: 'string', description: '<=30 words' },
        },
        required: ['id', 'verdict_agrees', 'corrected_verdict', 'deps_wrong', 'deps_missed', 'code_execution_correct', 'note'],
      },
    },
  },
  required: ['checks'],
}

const batches = [0, 1, 2, 3, 4]
const results = await pipeline(
  batches,
  (i) => agent(`${CONTEXT}

TASK. Read ${SP}/focus/batch${i}.tsv (columns: id, group, publisher, repo, name, skill_dir_abs_path). For EVERY row (one entry per id):
1. Read SKILL.md in full and every other file in the folder (skim non-md files enough to know their role and purpose).
2. Determine what the skill produces (outputs) and whether it needs code execution.
3. List every dependency OUTSIDE the folder: plugin-level files it tells the agent to read (resolve ../ paths and names like CLAUDE.md, CONNECTORS.md, shared/*.md against the repo on disk and count files), other skills it invokes, built-in doc skills it relies on to create xlsx/docx/pptx/pdf (explicitly named OR implied by producing that file type without bundling a generator), MCP connectors/APIs, CLIs/libraries (openpyxl, python-docx, LibreOffice...), and referenced files that don't exist anywhere. Give quoted evidence. Don't list placeholders like path/to/input.csv or output paths as dependencies.
4. Give the md_only_ui_verdict with a concrete reason.`,
    { label: `analyse:batch${i}`, phase: 'Analyse', schema: ANALYSIS }),
  (res, i) => res && agent(`${CONTEXT}

You are an adversarial reviewer. Another analyst produced the JSON below for the skills listed in ${SP}/focus/batch${i}.tsv. Re-open each skill folder (and any dependency paths) yourself and try to REFUTE each verdict and each listed dependency. Watch for both kinds of error: calling a skill 'breaks' when markdown alone would really do (e.g. the file type could be produced as plain text), and calling it 'works' when it silently needs code execution, a document skill, plugin-level context or a missing file. For each id, say whether you agree and give the corrected verdict (same as the original if you agree).

ANALYST OUTPUT:
${JSON.stringify(res.skills)}`,
    { label: `verify:batch${i}`, phase: 'Verify', schema: VERIFY }).then((v) => ({ analysis: res.skills, verify: v && v.checks })),
)
return { batches: results.filter(Boolean) }
