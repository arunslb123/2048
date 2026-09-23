#!/usr/bin/env python3
"""Apply audit verdicts to the drawn sample and compute the reported statistics.

Replacement rule (deterministic, no cherry-picking): a rejected pick is replaced by the
next audited 'keep' reserve from the same stratum (in the stratum's SKILL.md-hash order),
else from the same publisher. Writes final_sample.json, final_stats.json, final_sample.csv.
"""
import contextlib, csv, io, json, os, re, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {"__file__": os.path.join(HERE, "sample_and_stats.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(ns["__file__"]).read(), ns)
describe, cat_counts, content_files, group = ns["describe"], ns["cat_counts"], ns["content_files"], ns["group"]
QUOTA = ns["QUOTA"]
eligible = ns["eligible"]

sample = json.load(open(os.path.join(HERE, "sample.json")))
reserves = json.load(open(os.path.join(HERE, "reserves.json")))
audit = {}
for f in ("audit.json", "audit5.json", "audit6.json"):
    p = os.path.join(HERE, f)
    if os.path.exists(p):
        for a in json.load(open(p)):
            audit[a["id"]] = a

reserves.sort(key=lambda x: (group(x), x["skill_md_sha"]))
used, final, replacements, unaudited = set(), [], [], []
for x in sample:
    a = audit.get(x["id"])
    if a is None:
        unaudited.append(x["id"])
        continue
    if a["verdict"] == "keep":
        final.append(x)
        continue
    cands = [r for r in reserves if r["id"] not in used and audit.get(r["id"], {}).get("verdict") == "keep"]
    pick = ([r for r in cands if group(r) == group(x)] or [r for r in cands if r["publisher"] == x["publisher"]] or [None])[0]
    replacements.append({"rejected": x["id"], "rejected_name": x["name"], "repo": x["repo"],
                         "reason": a.get("reject_reason"), "replacement": pick and pick["id"],
                         "replacement_name": pick and pick["name"], "replacement_repo": pick and pick["repo"]})
    if pick:
        used.add(pick["id"])
        final.append(pick)
assert not unaudited, f"unaudited picks: {unaudited}"

for x in final:
    a = audit[x["id"]]
    x["audit"] = {k: a[k] for k in ("md_roles", "nonmd_summary", "skill_md_quality")}


# ---- robustness figures -------------------------------------------------------------
def reweighted(xs, pop):
    """Publisher-reweighted prevalence/mean: weight = population share / sample share."""
    w = {}
    for p in QUOTA:
        ns_ = sum(1 for x in xs if x["publisher"] == p)
        np_ = sum(1 for x in pop if x["publisher"] == p)
        w[p] = (np_ / len(pop)) / (ns_ / len(xs)) if ns_ else 0
    tot = sum(w[x["publisher"]] for x in xs)
    def wmean(f):
        return round(sum(w[x["publisher"]] * f(x) for x in xs) / tot, 3)
    cc = lambda x: cat_counts(x)
    return {
        "md_mean": wmean(lambda x: x["md_total"]),
        "one_md_pct": round(100 * wmean(lambda x: x["md_total"] == 1), 1),
        "single_file_pct": round(100 * wmean(lambda x: x["files_total"] == 1), 1),
        "content_single_pct": round(100 * wmean(lambda x: content_files(x) == 1), 1),
        "script_pct": round(100 * wmean(lambda x: cc(x)["script"] > 0), 1),
        "asset_pct": round(100 * wmean(lambda x: cc(x)["asset"] > 0), 1),
        "data_pct": round(100 * wmean(lambda x: cc(x)["data_config"] > 0), 1),
        "extra_md_pct": round(100 * wmean(lambda x: x["md_total"] > 1), 1),
        "weights": {k: round(v, 3) for k, v in w.items()},
    }


def brief(xs):
    if not xs:
        return {}
    md = [x["md_total"] for x in xs]
    n = len(xs)
    return {"n": n, "md_mean": round(st.mean(md), 2), "md_median": st.median(md),
            "one_md_pct": round(100 * sum(v == 1 for v in md) / n, 1),
            "single_file_pct": round(100 * sum(x["files_total"] == 1 for x in xs) / n, 1),
            "content_single_pct": round(100 * sum(content_files(x) == 1 for x in xs) / n, 1),
            "script_pct": round(100 * sum(cat_counts(x)["script"] > 0 for x in xs) / n, 1),
            "asset_pct": round(100 * sum(cat_counts(x)["asset"] > 0 for x in xs) / n, 1)}


def pooled_share(xs):
    tot = {k: 0 for k in ns["CATS"]}
    for x in xs:
        for k, v in cat_counts(x).items():
            tot[k] += v
    s = sum(tot.values())
    return {k: round(100 * v / s, 1) for k, v in tot.items()}


big3 = sorted(final, key=lambda x: -x["files_total"])[:3]
no_big3 = [x for x in final if x not in big3]

# Anthropic skills that lean on plugin-level shared context outside the skill folder
PLUGIN_REF = re.compile(r"(\.\./)+[A-Za-z_./-]*\.md|CLAUDE\.md|CONNECTORS\.md|plugin[- ]level|practice profile", re.I)
def refs_outside(x):
    t = open(os.path.join(HERE, "repos", x["repo"].replace("/", "__"), x["path"], "SKILL.md"), errors="replace").read()
    return bool(PLUGIN_REF.search(t))

anth_single = [x for x in eligible if x["publisher"] == "Anthropic" and content_files(x) == 1]
readme_files = 0
for x in final:
    root = os.path.join(HERE, "repos", x["repo"].replace("/", "__"), x["path"])
    for dp, dns, fns in os.walk(root):
        readme_files += sum(1 for f in fns if f.lower() in ("readme.md", "changelog.md", "claude.md"))

stats = {
    "n": len(final),
    "sample": describe(final),
    "sample_by_publisher": {p: describe([x for x in final if x["publisher"] == p]) for p in QUOTA},
    "sample_by_domain": {d: describe([x for x in final if x["label"]["domain"] == d])
                         for d in sorted({x["label"]["domain"] for x in final})},
    "eligible_population": describe(eligible),
    "eligible_by_publisher": {p: describe([x for x in eligible if x["publisher"] == p]) for p in QUOTA},
    "all_skills": ns["stats"]["all_skills"],
    "all_skills_by_publisher": ns["stats"]["all_skills_by_publisher"],
    "replacements": replacements,
    "quality": {q: sum(1 for x in final if x["audit"]["skill_md_quality"] == q) for q in ("substantive", "moderate", "thin")},
    "robust": {
        "sample": brief(final),
        "sample_reweighted_to_population": reweighted(final, eligible),
        "population": brief(eligible),
        "population_without_kdense": brief([x for x in eligible if not x["repo"].startswith("K-Dense")]),
        "population_without_claude_for_legal": brief([x for x in eligible if x["repo"] != "anthropics/claude-for-legal"]),
        "anthropic_population": brief([x for x in eligible if x["publisher"] == "Anthropic"]),
        "anthropic_without_legal": brief([x for x in eligible if x["publisher"] == "Anthropic" and x["repo"] != "anthropics/claude-for-legal"]),
        "anthropics_skills_repo": brief([x for x in eligible if x["repo"] == "anthropics/skills"]),
        "openai_population": brief([x for x in eligible if x["publisher"] == "OpenAI"]),
        "pooled_share_sample": pooled_share(final),
        "pooled_share_sample_without_3_largest": pooled_share(no_big3),
        "three_largest": [{"name": x["name"], "repo": x["repo"], "files": x["files_total"]} for x in big3],
        "files_in_3_largest_pct": round(100 * sum(x["files_total"] for x in big3) / sum(x["files_total"] for x in final), 1),
        "anthropic_single_file_refs_outside_folder_pct": round(100 * sum(refs_outside(x) for x in anth_single) / len(anth_single), 1),
        "anthropic_single_file_n": len(anth_single),
        "readme_like_md_in_sample": readme_files,
        "near_dups_dropped": len(ns["NEAR_DUPS"]),
    },
}
json.dump(final, open(os.path.join(HERE, "final_sample.json"), "w"), indent=1)
json.dump(stats, open(os.path.join(HERE, "final_stats.json"), "w"), indent=1)

with open(os.path.join(HERE, "final_sample.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "publisher", "repo", "plugin", "skill", "domain", "md_files", "scripts_code", "assets",
                "data_config", "packaging", "license", "other", "files_total", "skill_md_lines",
                "skill_md_quality", "extra_md_roles", "non_md_summary", "path"])
    for x in sorted(final, key=lambda x: (x["publisher"], x["repo"], x["plugin"], x["name"])):
        cc = cat_counts(x)
        w.writerow([x["id"], x["publisher"], x["repo"], x["plugin"], x["name"], x["label"]["domain"],
                    cc["md_total"], cc["script"], cc["asset"], cc["data_config"], cc["packaging"],
                    cc["license"], cc["other"], x["files_total"], x["skill_md_lines"],
                    x["audit"]["skill_md_quality"], x["audit"]["md_roles"], x["audit"]["nonmd_summary"], x["path"]])

print(f"final n={len(final)}; replacements={len(replacements)}")
for r in replacements:
    print("  ", r)
print(json.dumps(stats["robust"], indent=1))
