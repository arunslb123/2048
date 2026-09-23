export const meta = {
  name: 'audit-new-picks',
  description: 'Audit the 12 skills newly drawn after fixing dedup, labels and strata',
  phases: [{ title: 'Audit', detail: '1 agent, 12 skills' }],
}
const SP = '/tmp/claude-0/-home-user-2048/52a1ea60-b7a7-54b2-835a-a72ec8f4e1e5/scratchpad'
const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    skills: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['keep', 'reject'] },
          reject_reason: { type: 'string' },
          md: { type: 'integer' }, script: { type: 'integer' }, asset: { type: 'integer' },
          data_config: { type: 'integer' }, license: { type: 'integer' }, other: { type: 'integer' }, total: { type: 'integer' },
          md_roles: { type: 'string' }, nonmd_summary: { type: 'string' },
          skill_md_quality: { type: 'string', enum: ['substantive', 'moderate', 'thin'] },
        },
        required: ['id', 'verdict', 'md', 'script', 'asset', 'data_config', 'license', 'other', 'total', 'md_roles', 'nonmd_summary', 'skill_md_quality'],
      },
    },
  },
  required: ['skills'],
}
const res = await agent(
`Audit Agent Skills for a study of real knowledge-work skills. Read ${SP}/audit/batch6.tsv (columns: id, publisher, repo, name, skill_dir_abs_path). For EVERY row:
1. verdict keep/reject: keep = real, production-intended skill that helps a knowledge worker do actual work (finance, legal, sales, marketing, HR, ops, support, PM, research/science incl. querying scientific databases, docs, communication, analytics, design). reject = not knowledge work, toy/demo/template, stub too thin, mainly a router to other skills, or setup/onboarding/auth helper. A wrapper over a vendor tool or public API is fine if it performs a user task. Read the whole SKILL.md.
2. Independently count files: find "<dir>" -type f (exclude .git, node_modules, and any subdirectory that has its own SKILL.md). Buckets: md (.md/.mdx incl SKILL.md), script (code incl. .html/.css), asset (images, fonts, office/pdf, media), data_config (json/yaml/csv/xml/xsd/txt...), license (LICENSE*/NOTICE*), other. total = sum.
3. md_roles (<=15 words on extra md files, 'none' if SKILL.md only), nonmd_summary (<=20 words, 'none' if none), skill_md_quality (substantive/moderate/thin).`,
  { label: 'audit:new-picks', phase: 'Audit', schema: AUDIT_SCHEMA })
return res
