#!/usr/bin/env python3
"""Split the business-skill population by output complexity and draw 50 complex output skills.

complex output skill = classifier complexity 'complex' AND it hands back a deliverable
(an Office/PDF/HTML/data file or a multi-section structured report), not just a chat answer.
Writes complex_labels.json (merged), complex_stats.json, complex_sample.json, complex/batch*.tsv
for skills not already audited in the mixed 50-skill test.
"""
import json, os, statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
pop = json.load(open(os.path.join(HERE, "complex_pop.json")))
labels = {l["id"]: l for l in json.load(open(os.path.join(HERE, "complex_labels.json")))}
audited = {r["id"] for r in json.load(open(os.path.join(HERE, "focus_rows.json")))}
GROUPS = ["Finance & accounting", "Investing & banking", "Legal & compliance", "HR & people", "Operations", "Reports & documents"]
QUOTA = {"Finance & accounting": 9, "Investing & banking": 11, "Legal & compliance": 11, "HR & people": 4, "Operations": 5, "Reports & documents": 10}
REPO_CAP = 4
DELIV = {"structured-report-text", "xlsx", "docx", "pptx", "pdf", "html", "data-file"}
FILES = {"xlsx", "docx", "pptx", "pdf", "html", "data-file"}

for x in pop:
    l = labels[x["id"]]
    x["cx"] = l
    x["tier"] = ("complex-output" if l["complexity"] == "complex" and set(l["deliverables"]) & DELIV
                 else "moderate" if l["complexity"] == "moderate" else "simple" if l["complexity"] == "simple" else "complex-no-deliverable")


def stats(xs):
    n = len(xs)
    if not n:
        return {"n": 0}
    f = [x["focus"] for x in xs]
    has = Counter()
    tot = Counter()
    for a in f:
        for k, v in a["roles"].items():
            tot[k] += v
            has[k] += v > 0
    nonmd = [a["files"] - a["roles"].get("md", 0) for a in f]
    return {
        "n": n,
        "files_mean": round(sum(a["files"] for a in f) / n, 2), "files_median": st.median(a["files"] for a in f),
        "md_mean": round(tot["md"] / n, 2),
        "fits_ui_pct": round(100 * sum(a["ui_ok"] for a in f) / n, 1),
        "over20_pct": round(100 * sum(a["files"] > 20 for a in f) / n, 1),
        "has_nonmd_pct": round(100 * sum(v > 0 for v in nonmd) / n, 1),
        "has_pct": {k: round(100 * has[k] / n, 1) for k in ("md", "script", "template", "data", "asset", "packaging")},
        "totals": {k: tot[k] for k in ("md", "script", "template", "data", "asset", "packaging", "license", "other")},
        "office_file_pct": round(100 * sum(bool(set(x["cx"]["deliverables"]) & {"xlsx", "docx", "pptx", "pdf"}) for x in xs) / n, 1),
        "steps_median": st.median(x["cx"]["steps"] for x in xs),
        "calc_pct": round(100 * sum(x["cx"]["calculations"] for x in xs) / n, 1),
        "gate_pct": round(100 * sum(x["cx"]["quality_gate"] for x in xs) / n, 1),
        "outside_pct": round(100 * sum(a["refs_outside"] for a in f) / n, 1),
        "code_blocks_pct": round(100 * sum(a["code_blocks"] > 0 for a in f) / n, 1),
    }


tiers = ["simple", "moderate", "complex-output", "complex-no-deliverable"]
out = {"by_tier": {t: stats([x for x in pop if x["tier"] == t]) for t in tiers},
       "complex_by_group": {g: stats([x for x in pop if x["tier"] == "complex-output" and x["group"] == g]) for g in GROUPS},
       "tier_by_group": {g: dict(Counter(x["tier"] for x in pop if x["group"] == g)) for g in GROUPS},
       "all": stats(pop)}

sample = []
for g, q in QUOTA.items():
    items = sorted([x for x in pop if x["tier"] == "complex-output" and x["group"] == g], key=lambda x: x["skill_md_sha"])
    per_repo = defaultdict(int)
    picked = []
    for x in items:
        if len(picked) >= q:
            break
        if per_repo[x["repo"]] < REPO_CAP:
            per_repo[x["repo"]] += 1
            picked.append(x)
    for x in items:
        if len(picked) >= q:
            break
        if x not in picked:
            picked.append(x)
    sample.extend(picked)
short = 50 - len(sample)
if short > 0:  # top up from the largest groups if a quota could not be met
    rest = sorted([x for x in pop if x["tier"] == "complex-output" and x not in sample], key=lambda x: x["skill_md_sha"])
    sample.extend(rest[:short])

out["sample_stats"] = stats(sample)
out["sample_by_group"] = dict(Counter(x["group"] for x in sample))
json.dump(out, open(os.path.join(HERE, "complex_stats.json"), "w"), indent=1)
json.dump(sample, open(os.path.join(HERE, "complex_sample.json"), "w"), indent=1)

todo = [x for x in sample if x["id"] not in audited]
root = os.path.join(HERE, "repos")
nb = max(1, -(-len(todo) // 10))
for i in range(nb):
    with open(os.path.join(HERE, "complex", f"batch{i}.tsv"), "w") as fh:
        fh.write("id\tgroup\tpublisher\trepo\tname\tskill_dir_abs_path\n")
        for x in todo[i * 10:(i + 1) * 10]:
            fh.write(f"{x['id']}\t{x['group']}\t{x['publisher']}\t{x['repo']}\t{x['name']}\t{root}/{x['repo'].replace('/', '__')}/{x['path']}\n")
print(f"population {len(pop)} tiers {Counter(x['tier'] for x in pop)}")
print(f"sample {len(sample)} by group {out['sample_by_group']}; already audited {len(sample) - len(todo)}; to audit {len(todo)} in {nb} batches")
for t in tiers:
    s = out["by_tier"][t]
    if s["n"]:
        print(f"  {t:24s} n={s['n']:3d} fits_ui={s['fits_ui_pct']:5.1f}% has_nonmd={s['has_nonmd_pct']:5.1f}% over20={s['over20_pct']:4.1f}% files_mean={s['files_mean']:5.2f} md_mean={s['md_mean']:4.2f} office={s['office_file_pct']:4.1f}% steps_med={s['steps_median']} outside={s['outside_pct']}% has={s['has_pct']}")
