#!/usr/bin/env python3
"""Build out/markdown-only-test.html from focus_rows.json (50 audited skills) and focus_census.json (329)."""
import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "focus_rows.json")))
census = json.load(open(os.path.join(HERE, "focus_census.json")))
GROUPS = ["Finance & accounting", "Investing & banking", "Legal & compliance", "HR & people", "Operations"]
ROLES = ["md", "script", "template", "data", "asset", "packaging"]
CAP = 20

not_works = [x for x in rows if x["verdict"] != "works"]
nonmd_cause = [x for x in not_works if x["eff_nonmd"] > 0 or x["bundled"]]
causes = [
    ("Runs code (Python, SQL, shell)", "Runs code (writes or executes Python, SQL, shell)", sum(x["code"] for x in not_works)),
    ("Invokes skills not in its folder", "Invokes other skills that aren't in its folder", sum(x["deps"].get("other-skill", 0) > 0 for x in not_works)),
    ("Bundled scripts, templates or data", "Needs bundled scripts, templates or data files", sum(bool(x["bundled"]) for x in not_works)),
    ("Needs a connector", "Needs a connector (CRM, ledger, mail, Box…)", sum(x["deps"].get("mcp-connector-or-api", 0) > 0 for x in not_works)),
    ("Reads plugin-level playbooks", "Reads plugin-level playbooks or policy files", sum(x["deps"].get("plugin-level-file", 0) > 0 for x in not_works)),
    ("Office file via a document skill", "Delivers Excel/Word/PowerPoint via a document skill", sum(bool(x["doc_skills"]) for x in not_works)),
]
causes.sort(key=lambda c: -c[2])


def census_row(label, xs):
    n = len(xs)
    f = [x["focus"] for x in xs]
    tot = Counter()
    has = Counter()
    for a in f:
        for k, v in a["roles"].items():
            tot[k] += v
            has[k] += v > 0
    return {"label": label, "n": n,
            "fits": round(100 * sum(a["ui_ok"] for a in f) / n), "over": sum(a["files"] > CAP for a in f),
            "script": round(100 * has["script"] / n), "template": round(100 * (sum((a["roles"].get("template", 0) > 0 or a["md_templates"] > 0) for a in f)) / n),
            "data": round(100 * has["data"] / n), "asset": round(100 * has["asset"] / n),
            "office": round(100 * sum(a["office_output"] for a in f) / n), "outside": round(100 * sum(a["refs_outside"] for a in f) / n),
            "files": {k: tot[k] for k in ROLES}, "files_max": max(a["files"] for a in f)}


tot = Counter()
for x in rows:
    for k, v in x["roles"].items():
        tot[k] += v
data = {
    "n": len(rows),
    "verdicts": dict(Counter(x["verdict"] for x in rows)),
    "by_group": [{"label": g, "n": sum(x["group"] == g for x in rows),
                  **{v: sum(x["group"] == g and x["verdict"] == v for x in rows) for v in ("works", "degraded", "breaks")}} for g in GROUPS],
    "folder_fits": sum(x["folder_fits"] for x in rows),
    "eff_fits": sum(x["eff_files"] <= CAP and x["eff_nonmd"] == 0 for x in rows),
    "eff_over": sum(x["eff_files"] > CAP for x in rows),
    "eff_nonmd": sum(x["eff_nonmd"] > 0 for x in rows),
    "office_n": sum(x["office_out"] for x in rows), "office_works": sum(x["office_out"] and x["verdict"] == "works" for x in rows),
    "code_n": sum(x["code"] for x in rows), "code_works": sum(x["code"] and x["verdict"] == "works" for x in rows),
    "not_works": len(not_works), "nonmd_cause": len(nonmd_cause),
    "causes": [{"short": sh, "k": k, "v": v} for sh, k, v in causes],
    "folder_totals": {k: tot.get(k, 0) for k in ROLES},
    "census": [census_row(g, [x for x in census if x["group"] == g]) for g in GROUPS] + [census_row("All five domains", census)],
    "census_n": len(census),
    "census_md_templates": sum(x["focus"]["md_templates"] for x in census),
    "census_md_template_skills": sum(x["focus"]["md_templates"] > 0 for x in census),
    "dumbbell": [{"name": x["name"], "group": x["group"], "folder": x["files"], "eff": x["eff_files"], "verdict": x["verdict"],
                  "docs": x["doc_skills"]} for x in sorted(rows, key=lambda x: -x["eff_files"]) if x["eff_files"] > x["files"] or x["files"] > CAP][:16],
    "works": [{"name": x["name"], "group": x["group"]} for x in rows if x["verdict"] == "works"],
    "rows": [{"name": x["name"], "group": x["group"], "pub": x["pub"], "repo": x["repo"],
              "md": x["roles"].get("md", 0), "script": x["roles"].get("script", 0), "template": x["roles"].get("template", 0),
              "data": x["roles"].get("data", 0), "asset": x["roles"].get("asset", 0), "other": x["roles"].get("packaging", 0) + x["roles"].get("other", 0) + x["roles"].get("license", 0),
              "files": x["files"], "eff": x["eff_files"], "outputs": x["outputs"], "code": x["code"],
              "verdict": x["verdict"], "reason": x["reason"],
              "url": f"https://github.com/{x['repo']}/tree/HEAD/{x['path']}"} for x in sorted(rows, key=lambda x: (GROUPS.index(x["group"]), x["name"]))],
    "verifier_changed": sum(bool(x["verifier_note"]) for x in rows),
}
tpl = open(os.path.join(HERE, "focus_template.html")).read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
open(os.path.join(HERE, "out", "markdown-only-test.html"), "w").write(html)
json.dump(data, open(os.path.join(HERE, "focus_page_data.json"), "w"), indent=1)
print("wrote out/markdown-only-test.html", len(html), "bytes;", {k: data[k] for k in ("verdicts", "folder_fits", "eff_fits", "eff_over", "eff_nonmd", "office_n", "office_works", "code_n", "code_works", "not_works", "nonmd_cause", "folder_totals", "census_md_templates")})
