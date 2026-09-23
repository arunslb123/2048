export const meta = {
  name: 'verify-skill-sample',
  description: 'Audit 4 replacement candidates and run an adversarial critic over the method, sample and headline claims',
  phases: [{ title: 'Verify', detail: 'replacement audit + methodology critic' }],
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

const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    issues: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          issue: { type: 'string' },
          evidence: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'issue', 'evidence', 'fix'],
      },
    },
    spot_checks: { type: 'array', items: { type: 'object', properties: { skill: { type: 'string' }, csv_md: { type: 'integer' }, your_md: { type: 'integer' }, csv_total: { type: 'integer' }, your_total: { type: 'integer' } }, required: ['skill', 'csv_md', 'your_md', 'csv_total', 'your_total'] } },
    claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, detail: { type: 'string' } }, required: ['claim', 'holds', 'detail'] } },
  },
  required: ['issues', 'spot_checks', 'claims_checked'],
}

const [aud, critic] = await parallel([
  () => agent(
`Audit Agent Skills for a study of real knowledge-work skills. Read ${SP}/audit/batch5.tsv (columns: id, publisher, repo, name, skill_dir_abs_path). For EVERY row:
1. verdict keep/reject: keep = real, production-intended skill that helps a knowledge worker do actual work (finance, legal, sales, marketing, HR, ops, support, PM, research, docs, communication, analytics, design). reject = not knowledge work, toy/demo/template, stub too thin, mainly API reference/router, or setup/onboarding/auth helper. Read the whole SKILL.md.
2. Independently count files: find "<dir>" -type f (exclude .git, node_modules, and any subdirectory that has its own SKILL.md). Buckets: md (.md/.mdx incl SKILL.md), script (code), asset (images, fonts, office/pdf, html/css, media), data_config (json/yaml/csv/xml/xsd/txt...), license (LICENSE*/NOTICE*), other. total = sum.
3. md_roles (<=15 words on extra md files, 'none' if SKILL.md only), nonmd_summary (<=20 words, 'none' if none), skill_md_quality.`,
    { label: 'audit:replacements', phase: 'Verify', schema: AUDIT_SCHEMA }),
  () => agent(
`You are an adversarial reviewer of a small empirical study. Your job is to find what is WRONG or MISLEADING before it is reported to a user.

User's request: "Look into skills shared by OpenAI and Anthropic etc and let me know how many md files on average in each skills folder, and give me a distribution of md files, assets, scripts etc in the skills folder. I'm looking for real projects not toy examples. For knowledge work. Aim for 100 skills and use that as a sample."

Materials (all under ${SP}):
- methodology.md (read first)
- final_stats.json — stats for the final sample (98 skills now; 2 more pending from a replacement audit), per publisher, per domain, the eligible population (~1,000 knowledge-work task skills), and all skills.
- final_sample.csv — one row per sampled skill with counts.
- inventory.json — every skill folder found (2,810 incl. duplicates), with counts. repos/ — the cloned repos. labels_main.json/labels_add.json — classifier labels (ids map via pool.json/pool_add.json). audit.json — audit results.

Do ALL of the following:
1. Spot-check at least 10 rows of final_sample.csv (pick varied ones, include the largest by files_total) by recounting md files and total files yourself with find in repos/<owner>__<repo>/<path>. Report them in spot_checks.
2. Check these draft headline claims against the data and report each in claims_checked (holds true/false + detail with numbers):
   a. "Average md files per knowledge-work skill folder is ~3 (mean) but the median is 1 — most skills are a single SKILL.md."
   b. "Anthropic's knowledge-work skills are overwhelmingly SKILL.md-only (~75-80%), while OpenAI's almost always ship extra files (at least agents/openai.yaml)."
   c. "Scripts appear in roughly 1 in 4-5 knowledge-work skills; true binary/visual assets (templates, images, fonts) are rare (<5% of skills) once OpenAI UI icons are excluded."
   d. "When skills do add files, markdown reference docs (references/ folder) are the most common addition."
   e. "The sample is representative of the eligible population on md mean/median and SKILL.md-only share." (compare sample vs eligible_population, overall and per publisher)
3. Look for methodological problems: sampling bias (quotas vs population sizes, per-plugin cap, dedup choices), misclassification of knowledge-work vs dev (open a handful of eligible and excluded SKILL.md files to test the labels), category-bucket definitions that could mislead (e.g. .xsd schemas as data, html as asset, packaging split), outliers driving means, and any major official source that is missing. Also: are there skills where 'md files' include things that aren't really skill content (README.md, CHANGELOG)?
Report issues with severity (high = would change a headline number or conclusion). Be concrete and quantitative. Don't pad with generic advice.`,
    { label: 'critic:method', phase: 'Verify', schema: CRITIC_SCHEMA }),
])

return { audit: aud, critic }
