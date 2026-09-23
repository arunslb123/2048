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

tpl = open(os.path.join(HERE, "report_template.html")).read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
open(os.path.join(HERE, "out", "skill-folder-anatomy.html"), "w").write(html)
print("wrote out/skill-folder-anatomy.html", len(html), "bytes")
