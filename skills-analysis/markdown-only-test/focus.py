#!/usr/bin/env python3
"""Finance / legal / HR / operations focus set: 50-skill sample + census of those domains.

For every skill it records, beyond the plain file counts:
  - an exclusive file-role breakdown: md, template, script, asset, data, packaging, license, other
  - code embedded in the markdown (fenced blocks by language) and whether it must be executed
  - files the markdown points to that are NOT in the folder (e.g. a stripped example .xlsx)
  - references outside the folder (../ paths, plugin-level CLAUDE.md / CONNECTORS.md)
  - dependencies on file-producing skills (xlsx/docx/pptx/pdf) or Office output
Writes focus_census.json, focus_sample.json, focus_sample.tsv.
"""
import contextlib, io, json, os, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {"__file__": os.path.join(HERE, "sample_and_stats.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(ns["__file__"]).read(), ns)
import sys
sys.path.insert(0, HERE)
import inventory as inv

DOMAINS = {  # focus group -> classifier domains
    "Finance & accounting": ["finance-accounting"],
    "Investing & banking": ["investing-banking-pe"],
    "Legal & compliance": ["legal-compliance"],
    "HR & people": ["hr-people"],
    "Operations": ["operations-admin"],
}
QUOTA = {"Finance & accounting": 10, "Investing & banking": 12, "Legal & compliance": 14, "HR & people": 7, "Operations": 7}
REPO_CAP = 4  # per domain, keeps one big repo (e.g. claude-for-legal) from filling a domain

TEMPLATE_EXT = {".docx", ".xlsx", ".xlsm", ".xltx", ".pptx", ".potx", ".dotx", ".j2", ".jinja", ".jinja2", ".tmpl", ".hbs", ".mustache"}
TEMPLATE_RE = re.compile(r"template|boilerplate|skeleton|starter", re.I)
EXEC_LANGS = {"python", "py", "bash", "sh", "shell", "zsh", "console", "javascript", "js", "typescript", "ts",
              "sql", "r", "powershell", "ps1", "vba", "excel", "applescript", "node", "mjs"}
FENCE = re.compile(r"^```+\s*([A-Za-z0-9_+-]*)", re.M)
REF = re.compile(r"(?<![\w/.-])((?:\./)?(?:[\w.-]+/)*[\w.-]+\.(?:py|js|mjs|ts|sh|sql|json|ya?ml|csv|tsv|xml|xsd|xlsx|xlsm|docx|pptx|pdf|html|css|j2|txt|md|png|svg|jpg|ttf))(?![\w])")
OUTSIDE = re.compile(r"\.\./|\bCLAUDE\.md\b|\bCONNECTORS\.md\b|practice profile|plugin[- ]level", re.I)
OFFICE_OUT = re.compile(r"\.(xlsx|docx|pptx)\b|\bexcel\b|\bword document\b|\bpowerpoint\b|\bdeck\b|\bworkbook\b|\bpdf\b", re.I)
SKILL_DEP = re.compile(r"\b(xlsx|docx|pptx|pdf)[- ](author|skill)\b|\bthe (xlsx|docx|pptx|pdf) skill\b|\b(audit-xls|clean-data-xls|xlsx-author|pptx-author|ppt-template-creator)\b", re.I)
RUNS_CODE = re.compile(r"\b(run|execute|python3?|bash|node|openpyxl|pandas|python-docx|pip install|npm)\b", re.I)


def role(rel):
    name = os.path.basename(rel)
    low = name.lower()
    ext = os.path.splitext(low)[1]
    if rel.startswith("agents" + os.sep) or low == "maintainers.yml" or low.endswith(".sig") or low.startswith("icon"):
        return "packaging"
    c = inv.category(name)
    if c == "license":
        return "license"
    if c in ("skill_md", "md"):
        return "md"
    if ext in TEMPLATE_EXT or TEMPLATE_RE.search(rel):
        return "template"
    return {"script": "script", "asset": "asset", "data_config": "data"}.get(c, "other")


def analyse(x):
    root = os.path.join(HERE, "repos", x["repo"].replace("/", "__"), x["path"])
    files = []
    for dp, dns, fns in os.walk(root):
        # stop at nested skills
        dns[:] = [d for d in dns if not os.path.exists(os.path.join(dp, d, "SKILL.md")) and d not in (".git", "node_modules")]
        for fn in fns:
            files.append(os.path.relpath(os.path.join(dp, fn), root))
    roles = Counter(role(f) for f in files)
    md_text = ""
    md_templates = 0
    for f in files:
        if f.lower().endswith((".md", ".mdx")):
            md_text += "\n" + open(os.path.join(root, f), errors="replace").read()
            if TEMPLATE_RE.search(f):
                md_templates += 1
    langs = Counter(m.group(1).lower() for m in FENCE.finditer(md_text) if m.group(1))
    # fences come in pairs; opening fences carry the language
    exec_blocks = sum(v for k, v in langs.items() if k in EXEC_LANGS)
    present = set(files) | {os.path.basename(f) for f in files}
    missing = sorted({r for r in (m.group(1).lstrip("./") for m in REF.finditer(md_text))
                      if "/" in r and not r.startswith(("http", "www")) and r not in present
                      and not r.startswith(("out/", "output/", "./out", "tmp/")) and "<" not in r
                      and not os.path.exists(os.path.join(root, r))})
    skill_md = open(os.path.join(root, "SKILL.md"), errors="replace").read()
    return {
        "roles": dict(roles),
        "files": len(files),
        "md_templates": md_templates,
        "code_blocks": exec_blocks,
        "code_langs": {k: v for k, v in langs.items() if k in EXEC_LANGS},
        "missing_refs": missing[:12],
        "refs_outside": bool(OUTSIDE.search(skill_md)),
        "office_output": bool(OFFICE_OUT.search(skill_md)),
        "skill_deps": sorted({m.group(0).lower() for m in SKILL_DEP.finditer(md_text)}),
        "runs_code": bool(RUNS_CODE.search(md_text)) and exec_blocks > 0,
        "ui_ok": len(files) <= 20 and roles.get("md", 0) == len(files),
    }


eligible = ns["eligible"]
group_of = {d: g for g, ds in DOMAINS.items() for d in ds}
census = []
for x in eligible:
    g = group_of.get(x["label"]["domain"])
    if g:
        census.append({**x, "group": g, "focus": analyse(x)})

sample = []
for g, q in QUOTA.items():
    items = sorted([x for x in census if x["group"] == g], key=lambda x: x["skill_md_sha"])
    per_repo = defaultdict(int)
    picked = []
    for x in items:  # hash order, capped per repo
        if len(picked) >= q:
            break
        if per_repo[x["repo"]] >= REPO_CAP:
            continue
        per_repo[x["repo"]] += 1
        picked.append(x)
    for x in items:  # top up if the cap left the quota short
        if len(picked) >= q:
            break
        if x not in picked:
            picked.append(x)
    sample.extend(picked)

json.dump(census, open(os.path.join(HERE, "focus_census.json"), "w"), indent=1)
json.dump(sample, open(os.path.join(HERE, "focus_sample.json"), "w"), indent=1)
root = os.path.join(HERE, "repos")
with open(os.path.join(HERE, "focus_sample.tsv"), "w") as fh:
    fh.write("id\tgroup\tpublisher\trepo\tname\tskill_dir_abs_path\n")
    for x in sample:
        fh.write(f"{x['id']}\t{x['group']}\t{x['publisher']}\t{x['repo']}\t{x['name']}\t{root}/{x['repo'].replace('/', '__')}/{x['path']}\n")

print(f"census {len(census)} skills; sample {len(sample)}")
for g in QUOTA:
    xs = [x for x in census if x["group"] == g]
    s = [x for x in sample if x["group"] == g]
    print(f"  {g:22s} census {len(xs):3d}  sample {len(s):2d}  repos {Counter(x['repo'] for x in s).most_common()}")
