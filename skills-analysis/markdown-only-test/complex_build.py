#!/usr/bin/env python3
"""Build out/markdown-only-test.html around complex, multi-step output skills.

Inputs: complex_pop.json (392 business skills + folder analysis), complex_labels.json (complexity),
complex_rows.json (50 complex skills, audited), focus_rows.json (earlier mixed 50, for comparison).
"""
import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
pop = json.load(open(os.path.join(HERE, "complex_pop.json")))
labels = {l["id"]: l for l in json.load(open(os.path.join(HERE, "complex_labels.json")))}
rows = json.load(open(os.path.join(HERE, "complex_rows.json")))
mixed = json.load(open(os.path.join(HERE, "focus_rows.json")))
GROUPS = ["Finance & accounting", "Investing & banking", "Legal & compliance", "HR & people", "Operations", "Reports & documents"]
CAP = 20
DELIV = {"structured-report-text", "xlsx", "docx", "pptx", "pdf", "html", "data-file"}
FILEOUT = {"xlsx", "docx", "pptx", "pdf", "html", "data-file"}
OFFICE = {"xlsx", "docx", "pptx", "pdf"}


def tier(l):
    if l["complexity"] == "complex" and set(l["deliverables"]) & DELIV:
        return "Complex: file deliverable" if set(l["deliverables"]) & FILEOUT else "Complex: text report"
    return {"simple": "Simple", "moderate": "Moderate"}.get(l["complexity"], "Other")


for x in pop:
    x["tier"] = tier(labels[x["id"]])
TIERS = ["Simple", "Moderate", "Complex: text report", "Complex: file deliverable"]


def census(xs, label):
    n = len(xs)
    f = [x["focus"] for x in xs]
    tot = Counter()
    for a in f:
        for k, v in a["roles"].items():
            tot[k] += v
    return {"label": label, "n": n,
            "nonmd": round(100 * sum(a["files"] > a["roles"].get("md", 0) for a in f) / n, 1),
            "script": round(100 * sum(a["roles"].get("script", 0) > 0 for a in f) / n, 1),
            "template": round(100 * sum(a["roles"].get("template", 0) > 0 or a["md_templates"] > 0 for a in f) / n, 1),
            "data": round(100 * sum(a["roles"].get("data", 0) > 0 for a in f) / n, 1),
            "fits": round(100 * sum(a["ui_ok"] for a in f) / n, 1),
            "over": sum(a["files"] > CAP for a in f),
            "files_mean": round(sum(a["files"] for a in f) / n, 1),
            "files_max": max(a["files"] for a in f),
            "steps": sorted(labels[x["id"]]["steps"] for x in xs)[n // 2],
            "office": round(100 * sum(bool(set(labels[x["id"]]["deliverables"]) & OFFICE) for x in xs) / n, 1),
            "outside": round(100 * sum(a["refs_outside"] for a in f) / n, 1),
            "totals": {k: tot[k] for k in ("md", "script", "template", "data", "asset", "packaging")}}


complex_pop = [x for x in pop if x["tier"].startswith("Complex")]
not_works = [x for x in rows if x["verdict"] != "works"]
causes = [
    ("Runs code (Python, SQL, shell)", sum(x["code"] for x in not_works)),
    ("Invokes skills not in its folder", sum(x["deps"].get("other-skill", 0) > 0 for x in not_works)),
    ("Bundled scripts, templates or data", sum(bool(x["bundled"]) for x in not_works)),
    ("Needs a connector", sum(x["deps"].get("mcp-connector-or-api", 0) > 0 for x in not_works)),
    ("Reads plugin-level playbooks", sum(x["deps"].get("plugin-level-file", 0) > 0 for x in not_works)),
    ("Office file via a document skill", sum(bool(x["doc_skills"]) for x in not_works)),
]
causes.sort(key=lambda c: -c[1])
tot = Counter()
for x in rows:
    for k, v in x["roles"].items():
        tot[k] += v
file_rows = [x for x in rows if set(x["outputs"]) & OFFICE]
data = {
    "n": len(rows),
    "verdicts": dict(Counter(x["verdict"] for x in rows)),
    "by_group": [{"label": g, "n": sum(x["group"] == g for x in rows),
                  **{v: sum(x["group"] == g and x["verdict"] == v for x in rows) for v in ("works", "degraded", "breaks")}}
                 for g in GROUPS if any(x["group"] == g for x in rows)],
    "folder_fits": sum(x["folder_fits"] for x in rows),
    "eff_fits": sum(x["eff_files"] <= CAP and x["eff_nonmd"] == 0 for x in rows),
    "eff_over": sum(x["eff_files"] > CAP for x in rows),
    "office_n": len(file_rows), "office_works": sum(x["verdict"] == "works" for x in file_rows),
    "code_n": sum(x["code"] for x in rows), "code_works": sum(x["code"] and x["verdict"] == "works" for x in rows),
    "not_works": len(not_works),
    "nonmd_cause": sum(x["eff_nonmd"] > 0 or bool(x["bundled"]) for x in not_works),
    "causes": [{"k": k, "v": v} for k, v in causes],
    "totals": {k: tot.get(k, 0) for k in ("md", "script", "template", "data", "asset", "packaging", "other", "license")},
    "steps_median": sorted(x["cx"]["steps"] for x in rows)[len(rows) // 2],
    "tiers": [census([x for x in pop if x["tier"] == t], t) for t in TIERS],
    "complex_by_group": [census([x for x in complex_pop if x["group"] == g], g) for g in GROUPS] + [census(complex_pop, "All complex")],
    "pop_n": len(pop), "complex_n": len(complex_pop),
    "dumbbell": [{"name": x["name"], "group": x["group"], "folder": x["files"], "eff": x["eff_files"], "docs": x["doc_skills"]}
                 for x in sorted(rows, key=lambda x: -x["eff_files"]) if x["eff_files"] > x["files"] or x["files"] > CAP][:18],
    "works": [{"name": x["name"], "group": x["group"], "reason": x["reason"]} for x in rows if x["verdict"] == "works"],
    "rows": [{"name": x["name"], "group": x["group"], "pub": x["pub"], "repo": x["repo"],
              "output": x["cx"]["output"], "steps": x["cx"]["steps"],
              "md": x["roles"].get("md", 0), "script": x["roles"].get("script", 0), "template": x["roles"].get("template", 0),
              "data": x["roles"].get("data", 0), "asset": x["roles"].get("asset", 0),
              "other": x["roles"].get("packaging", 0) + x["roles"].get("other", 0) + x["roles"].get("license", 0),
              "files": x["files"], "eff": x["eff_files"], "verdict": x["verdict"], "reason": x["reason"],
              "url": f"https://github.com/{x['repo']}/tree/HEAD/{x['path']}"}
             for x in sorted(rows, key=lambda x: (GROUPS.index(x["group"]), x["name"]))],
    "verifier_changed": sum(bool(x["verifier_note"]) for x in rows),
    "mixed": {"n": len(mixed), "verdicts": dict(Counter(x["verdict"] for x in mixed)),
              "simple_works": sum(x["verdict"] == "works" and tier(labels[x["id"]]) in ("Simple", "Moderate") for x in mixed)},
}
tpl = open(os.path.join(HERE, "complex_template.html")).read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
open(os.path.join(HERE, "out", "markdown-only-test.html"), "w").write(html)
json.dump(data, open(os.path.join(HERE, "complex_page_data.json"), "w"), indent=1)
print("wrote out/markdown-only-test.html", len(html), "bytes")
print({k: data[k] for k in ("verdicts", "folder_fits", "eff_fits", "eff_over", "office_n", "office_works", "code_n", "code_works", "not_works", "nonmd_cause", "totals", "steps_median")})
for t in data["tiers"]:
    print("  ", t["label"], t["n"], "nonmd", t["nonmd"], "script", t["script"], "template", t["template"], "fits", t["fits"], "over", t["over"], "files_mean", t["files_mean"], "steps", t["steps"])
