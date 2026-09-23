export const meta = {
  name: 'skill-structure-guidance',
  description: 'Research official Anthropic/OpenAI guidance on skill folder contents, verify quotes, and classify why real skills ship non-markdown files',
  phases: [
    { title: 'Research', detail: 'official docs (Anthropic, OpenAI) + why non-md files exist' },
    { title: 'Verify', detail: 'independent re-check of every quote and URL' },
  ],
}

const SP = '/tmp/claude-0/-home-user-2048/52a1ea60-b7a7-54b2-835a-a72ec8f4e1e5/scratchpad'

const GUIDE_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          topic: { type: 'string', enum: ['file-count-or-size-limit', 'skill-md-length', 'reference-files', 'scripts', 'assets-templates', 'folder-structure', 'other'] },
          quote: { type: 'string', description: 'verbatim text from the source, <= 60 words' },
          source_title: { type: 'string' },
          url: { type: 'string', description: 'public URL (or repo path like github.com/anthropics/skills/blob/main/...)' },
          takeaway: { type: 'string', description: '<= 20 words: what it implies for a "max 20 files, markdown only" rule' },
        },
        required: ['topic', 'quote', 'source_title', 'url', 'takeaway'],
      },
    },
    no_limit_found: { type: 'string', description: 'State explicitly whether any official hard limit on number of files in a skill folder exists, and any size limits found' },
  },
  required: ['findings', 'no_limit_found'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer' },
          verdict: { type: 'string', enum: ['verbatim', 'paraphrase-accurate', 'inaccurate', 'not-found'] },
          corrected_quote: { type: 'string', description: 'exact text as it appears at the source, if different' },
          correct_url: { type: 'string' },
          note: { type: 'string' },
        },
        required: ['index', 'verdict'],
      },
    },
    limit_claim_verdict: { type: 'string' },
  },
  required: ['checks', 'limit_claim_verdict'],
}

const PURPOSE_SCHEMA = {
  type: 'object',
  properties: {
    skills: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          skill: { type: 'string' },
          publisher: { type: 'string' },
          nonmd_files: { type: 'integer' },
          purposes: { type: 'array', items: { type: 'string', enum: ['deterministic-calculation', 'validation-qa', 'file-format-manipulation', 'api-or-data-client', 'schema-or-spec', 'lookup-data-or-taxonomy', 'output-template', 'fonts-images-media', 'ui-packaging-metadata', 'tests', 'other'] } },
          could_be_markdown: { type: 'string', enum: ['no', 'partly', 'yes'], description: 'Could the same job be done by markdown instructions alone without losing reliability?' },
          why: { type: 'string', description: '<= 25 words, concrete' },
        },
        required: ['skill', 'publisher', 'nonmd_files', 'purposes', 'could_be_markdown', 'why'],
      },
    },
  },
  required: ['skills'],
}

const SOURCES = {
  anthropic: `Anthropic / Claude: the Agent Skills docs on docs.claude.com or platform.claude.com (overview, "Skill authoring best practices", Skills API / upload limits), Claude Code skills docs (code.claude.com/docs), the open spec at agentskills.io, the anthropics/skills repo README and its skill-creator SKILL.md (local clone: ${SP}/repos/anthropics__skills/skills/skill-creator/SKILL.md), and Anthropic engineering blog posts on Agent Skills.`,
  openai: `OpenAI: Codex skills docs (developers.openai.com/codex/skills or similar), the openai/skills repo README and its .system/skill-creator SKILL.md (local clone: ${SP}/repos/openai__skills/skills/.system/skill-creator/SKILL.md), the openai/plugins README (${SP}/repos/openai__plugins/README.md), and any OpenAI docs on ChatGPT skills.`,
}

function researchPrompt(who) {
  return `A team is proposing an internal rule for Agent Skills (folders with a SKILL.md): "max 20 files per skill folder, and all files must be markdown". Find what OFFICIAL guidance from ${who === 'anthropic' ? 'Anthropic' : 'OpenAI'} says about what belongs in a skill folder.

Sources to use: ${SOURCES[who]}
Use WebSearch/WebFetch (load via ToolSearch) and the local clones. Prefer primary sources. Capture VERBATIM quotes (<=60 words each) with exact URLs about: any limits on number of files or total size, SKILL.md length guidance, reference/markdown files and progressive disclosure, bundling scripts (when and why), assets/templates, and recommended folder structure. 6-12 findings. Do not invent quotes; if you only have a paraphrase, say so in the quote field by prefixing "PARAPHRASE:". Also state clearly whether any official hard limit on file COUNT exists.`
}

function verifyPrompt(who, res) {
  const list = res.findings.map((f, i) => `[${i}] (${f.url}) "${f.quote}"`).join('\n')
  return `Adversarially verify these quotes attributed to official ${who === 'anthropic' ? 'Anthropic' : 'OpenAI'} sources about Agent Skills. For each, fetch the URL (WebFetch via ToolSearch; for github.com repo files you may read the local clone under ${SP}/repos/<owner>__<repo>/ instead) and check the text really appears there. Verdict: verbatim / paraphrase-accurate / inaccurate / not-found. If the text lives at a different URL, give correct_url. Default to not-found if you cannot locate it.

${list}

Also verify this claim about limits: "${res.no_limit_found}"`
}

phase('Research')
const [anth, oai, purposes] = await parallel([
  () => agent(researchPrompt('anthropic'), { label: 'research:anthropic-docs', phase: 'Research', schema: GUIDE_SCHEMA }),
  () => agent(researchPrompt('openai'), { label: 'research:openai-docs', phase: 'Research', schema: GUIDE_SCHEMA }),
  () => agent(
`Real knowledge-work Agent Skills often ship non-markdown files. A team wants to ban them ("all markdown, max 20 files"). Explain WHY publishers include them, with evidence.

Read ${SP}/nonmd_targets.tsv (columns: publisher, repo, name, skill_dir_abs_path, files_total, md, nonmd). It lists ~36 real knowledge-work skills that contain non-markdown content files, spread across publishers. For EACH row: list the non-md files (find), open the scripts/data files enough to see what they do, and read the parts of SKILL.md that reference them. Classify the purposes (schema enum), judge whether markdown alone could do the same job reliably (could_be_markdown), and give a concrete why (e.g. "recalc.py recomputes Excel formulas via LibreOffice so the model can verify numbers; markdown can't execute").`,
    { label: 'research:why-non-md', phase: 'Research', schema: PURPOSE_SCHEMA }),
])

phase('Verify')
const [vA, vO] = await parallel([
  () => anth ? agent(verifyPrompt('anthropic', anth), { label: 'verify:anthropic-quotes', phase: 'Verify', schema: VERIFY_SCHEMA }) : null,
  () => oai ? agent(verifyPrompt('openai', oai), { label: 'verify:openai-quotes', phase: 'Verify', schema: VERIFY_SCHEMA }) : null,
])

return { anthropic: anth, openai: oai, verify_anthropic: vA, verify_openai: vO, purposes }
