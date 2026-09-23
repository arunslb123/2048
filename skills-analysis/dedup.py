#!/usr/bin/env python3
"""Find near-duplicate SKILL.md files across the candidate pool (text similarity >= 0.9).

Candidate pairs come from an inverted index of 5-word shingles; each is confirmed with
difflib. For each duplicate cluster the canonical copy is kept by source priority:
official maintained repo > archived official repo > community; ties go to the lower id.
Writes near_dups.json: {dropped_id: kept_id}.
"""
import difflib, json, os, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
pool = json.load(open(os.path.join(HERE, "pool.json"))) + json.load(open(os.path.join(HERE, "pool_add.json")))
ROOT = os.path.join(HERE, "repos")
COMMUNITY = ("K-Dense-AI/", "coreyhaines31/", "phuryn/", "alirezarezvani/", "kepano/")
ARCHIVED = ("openai/role-specific-plugins",)


def priority(x):
    if x["repo"].startswith(COMMUNITY):
        return 2
    if x["repo"].startswith(ARCHIVED):
        return 1
    return 0


def body(x):
    p = os.path.join(ROOT, x["repo"].replace("/", "__"), x["path"], "SKILL.md")
    t = open(p, encoding="utf-8", errors="replace").read()
    t = re.sub(r"^---.*?\n---", "", t, flags=re.S)  # frontmatter differs trivially between copies
    return " ".join(t.split()).lower()


texts = {x["id"]: body(x) for x in pool}
shingles = {}
for i, t in texts.items():
    w = t.split()
    shingles[i] = {" ".join(w[k:k + 5]) for k in range(max(1, len(w) - 4))}
index = defaultdict(list)
for i, sh in shingles.items():
    for s in sh:
        index[s].append(i)
co = Counter()
for s, ids in index.items():
    if 1 < len(ids) <= 40:
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                co[(ids[a], ids[b])] += 1
pairs = []
for (a, b), n in co.items():
    jac = n / (len(shingles[a]) + len(shingles[b]) - n)
    if jac < 0.5:
        continue
    r = difflib.SequenceMatcher(None, texts[a], texts[b], autojunk=False).ratio()
    if r >= 0.9:
        pairs.append((a, b, round(r, 3)))

# union-find clusters
parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
for a, b, _ in pairs:
    parent[find(a)] = find(b)
clusters = defaultdict(list)
for a, b, _ in pairs:
    clusters[find(a)].append(a)
    clusters[find(a)].append(b)
by_id = {x["id"]: x for x in pool}
dropped = {}
for members in clusters.values():
    members = sorted(set(members), key=lambda i: (priority(by_id[i]), i))
    for m in members[1:]:
        dropped[m] = members[0]
json.dump({"pairs": pairs, "dropped": dropped}, open(os.path.join(HERE, "near_dups.json"), "w"), indent=1)
print(f"{len(pairs)} near-duplicate pairs, {len(dropped)} copies dropped")
for d, k in sorted(dropped.items()):
    print(f"  drop {d} {by_id[d]['repo']}::{by_id[d]['name']}  -> keep {k} {by_id[k]['repo']}::{by_id[k]['name']}")
