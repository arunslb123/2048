#!/usr/bin/env python3
"""Build report.html (the published page) from final_sample.json / final_stats.json."""
import contextlib, io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {"__file__": os.path.join(HERE, "sample_and_stats.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(ns["__file__"]).read(), ns)
cat_counts = ns["cat_counts"]

final = json.load(open(os.path.join(HERE, "final_sample.json")))
stats = json.load(open(os.path.join(HERE, "final_stats.json")))
eligible = ns["eligible"]
audit = {}
for f in ("audit.json", "audit5.json", "audit6.json"):
    for a in json.load(open(os.path.join(HERE, f))):
        audit[a["id"]] = a
pool_by_id = {x["id"]: x for x in ns["pool"]}
mismatch = 0
for i, a in audit.items():
    x = pool_by_id[i]; c = x["counts"]
    if (x["md_total"], x["files_total"], c["script"] + c["asset"], c["data_config"], c["license"]) != \
            (a["md"], a["total"], a["script"] + a["asset"], a["data_config"], a["license"]):
        mismatch += 1
non_google = [i for i in audit if pool_by_id[i]["repo"] != "googleworkspace/cli"]
PUBS = ["Anthropic", "OpenAI", "Other vendors", "Community"]


def shape(x):
    cc = cat_counts(x)
    if cc["script"]:
        return "scripts"
    if cc["asset"] or cc["data_config"] or cc["other"]:
        return "data"
    if cc["md_total"] > 1:
        return "md"
    return "solo"


def shapes(xs):
    out = {"solo": 0, "md": 0, "scripts": 0, "data": 0}
    for x in xs:
        out[shape(x)] += 1
    return {"n": len(xs), **out}


def pub_rows(xs):
    return [{"label": p, **shapes([x for x in xs if x["publisher"] == p])} for p in PUBS] + \
           [{"label": "All", **shapes(xs)}]


def pub_table(block):
    rows = []
    for p in PUBS + ["All"]:
        d = block["all"] if p == "All" else block[p]
        pc = d["per_category"]
        rows.append({"label": p, "n": d["n"], "md_mean": d["md_mean"], "md_median": d["md_median"],
                     "md_p90": d["md_p90"], "solo_pct": d["skill_md_only_content_pct"],
                     "extra_md_pct": d["pct_with_reference_md_beyond_skill_md"],
                     "script_pct": pc["script"]["pct_skills_with_any"],
                     "data_pct": pc["data_config"]["pct_skills_with_any"],
                     "asset_pct": pc["asset"]["pct_skills_with_any"],
                     "pack_pct": pc["packaging"]["pct_skills_with_any"],
                     "content_mean": d["content_files_mean"], "content_median": d["content_files_median"]})
    return rows


rows = []
for x in sorted(final, key=lambda x: (PUBS.index(x["publisher"]), x["repo"], x["plugin"], x["name"])):
    cc = cat_counts(x)
    rows.append({"pub": x["publisher"], "repo": x["repo"], "plugin": x["plugin"], "name": x["name"],
                 "domain": x["label"]["domain"], "md": cc["md_total"], "script": cc["script"],
                 "asset": cc["asset"], "data": cc["data_config"], "pack": cc["packaging"],
                 "lic": cc["license"], "total": x["files_total"], "lines": x["skill_md_lines"],
                 "quality": x["audit"]["skill_md_quality"], "md_roles": x["audit"]["md_roles"],
                 "nonmd": x["audit"]["nonmd_summary"],
                 "url": f"https://github.com/{x['repo']}/tree/HEAD/{x['path']}"})

s = stats["sample"]
data = {
    "n": stats["n"],
    "md_hist": s["md_histogram"],
    "md_mean": s["md_mean"], "md_median": s["md_median"], "md_p90": s["md_p90"], "md_max": s["md_max"],
    "solo_pct": s["skill_md_only_content_pct"],
    "contains": [
        {"k": "More markdown (beyond SKILL.md)", "v": s["pct_with_reference_md_beyond_skill_md"]},
        {"k": "OpenAI UI packaging (openai.yaml + icons)", "v": s["per_category"]["packaging"]["pct_skills_with_any"]},
        {"k": "Scripts & code (incl. HTML/CSS)", "v": s["per_category"]["script"]["pct_skills_with_any"]},
        {"k": "Data & config (JSON, YAML, CSV, XSD)", "v": s["per_category"]["data_config"]["pct_skills_with_any"]},
        {"k": "License file", "v": s["per_category"]["license"]["pct_skills_with_any"]},
        {"k": "Binary assets (images, fonts, Office/PDF)", "v": s["per_category"]["asset"]["pct_skills_with_any"]},
    ],
    "share": {k: s["per_category"][k]["share_of_all_files_pct"] for k in s["per_category"]},
    "means": {k: s["per_category"][k]["mean_per_skill"] for k in s["per_category"]},
    "shapes_sample": pub_rows(final),
    "shapes_pop": pub_rows(eligible),
    "pub_sample": pub_table({**stats["sample_by_publisher"], "all": stats["sample"]}),
    "pub_pop": pub_table({**stats["eligible_by_publisher"], "all": stats["eligible_population"]}),
    "all_skills": {"n": stats["all_skills"]["n"], "md_mean": stats["all_skills"]["md_mean"],
                   "md_median": stats["all_skills"]["md_median"]},
    "eligible_n": stats["eligible_population"]["n"],
    "subdirs": s["subdir_pct"],
    "rows": rows,
    "quality": stats["quality"],
    "robust": stats["robust"],
    "audited": len(audit), "audit_mismatch": mismatch,
    "audit_rejected": sum(a["verdict"] == "reject" for a in audit.values()),
    "audited_non_google": len(non_google),
    "audit_rejected_non_google": sum(audit[i]["verdict"] == "reject" for i in non_google),
    "replacements": len(stats["replacements"]),
}

def tree(x, limit=14):
    """Render a skill folder as an ASCII tree (files only, dirs implied)."""
    root = os.path.join(HERE, "repos", x["repo"].replace("/", "__"), x["path"])
    files = []
    for dp, dns, fns in os.walk(root):
        dns.sort()
        for fn in sorted(fns):
            files.append(os.path.relpath(os.path.join(dp, fn), root))
    files.sort(key=lambda p: (p.count(os.sep) > 0, p.lower()))
    lines, seen_dirs = [], set()
    shown = files[:limit]
    for i, p in enumerate(shown):
        parts = p.split(os.sep)
        for d in range(len(parts) - 1):
            key = os.sep.join(parts[: d + 1])
            if key not in seen_dirs:
                seen_dirs.add(key)
                lines.append({"t": "  " * d + parts[d] + "/", "k": "dir"})
        name = parts[-1]
        lines.append({"t": "  " * (len(parts) - 1) + name, "k": kind_of(p, x)})
    if len(files) > limit:
        lines.append({"t": f"… {len(files) - limit} more files", "k": "more"})
    return lines


def kind_of(rel, x):
    import inventory as inv
    name = os.path.basename(rel)
    if rel.startswith("agents" + os.sep) or name.startswith(("icon",)) or name.endswith(".sig"):
        return "pack"
    c = inv.category(name)
    return {"skill_md": "md", "md": "md", "script": "script", "asset": "asset",
            "data_config": "data", "license": "lic"}.get(c, "other")


import sys
sys.path.insert(0, HERE)
by_name = {(x["repo"], x["name"]): x for x in final}
ARCH = [
    ("anthropics/claude-for-legal", "nda-review", "SKILL.md only", "The most common shape. One file carries the whole workflow: scope, checklist, escalation rules, output format."),
    ("anthropics/knowledge-work-plugins", "proposal-builder", "Markdown only", "SKILL.md routes to a reference/ folder of focused .md files that load on demand (progressive disclosure)."),
    ("zapier/gtm-cheat-codes", "customer-deck-builder", "Markdown + data", "Reference docs plus a structured data file (JSON/YAML/CSV), with no executable code."),
    ("openai/plugins", "financials-normalizer", "Markdown + scripts", "References, validation scripts and a lookup CSV, plus Codex UI packaging (agents/openai.yaml, icon)."),
]
archetypes = []
for repo, name, title, blurb in ARCH:
    x = by_name.get((repo, name))
    if x:
        archetypes.append({"title": title, "blurb": blurb, "name": x["name"], "repo": repo,
                           "pub": x["publisher"], "tree": tree(x), "files": x["files_total"],
                           "url": f"https://github.com/{repo}/tree/HEAD/{x['path']}"})
data["archetypes"] = archetypes

# ---- "max 20 files, markdown only" rule check ----------------------------------------
content_files = ns["content_files"]
CAP = 20


def rule(xs):
    n = len(xs)
    multi = [x for x in xs if content_files(x) > 1]
    return {
        "n": n,
        "le_cap_pct": round(100 * sum(x["files_total"] <= CAP for x in xs) / n, 1),
        "over_cap": sum(x["files_total"] > CAP for x in xs),
        "md_only_pct": round(100 * sum(content_files(x) == x["md_total"] for x in xs) / n, 1),
        "md_only_strict_pct": round(100 * sum(x["files_total"] == x["md_total"] for x in xs) / n, 1),
        "both_pct": round(100 * sum(content_files(x) <= CAP and content_files(x) == x["md_total"] for x in xs) / n, 1),
        "multi_n": len(multi),
        "multi_md_only_pct": round(100 * sum(content_files(x) == x["md_total"] for x in multi) / max(1, len(multi)), 1),
        "md_over_cap": sum(x["md_total"] > CAP for x in xs),
    }


def pctl(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, max(0, -(-int(q * len(v) * 1000) // 1000) - 1))]


fbins = [(1, 1, "1"), (2, 5, "2–5"), (6, 10, "6–10"), (11, 20, "11–20"), (21, 50, "21–50"), (51, 10**9, "51+")]
nonmd = [x for x in eligible if content_files(x) > x["md_total"]]
breaks = {"scripts": sum(cat_counts(x)["script"] > 0 for x in nonmd),
          "data_only": sum(cat_counts(x)["script"] == 0 and cat_counts(x)["asset"] == 0 and cat_counts(x)["data_config"] > 0 for x in nonmd),
          "assets": sum(cat_counts(x)["asset"] > 0 for x in nonmd), "n": len(nonmd)}
over = []
for x in sorted([x for x in eligible if x["files_total"] > CAP], key=lambda x: -x["files_total"]):
    c = cat_counts(x)
    over.append({"name": x["name"], "repo": x["repo"], "pub": x["publisher"], "files": x["files_total"],
                 "md": x["md_total"], "script": c["script"], "data": c["data_config"], "asset": c["asset"],
                 "url": f"https://github.com/{x['repo']}/tree/HEAD/{x['path']}"})
g = json.load(open(os.path.join(HERE, "guidance.json")))
purposes = g["purposes"]["skills"]
from collections import Counter as _C
pc = _C(p for sk in purposes for p in sk["purposes"] if p not in ("other",))
PLABEL = {"validation-qa": "Validate or QA the output", "deterministic-calculation": "Exact calculations",
          "output-template": "Output templates", "schema-or-spec": "Schemas and specs",
          "api-or-data-client": "Call an API or fetch data", "file-format-manipulation": "Edit Office/PDF/XML files",
          "tests": "Tests and eval sets", "lookup-data-or-taxonomy": "Lookup tables and taxonomies",
          "fonts-images-media": "Fonts, images, media", "ui-packaging-metadata": "UI / catalog metadata"}
# Quotes: text re-verified word for word against the live sources by an independent agent
# (guidance.json -> verify_*); ellipses mark omitted text, order follows the source page.
QUOTES = [
    ("Anthropic", "A Skill can include dozens of reference files, but if your task only needs the sales schema, that's the one file Claude loads. … No practical limit on bundled content: Files don't consume context until accessed, so Skills can include comprehensive API documentation, large datasets, or extensive examples.",
     "Claude docs · Agent Skills overview", "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview",
     "Anthropic expects many files in a skill and sets no count limit."),
    ("Anthropic", "A skill directory may contain any files and directories beyond the required SKILL.md.",
     "Agent Skills specification (agentskills.io)", "https://agentskills.io/specification",
     "The open standard both labs follow allows any file type."),
    ("Anthropic", "Even if Claude could write a script, pre-made scripts offer advantages: … More reliable than generated code … Ensure consistency across uses … Prefer scripts for deterministic operations: Write validate_form.py rather than asking Claude to generate validation code",
     "Claude docs · Skill authoring best practices", "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices",
     "Scripts are the recommended pattern for anything that must be exact."),
    ("Anthropic", "Keep SKILL.md body under 500 lines for optimal performance. If your content exceeds this, split it into separate files using the progressive disclosure patterns described earlier.",
     "Claude docs · Skill authoring best practices", "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices",
     "The limit that matters is SKILL.md length. Overflow goes into more files, not fewer."),
    ("Anthropic", "Maximum Skill upload size: 30 MB (all files combined, uncompressed)",
     "Claude docs · Skills API guide, limits", "https://platform.claude.com/docs/en/build-with-claude/skills-guide",
     "The only hard limit is on total size, not file count."),
    ("OpenAI", "Instruction-only is the default. … Prefer instructions over scripts unless you need deterministic behavior or external tooling.",
     "ChatGPT docs · Build skills", "https://learn.chatgpt.com/docs/build-skills",
     "Markdown-first is endorsed, with an explicit exception for exact or tool-driven work."),
    ("OpenAI", "Use references/ for policies, schemas, examples, and background material. Use assets/ for templates or files the workflow should copy or transform. Use scripts/ when the workflow needs deterministic computation or file processing. … Do not add a script when instructions and existing tools can complete the task reliably.",
     "OpenAI Plugins docs · Build skills", "https://developers.openai.com/plugins/build/skills",
     "Scripts and assets have defined roles. Add them when needed, not by default."),
    ("OpenAI", "Maximum file count per skill version is 500.",
     "OpenAI API docs · Skills guide, limits", "https://developers.openai.com/api/docs/guides/tools-skills",
     "Hard caps exist, but at 500 files (100 for MCP-imported skills), far above 20."),
    ("OpenAI", "A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files, including: README.md, INSTALLATION_GUIDE.md, QUICK_REFERENCE.md, CHANGELOG.md",
     "openai/skills · skill-creator SKILL.md", "https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md",
     "The useful restriction is on clutter, not on file type."),
]
quotes = [{"who": w, "quote": q, "source": src, "url": u, "takeaway": t} for w, q, src, u, t in QUOTES]
data["rule"] = {
    "cap": CAP,
    "census": rule(eligible), "sample": rule(final),
    "by_pub": [{"label": p, **rule([x for x in eligible if x["publisher"] == p])} for p in PUBS],
    "hist": [{"k": lab, "v": sum(lo <= x["files_total"] <= hi for x in eligible), "over": lo > CAP} for lo, hi, lab in fbins],
    "p95_files": pctl([x["files_total"] for x in eligible], 0.95),
    "p99_files": pctl([x["files_total"] for x in eligible], 0.99),
    "nonmd": breaks, "over": over,
    "purposes": [{"k": PLABEL.get(k, k), "v": v} for k, v in pc.most_common()],
    "purpose_n": len(purposes),
    "could_md": dict(_C(sk["could_be_markdown"] for sk in purposes)),
    "purpose_examples": [sk for sk in purposes if sk["skill"] in ("docx", "financials-normalizer", "narrator", "tres-asc845-swap-reprice-skill", "clinical-reports", "fraud-detection", "notion-meeting-intelligence", "build-competitive-brief")],
    "quotes": quotes,
}

tpl = open(os.path.join(HERE, "report_template.html")).read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
open(os.path.join(HERE, "out", "skill-folder-anatomy.html"), "w").write(html)
print("wrote out/skill-folder-anatomy.html", len(html), "bytes")
