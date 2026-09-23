export const meta = {
  name: 'classify-output-complexity',
  description: 'Classify ~392 finance/legal/HR/ops/reporting skills by deliverable type and multi-step complexity',
  phases: [{ title: 'Classify', detail: '5 agents x ~79 skills, reading each SKILL.md' }],
}
const SP = '/tmp/claude-0/-home-user-2048/52a1ea60-b7a7-54b2-835a-a72ec8f4e1e5/scratchpad'
const SCHEMA = {
  type: 'object',
  properties: {
    skills: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          deliverables: { type: 'array', items: { type: 'string', enum: ['chat-answer', 'structured-report-text', 'xlsx', 'docx', 'pptx', 'pdf', 'html', 'data-file', 'external-system-changes'] }, description: 'What the skill hands back. chat-answer = short advice/checklist/answer in chat; structured-report-text = a multi-section memo/report/plan written as markdown or text' },
          steps: { type: 'integer', description: 'Number of distinct sequential stages the skill prescribes to produce its output (count numbered steps/phases/workflow stages; 1 if single pass)' },
          calculations: { type: 'boolean', description: 'Output depends on non-trivial computation (models, ratios, reconciliations, scoring, statistics)' },
          quality_gate: { type: 'boolean', description: 'Explicit verification before delivery: tie-outs, recalculation, schema/formula/citation checks, reconciliation, review loop' },
          multi_source: { type: 'boolean', description: 'Combines 2+ inputs/sources (documents, systems, datasets)' },
          complexity: { type: 'string', enum: ['simple', 'moderate', 'complex'], description: 'simple: single-pass answer, checklist or advice. moderate: a few steps producing a structured document. complex: a substantial deliverable (a file, model, or multi-section report) built through 4+ distinct steps, usually with calculations, multiple sources or a verification gate' },
          output: { type: 'string', description: '<=12 words: what the finished output is' },
        },
        required: ['id', 'deliverables', 'steps', 'calculations', 'quality_gate', 'multi_source', 'complexity', 'output'],
      },
    },
  },
  required: ['skills'],
}
const res = await parallel([0, 1, 2, 3, 4].map((i) => () => agent(
`We are studying Agent Skills (folders with SKILL.md) used for business knowledge work: finance, investing, legal, HR, operations, reporting. We need to know which ones perform COMPLEX, MULTI-STEP OUTPUT GENERATION (building a model, a deck, a filing, a multi-section report, a reconciled workbook) and which ones give SIMPLE answers (checklists, advice, a short reply).

Read ${SP}/complex/chunk${i}.tsv (columns: id, group, repo, name, skill_dir_abs_path, skill_md_lines, files_in_folder). For EVERY row (one entry per id, none skipped), read the SKILL.md at skill_dir_abs_path. Skim it; for long files read the workflow/steps and output sections carefully. Classify it using the schema. Judge by what the skill instructs, not by how many files it has. Be consistent across rows. Return via the structured output tool.`,
  { label: `classify:chunk${i}`, phase: 'Classify', schema: SCHEMA })))
const all = res.filter(Boolean).flatMap((r) => r.skills)
log(`classified ${all.length}`)
return { skills: all }
