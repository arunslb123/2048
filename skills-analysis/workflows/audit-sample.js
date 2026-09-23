export const meta = {
  name: 'audit-skill-sample',
  description: 'Blind audit of 128 sampled/reserve skills: verify real knowledge-work, independently recount files by type, describe contents',
  phases: [{ title: 'Audit', detail: '5 agents x ~26 skills' }],
}

const SCHEMA = {
  type: 'object',
  properties: {
    skills: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['keep', 'reject'] },
          reject_reason: { type: 'string', description: 'if reject: not-knowledge-work | toy-demo-example | stub-too-thin | router-or-api-reference | setup-auth | other:<why>' },
          md: { type: 'integer', description: 'count of .md/.mdx files INCLUDING SKILL.md' },
          script: { type: 'integer', description: 'executable/source code files (.py .sh .js .ts .mjs .cjs .rb .ps1 .r .sql .ipynb ...)' },
          asset: { type: 'integer', description: 'images, fonts, office/pdf templates (.docx .xlsx .pptx .pdf), html/css, audio/video' },
          data_config: { type: 'integer', description: '.json .yaml .yml .csv .tsv .xml .xsd .txt .toml etc (non-license)' },
          license: { type: 'integer', description: 'LICENSE* / NOTICE* files' },
          other: { type: 'integer' },
          total: { type: 'integer' },
          md_roles: { type: 'string', description: '<=15 words: what the non-SKILL.md markdown files are (e.g. "references/ on DCF methodology; 3 example outputs"). "none" if SKILL.md only' },
          nonmd_summary: { type: 'string', description: '<=20 words: what the scripts/assets/data files are and do. "none" if no non-md files' },
          skill_md_quality: { type: 'string', enum: ['substantive', 'moderate', 'thin'], description: 'substantive = detailed domain workflow/checklists; thin = a few generic lines' },
        },
        required: ['id', 'verdict', 'md', 'script', 'asset', 'data_config', 'license', 'other', 'total', 'md_roles', 'nonmd_summary', 'skill_md_quality'],
      },
    },
  },
  required: ['skills'],
}

const batches = [0, 1, 2, 3, 4]
const results = await parallel(batches.map(i => () => agent(
`You are auditing Agent Skills (folders containing SKILL.md) for a study of how REAL knowledge-work skills from Anthropic, OpenAI and other publishers are structured.

Read /tmp/claude-0/-home-user-2048/52a1ea60-b7a7-54b2-835a-a72ec8f4e1e5/scratchpad/audit/batch${i}.tsv (columns: id, publisher, repo, name, skill_dir_abs_path). For EVERY row (return one entry per id, none omitted):

1. VERDICT. Read the SKILL.md (skim it fully, it's usually <400 lines) and decide:
   keep  = a real, production-intended skill that helps a knowledge worker (finance, legal, sales, marketing, HR, ops, support, PM, research/science, docs/office, communication, analytics, design) do actual work.
   reject = not knowledge work (software engineering/devops/SDK coding), a toy/demo/example/template, a stub too thin to be useful, mainly an API/CLI reference or router to other skills, or an auth/setup helper. Be fair: a short SKILL.md that encodes a real professional workflow is still 'keep'. Being a wrapper around a vendor tool/API is fine if it performs a user task.

2. INDEPENDENT FILE COUNT. Run your own shell command, e.g. \`find "<dir>" -type f -not -path '*/.git/*' -not -path '*/node_modules/*'\`. IMPORTANT: if a subdirectory contains its own SKILL.md, it is a separate nested skill: exclude that subdirectory's files. Count every remaining file into exactly one bucket: md (all .md/.mdx/.markdown incl. SKILL.md), script, asset, data_config, license (LICENSE*/NOTICE*), other — definitions are in the schema. Filenames starting with LICENSE go to license even if they end in .txt/.md. total = sum of buckets. Do NOT copy counts from anywhere; count yourself.

3. DESCRIBE the extra markdown files (md_roles) and the non-md files (nonmd_summary) briefly, based on filenames/directories and a quick peek where needed. Rate the SKILL.md depth (skill_md_quality).

Return via the structured output tool.`,
  { label: `audit:batch${i}`, phase: 'Audit', schema: SCHEMA }
)))

const all = results.filter(Boolean).flatMap(r => r.skills)
log(`audited ${all.length} skills`)
return { skills: all }
