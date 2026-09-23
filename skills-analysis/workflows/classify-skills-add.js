export const meta = {
  name: 'classify-skills-add',
  description: 'Label 605 added candidate skills as knowledge-work vs not, and real vs toy/meta, in 6 parallel batches',
  phases: [{ title: 'Classify', detail: '3 agents x ~200 skills each' }],
}

const DOMAINS = ['finance-accounting','investing-banking-pe','legal-compliance','sales-crm','marketing-content','hr-people','operations-admin','customer-support','product-management','docs-office-files','productivity-communication','data-analytics-bi','science-research','design-creative-media','software-dev-devops','other']
const ROLES = ['task','reference-or-router','setup-auth','meta-authoring','example-or-template']

const SCHEMA = {
  type: 'object',
  properties: {
    labels: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          knowledge_work: { type: 'boolean', description: 'true if the skill helps a non-developer knowledge worker (analyst, lawyer, marketer, recruiter, researcher, PM, ops, support, exec) do their job or produce business documents. false for software engineering, devops, SDK/API integration coding, app building.' },
          domain: { type: 'string', enum: DOMAINS },
          role: { type: 'string', enum: ROLES, description: 'task = does real end-user work; reference-or-router = mainly API/CLI reference or dispatches to other skills; setup-auth = install/login/config helper; meta-authoring = creates skills/plugins; example-or-template = demo, sample, template, toy' },
          real: { type: 'boolean', description: 'true if production-grade and intended for real use (substantive instructions, not a stub/demo/placeholder)' },
          note: { type: 'string', description: '<=12 words, only if label is non-obvious' },
        },
        required: ['id','knowledge_work','domain','role','real'],
      },
    },
  },
  required: ['labels'],
}

const chunks = args.chunks
const results = await parallel(chunks.map(i => () => agent(
`You are labelling Agent Skills (folders with a SKILL.md) for a study of REAL KNOWLEDGE-WORK skills published by Anthropic, OpenAI and others.

Read the TSV file /tmp/claude-0/-home-user-2048/52a1ea60-b7a7-54b2-835a-a72ec8f4e1e5/scratchpad/chunks/chunk${i}.tsv (columns: id, repo, plugin, name, skill_dir_abs_path, description). Label EVERY row (return exactly one label per id, no omissions).

Guidance:
- knowledge_work=true: helps a non-developer professional do business/research work: finance/accounting models, equity research, PE/IB deliverables, legal review, sales prospecting/CRM, marketing/copy/SEO strategy, HR/recruiting, ops/procurement, customer support, product management (PRDs, roadmaps, research synthesis), creating/editing docx/pptx/xlsx/pdf, email/calendar/meetings/notes/knowledge capture, business data analysis & dashboards, scientific/literature research and lab-data analysis done by a scientist, design/brand/creative work done by a designer or marketer.
- knowledge_work=false: software engineering, app/website building, SDK/API integration code, devops/deploy/CI, security of code, agent/plugin tooling. Scientific skills that are just a Python library's API reference for programmers (e.g. 'how to use library X') lean false unless clearly aimed at a researcher's analysis workflow; use judgement and put a short note.
- role: see schema. A Google Workspace CLI per-API reference (e.g. gws-drive) is 'reference-or-router'; a gws 'recipe'/'persona' doing a user task is 'task'. Auth/install helpers are 'setup-auth'. skill-creator / plugin-creator are 'meta-authoring'.
- real=false for stubs, placeholders, demos, samples, templates, 'hello world', or skills whose SKILL.md is clearly a toy. When the description alone is ambiguous, open the SKILL.md at skill_dir_abs_path (head -60 is enough). Don't open every file — only ambiguous ones.

Return the labels via the structured output tool.`,
  { label: `classify:chunk${i}`, phase: 'Classify', schema: SCHEMA }
)))

const all = results.filter(Boolean).flatMap(r => r.labels)
log(`labelled ${all.length} skills`)
return { labels: all }
