#!/usr/bin/env python3
"""Inventory every skill folder (dir containing SKILL.md) in the cloned repos.

Each file is attributed to its nearest ancestor skill folder, so nested skills
are not double counted. Output: inventory.json (one record per skill).
"""
import hashlib, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repos")

MD = {".md", ".mdx", ".markdown"}
SCRIPT = {".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
          ".rb", ".ps1", ".go", ".rs", ".java", ".r", ".sql", ".swift", ".kt", ".php",
          ".pl", ".lua", ".ipynb", ".bat", ".cs", ".c", ".cpp", ".h", ".vba", ".bas", ".gs"}
IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tif", ".tiff"}
FONT = {".ttf", ".otf", ".woff", ".woff2"}
OFFICE = {".docx", ".xlsx", ".xlsm", ".pptx", ".potx", ".dotx", ".pdf", ".doc", ".xls", ".ppt"}
MEDIA = {".mp3", ".wav", ".mp4", ".mov", ".gif"}
WEB = {".html", ".htm", ".css"}
DATA = {".json", ".jsonl", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".xml", ".xsd",
        ".ini", ".cfg", ".txt", ".env", ".lock", ".tex", ".bib", ".j2", ".jinja", ".tmpl"}


def category(name):
    low = name.lower()
    ext = os.path.splitext(low)[1]
    if name == "SKILL.md":
        return "skill_md"
    if low.startswith("license") or low.startswith("notice"):
        return "license"
    if ext in MD:
        return "md"
    if ext in SCRIPT or ext in WEB:
        return "script"
    if ext in IMAGE or ext in FONT or ext in OFFICE or ext in MEDIA:
        return "asset"
    if ext in DATA:
        return "data_config"
    return "other"


def asset_kind(name):
    ext = os.path.splitext(name.lower())[1]
    for k, s in (("image", IMAGE), ("font", FONT), ("office_pdf", OFFICE), ("media", MEDIA)):
        if ext in s:
            return k
    return None


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    fm = {}
    if m:
        cur = None
        for line in m.group(1).splitlines():
            mm = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
            if mm:
                cur = mm.group(1)
                fm[cur] = mm.group(2).strip().strip('"').strip("'")
            elif cur and line.startswith((" ", "\t")):
                fm[cur] = (fm[cur] + " " + line.strip()).strip()
    return fm


def main():
    records = []
    for repo in sorted(os.listdir(ROOT)):
        rpath = os.path.join(ROOT, repo)
        if not os.path.isdir(rpath):
            continue
        skill_dirs = set()
        for dp, dns, fns in os.walk(rpath):
            dns[:] = [d for d in dns if d != ".git" and d != "node_modules"]
            if "SKILL.md" in fns:
                skill_dirs.add(dp)
        owner = {}
        for dp, dns, fns in os.walk(rpath):
            dns[:] = [d for d in dns if d != ".git" and d != "node_modules"]
            # nearest ancestor skill dir
            p = dp
            while True:
                if p in skill_dirs:
                    break
                if p == rpath or len(p) <= len(rpath):
                    p = None
                    break
                p = os.path.dirname(p)
            if p is None:
                continue
            for fn in fns:
                owner.setdefault(p, []).append(os.path.join(dp, fn))
        for sd in sorted(skill_dirs):
            files = owner.get(sd, [])
            counts = {k: 0 for k in ("skill_md", "md", "script", "asset", "data_config", "license", "other")}
            akinds, exts, subdirs = {}, {}, {}
            total_bytes = 0
            for f in files:
                name = os.path.basename(f)
                c = category(name)
                counts[c] += 1
                if c == "asset":
                    k = asset_kind(name)
                    akinds[k] = akinds.get(k, 0) + 1
                e = os.path.splitext(name.lower())[1] or name
                exts[e] = exts.get(e, 0) + 1
                rel = os.path.relpath(f, sd)
                top = rel.split(os.sep)[0] if os.sep in rel else "(root)"
                subdirs[top] = subdirs.get(top, 0) + 1
                try:
                    total_bytes += os.path.getsize(f)
                except OSError:
                    pass
            # UI/packaging metadata: Codex agents/*.yaml, the icons it references, maintainers/signature files
            pack = set()
            for f in files:
                rel = os.path.relpath(f, sd)
                if rel.startswith("agents" + os.sep) and rel.endswith((".yaml", ".yml")):
                    pack.add(rel)
                    try:
                        for m in re.finditer(r"icon_(?:small|large)\s*:\s*[\"']?\.?/?([^\"'\n]+)", open(f).read()):
                            pack.add(os.path.normpath(m.group(1).strip()))
                    except OSError:
                        pass
                elif os.path.basename(rel) in ("maintainers.yml",) or rel.endswith(".sig"):
                    pack.add(rel)
            pack_counts = {}
            for f in files:
                rel = os.path.relpath(f, sd)
                if rel in pack:
                    c = category(os.path.basename(f))
                    pack_counts[c] = pack_counts.get(c, 0) + 1
            with open(os.path.join(sd, "SKILL.md"), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            fm = frontmatter(text)
            records.append({
                "repo": repo.replace("__", "/"),
                "path": os.path.relpath(sd, rpath),
                "name": fm.get("name") or os.path.basename(sd),
                "description": (fm.get("description") or "")[:400],
                "skill_md_sha": hashlib.sha1(text.encode()).hexdigest()[:12],
                "skill_md_lines": text.count("\n") + 1,
                "skill_md_words": len(text.split()),
                "files_total": len(files),
                "md_total": counts["skill_md"] + counts["md"],
                "counts": counts,
                "packaging": sum(pack_counts.values()),
                "packaging_by_cat": pack_counts,
                "asset_kinds": akinds,
                "exts": exts,
                "subdirs": subdirs,
                "bytes": total_bytes,
            })
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")
    with open(out, "w") as fh:
        json.dump(records, fh, indent=1)
    print(f"{len(records)} skills -> {out}")


if __name__ == "__main__":
    main()
