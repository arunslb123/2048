#!/usr/bin/env python3
"""Combine focus_sample.json + focus_audit.json into focus_rows.json with an 'as published' footprint.

Effective footprint = files in the folder + files it needs from outside when run as published:
plugin-level files it reads, sibling skills it invokes, and the built-in document skill for each
Office format it outputs (docx/xlsx/pptx/pdf). Connectors, CLIs and libraries add no files.
"""
import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, "focus_audit.json")))
s = {x["id"]: x for x in json.load(open(os.path.join(HERE, "focus_sample.json")))}
inv = {(x["repo"], x["path"]): x for x in json.load(open(os.path.join(HERE, "inventory.json")))}
doc = json.load(open(os.path.join(HERE, "docskills.json")))
A, V = {}, {}
for b in r["batches"]:
    for a in b["analysis"]:
        A[a["id"]] = a
    for v in b["verify"]:
        V[v["id"]] = v


def lookup(rp):
    parts = rp.strip().rstrip("/").split("/")
    if len(parts) < 3:
        return None
    repo, path = "/".join(parts[:2]), "/".join(parts[2:])
    return inv.get((repo, path)) or inv.get((repo, path.replace("/SKILL.md", "")))


rows = []
for i, x in s.items():
    a, v = A[i], V[i]
    roles = x["focus"]["roles"]
    own, own_md = x["focus"]["files"], roles.get("md", 0)
    add_md = add_nonmd = 0
    seen, doc_used, deps_used = set(), [], Counter()
    outs = set(a["outputs"])
    for d in a["external_deps"]:
        k, rp = d["kind"], d["resolved_path"]
        if k in ("mcp-connector-or-api", "cli-or-library", "referenced-file-missing") or (k, rp) in seen:
            deps_used[k] += 1
            continue
        seen.add((k, rp))
        if k == "built-in-doc-skill":
            fmt = next((f for f in doc if f in d["name"].lower()), None)
            if fmt and fmt in outs and fmt not in doc_used:  # only when the skill itself outputs that format
                doc_used.append(fmt)
                add_md += doc[fmt]["roles"].get("md", 0)
                add_nonmd += doc[fmt]["files"] - doc[fmt]["roles"].get("md", 0)
                deps_used[k] += 1
            continue
        deps_used[k] += 1
        if k == "other-skill":
            t = lookup(rp)
            if t:
                add_md += t["md_total"]
                add_nonmd += t["files_total"] - t["md_total"]
            continue
        if k == "plugin-level-file":
            add_md += d["file_count"] or 1
    # an Office output with no bundled generator still needs the matching document skill
    bundled = [b for b in a["bundled_non_md"] if b["role"] not in ("packaging", "test-eval")]
    for fmt in ("docx", "xlsx", "pptx"):
        if fmt in outs and fmt not in doc_used and not any(b["role"] in ("script", "template") for b in bundled):
            doc_used.append(fmt)
            add_md += doc[fmt]["roles"].get("md", 0)
            add_nonmd += doc[fmt]["files"] - doc[fmt]["roles"].get("md", 0)
    rows.append(dict(
        id=i, group=x["group"], pub=x["publisher"], repo=x["repo"], name=x["name"], path=x["path"],
        roles=roles, files=own, code_blocks=x["focus"]["code_blocks"],
        verdict=v["corrected_verdict"], reason=a["verdict_reason"], outputs=a["outputs"],
        code=a["needs_code_execution"], code_evidence=a["code_evidence"],
        bundled=[{"files": b["files"], "role": b["role"], "purpose": b["purpose"]} for b in bundled],
        doc_skills=doc_used, deps=dict(deps_used),
        eff_files=own + add_md + add_nonmd, eff_nonmd=(own - own_md) + add_nonmd,
        folder_fits=own <= 20 and own_md == own,
        office_out=bool(outs & {"xlsx", "docx", "pptx", "pdf"}),
        verifier_note=v["note"] if not v["verdict_agrees"] else "",
    ))
json.dump(rows, open(os.path.join(HERE, "focus_rows.json"), "w"), indent=1)
