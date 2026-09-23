#!/usr/bin/env python3
"""Population for the complex-output study: finance, investing, legal, HR, operations, plus
reporting/document skills (docs-office-files, data-analytics-bi). Reuses focus.py's per-skill analysis.
Writes complex_pop.json and classification chunks complex/chunk*.tsv."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "focus.py")).read()
exec(src.split('eligible = ns["eligible"]')[0])  # helpers: ns, analyse, role, ...
GROUP = {"finance-accounting": "Finance & accounting", "investing-banking-pe": "Investing & banking",
         "legal-compliance": "Legal & compliance", "hr-people": "HR & people", "operations-admin": "Operations",
         "docs-office-files": "Reports & documents", "data-analytics-bi": "Reports & documents"}
pop = []
for x in ns["eligible"]:
    g = GROUP.get(x["label"]["domain"])
    if g:
        pop.append({**x, "group": g, "focus": analyse(x)})
pop.sort(key=lambda x: x["id"])
json.dump(pop, open(os.path.join(HERE, "complex_pop.json"), "w"), indent=1)
os.makedirs(os.path.join(HERE, "complex"), exist_ok=True)
root = os.path.join(HERE, "repos")
N = 5
size = -(-len(pop) // N)
for i in range(N):
    with open(os.path.join(HERE, "complex", f"chunk{i}.tsv"), "w") as fh:
        fh.write("id\tgroup\trepo\tname\tskill_dir_abs_path\tskill_md_lines\tfiles_in_folder\n")
        for x in pop[i * size:(i + 1) * size]:
            fh.write(f"{x['id']}\t{x['group']}\t{x['repo']}\t{x['name']}\t{root}/{x['repo'].replace('/', '__')}/{x['path']}\t{x['skill_md_lines']}\t{x['focus']['files']}\n")
from collections import Counter
print(len(pop), Counter(x["group"] for x in pop))
