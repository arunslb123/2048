#!/usr/bin/env python3
"""Draw a stratified ~100-skill knowledge-work sample and compute file-mix stats.

Inputs: pool.json (candidates), labels.json (classifier output), inventory.json (all skills).
Outputs: sample.json, stats.json, printed summary.
"""
import json, math, os, statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
pool = json.load(open(os.path.join(HERE, "pool.json"))) + json.load(open(os.path.join(HERE, "pool_add.json")))
labels = {l["id"]: l for f in ("labels_main.json", "labels_add.json") if os.path.exists(os.path.join(HERE, f))
          for l in json.load(open(os.path.join(HERE, f)))}
inventory = json.load(open(os.path.join(HERE, "inventory.json")))
# de-duplicate identical SKILL.md copies (e.g. .gemini mirrors, bundled agent-plugin copies)
_seen = set()
inventory = [x for x in inventory if not x["path"].startswith(".gemini/") and "/v1/" not in "/" + x["path"] + "/"
             and x["repo"] != "anthropics/claude-cookbooks"]
inventory = [x for x in sorted(inventory, key=lambda x: ("agent-plugins" in x["path"], x["repo"], x["path"]))
             if not (x["skill_md_sha"] in _seen or _seen.add(x["skill_md_sha"]))]
overrides = {}
if os.path.exists(os.path.join(HERE, "overrides.json")):
    overrides = json.load(open(os.path.join(HERE, "overrides.json")))

NEAR_DUPS = json.load(open(os.path.join(HERE, "near_dups.json")))["dropped"]
QUOTA = {"Anthropic": 40, "OpenAI": 35, "Other vendors": 15, "Community": 10}
VENDOR_REPOS = ("googleworkspace/", "gemini-cli-extensions/", "intuit/", "HubSpot/", "zapier/", "atlassian/",
                "canva-sdks/", "box/", "makenotion/", "anthropics/claude-plugins-community")
PLUGIN_CAP = 6


def publisher(repo):
    if repo.startswith(VENDOR_REPOS):
        return "Other vendors"
    if repo.startswith("anthropics/"):
        return "Anthropic"
    if repo.startswith("openai/"):
        return "OpenAI"
    if repo.startswith(("microsoft/",)):
        return "Microsoft"
    if repo.startswith(("huggingface/",)):
        return "Hugging Face"
    return "Community"


def group(x):
    """Stratum inside a publisher: repo + plugin (vendor repos: whole repo, their sub-folders are categories)."""
    if x["publisher"] == "Other vendors":
        return x["repo"]
    return f"{x['repo']}::{x['plugin']}"


_fresh = {(x["repo"], x["path"]): x for x in json.load(open(os.path.join(HERE, "inventory.json")))}
for x in pool:
    x.update({k: v for k, v in _fresh[(x["repo"], x["path"])].items() if k not in ("plugin", "id")})
    x["label"] = {**labels.get(x["id"], {}), **overrides.get(x["id"], {})}
    x["publisher"] = publisher(x["repo"])

eligible = [x for x in pool if x["label"].get("knowledge_work") and x["label"].get("real")
            and x["label"].get("role") == "task" and not x["label"].get("exclude")
            and "/v1/" not in "/" + x["path"] + "/" and "inactive" not in x["path"]
            and x["id"] not in NEAR_DUPS and x["repo"] != "googleworkspace/cli"]


def allocate(items, quota):
    groups = defaultdict(list)
    for x in items:
        groups[group(x)].append(x)
    for g in groups.values():
        g.sort(key=lambda x: x["skill_md_sha"])  # deterministic pseudo-random order
    total = len(items)
    quota = min(quota, total)
    # proportional with min 1 per group (if quota allows) and a per-group cap
    alloc = {g: 0 for g in groups}
    if len(groups) <= quota:
        for g in groups:
            alloc[g] = 1
    remaining = quota - sum(alloc.values())
    shares = {g: len(v) / total * quota for g, v in groups.items()}
    while remaining > 0:
        cands = [g for g in groups if alloc[g] < min(len(groups[g]), PLUGIN_CAP)]
        if not cands:
            cands = [g for g in groups if alloc[g] < len(groups[g])]
        if not cands:
            break
        g = max(cands, key=lambda g: (shares[g] - alloc[g], len(groups[g]), g))
        alloc[g] += 1
        remaining -= 1
    out = []
    for g, n in alloc.items():
        out.extend(groups[g][:n])
    return out, alloc


RESERVE = {"Anthropic": 8, "OpenAI": 7, "Other vendors": 4, "Community": 3}
sample, reserves, allocs = [], [], {}
for pub, q in QUOTA.items():
    items = [x for x in eligible if x["publisher"] == pub]
    picked, alloc = allocate(items, q)
    bigger, _ = allocate(items, q + RESERVE[pub])
    ids = {x["id"] for x in picked}
    reserves.extend(x for x in bigger if x["id"] not in ids)
    sample.extend(picked)
    allocs[pub] = {"eligible": len(items), "picked": len(picked), "by_group": {g: n for g, n in alloc.items() if n}}
json.dump(reserves, open(os.path.join(HERE, "reserves.json"), "w"), indent=1)

CATS = ["md_total", "script", "asset", "data_config", "packaging", "license", "other"]


def cat_counts(x):
    c, p = x["counts"], x.get("packaging_by_cat", {})
    return {"md_total": x["md_total"], "script": c["script"] - p.get("script", 0),
            "asset": c["asset"] - p.get("asset", 0), "data_config": c["data_config"] - p.get("data_config", 0),
            "packaging": x.get("packaging", 0), "license": c["license"], "other": c["other"] - p.get("other", 0)}


def content_files(x):
    """Files that carry skill content: everything except packaging metadata and licenses."""
    cc = cat_counts(x)
    return cc["md_total"] + cc["script"] + cc["asset"] + cc["data_config"] + cc["other"]


def describe(xs):
    n = len(xs)
    if not n:
        return {}
    md = [x["md_total"] for x in xs]
    res = {
        "n": n,
        "md_mean": round(st.mean(md), 2),
        "md_median": st.median(md),
        "md_p90": sorted(md)[max(0, math.ceil(0.9 * n) - 1)],
        "md_max": max(md),
        "files_mean": round(st.mean(x["files_total"] for x in xs), 2),
        "files_median": st.median(x["files_total"] for x in xs),
        "skill_md_lines_median": st.median(x["skill_md_lines"] for x in xs),
        "skill_md_words_median": st.median(x["skill_md_words"] for x in xs),
        "skill_md_only_pct": round(100 * sum(1 for x in xs if x["files_total"] == 1) / n, 1),
        "content_files_mean": round(st.mean(content_files(x) for x in xs), 2),
        "content_files_median": st.median(content_files(x) for x in xs),
        "skill_md_only_content_pct": round(100 * sum(1 for x in xs if content_files(x) == 1) / n, 1),
        "md_share_of_content_files_pct": round(100 * sum(x["md_total"] for x in xs) / max(1, sum(content_files(x) for x in xs)), 1),
    }
    tot = Counter()
    has = Counter()
    for x in xs:
        cc = cat_counts(x)
        for k, v in cc.items():
            tot[k] += v
            if v:
                has[k] += 1
        if x["md_total"] > 1:
            has["extra_md"] += 1
    allfiles = sum(tot.values())
    res["per_category"] = {k: {"mean_per_skill": round(tot[k] / n, 2),
                               "pct_skills_with_any": round(100 * has[k] / n, 1),
                               "share_of_all_files_pct": round(100 * tot[k] / allfiles, 1) if allfiles else 0}
                           for k in CATS}
    res["pct_with_reference_md_beyond_skill_md"] = round(100 * has["extra_md"] / n, 1)
    bins = [(1, 1, "1"), (2, 2, "2"), (3, 5, "3-5"), (6, 10, "6-10"), (11, 20, "11-20"), (21, 10**9, "21+")]
    res["md_histogram"] = {lab: sum(1 for v in md if lo <= v <= hi) for lo, hi, lab in bins}
    fbins = [(1, 1, "1"), (2, 3, "2-3"), (4, 6, "4-6"), (7, 10, "7-10"), (11, 25, "11-25"), (26, 10**9, "26+")]
    res["files_histogram"] = {lab: sum(1 for x in xs if lo <= x["files_total"] <= hi) for lo, hi, lab in fbins}
    res["content_files_histogram"] = {lab: sum(1 for x in xs if lo <= content_files(x) <= hi) for lo, hi, lab in fbins}
    combos = Counter()
    for x in xs:
        cc = cat_counts(x)
        parts = ["md" if cc["md_total"] > 1 else "SKILL.md"]
        parts += [k for k in ("script", "asset", "data_config") if cc[k]]
        combos[" + ".join(parts)] += 1
    res["composition_patterns"] = dict(combos.most_common())
    sub = Counter()
    for x in xs:
        for s in x["subdirs"]:
            if s != "(root)":
                sub[s] += 1
    res["subdir_pct"] = {k: round(100 * v / n, 1) for k, v in sub.most_common(12)}
    ak = Counter()
    for x in xs:
        for k, v in x["asset_kinds"].items():
            ak[k] += v
    res["asset_kinds_total"] = dict(ak)
    ext = Counter()
    for x in xs:
        for k, v in x["exts"].items():
            ext[k] += v
    res["top_exts"] = dict(ext.most_common(20))
    return res


stats = {
    "sample": describe(sample),
    "sample_by_publisher": {p: describe([x for x in sample if x["publisher"] == p]) for p in QUOTA},
    "sample_by_domain": {d: describe([x for x in sample if x["label"]["domain"] == d])
                         for d in sorted({x["label"]["domain"] for x in sample})},
    "eligible_population": describe(eligible),
    "eligible_by_publisher": {p: describe([x for x in eligible if x["publisher"] == p]) for p in QUOTA},
    "all_skills_by_publisher": {p: describe([dict(x) for x in inventory if publisher(x["repo"]) == p])
                                for p in ["Anthropic", "OpenAI", "Other vendors", "Microsoft", "Hugging Face", "Community"]},
    "all_skills": describe(inventory),
    "allocation": allocs,
}

json.dump(sample, open(os.path.join(HERE, "sample.json"), "w"), indent=1)
json.dump(stats, open(os.path.join(HERE, "stats.json"), "w"), indent=1)

s = stats["sample"]
print(f"eligible={len(eligible)} sample={len(sample)}")
for p, a in allocs.items():
    print(f"  {p}: eligible {a['eligible']} picked {a['picked']}")
print(json.dumps({k: s[k] for k in s if k not in ("top_exts",)}, indent=1))
