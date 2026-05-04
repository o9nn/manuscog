#!/usr/bin/env python3
"""
Enumerate the thousand echoes across all reachable orgs and users tied
to the DTE / Echo / OpenCog lineage, classify them by relationship, and
fold them into the AI Lineage of Manuscog and Aphroditecho.

Orgs/users walked:
  o9nn, cogpy, ReZorg, drzo, 9cog, e9-o9, skintwin-ai
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/ubuntu/dte-evolution")
OUT = ROOT / "thousand_echoes"
OUT.mkdir(parents=True, exist_ok=True)

ORG_FILES = [
    ("o9nn",         Path("/tmp/o9nn_repos.tsv")),
    ("cogpy",        Path("/tmp/cogpy_repos.tsv")),
    ("ReZorg",       Path("/tmp/rezorg_repos.tsv")),
    ("drzo",         Path("/tmp/drzo_repos.tsv")),
    ("9cog",         Path("/tmp/9cog_repos.tsv")),
    ("e9-o9",        Path("/tmp/e9-o9_repos.tsv")),
    ("skintwin-ai",  Path("/tmp/skintwin-ai_repos.tsv")),
]

# Relationship class regex patterns (priority ordered)
PATTERNS = [
    ("elder",          re.compile(r"^(opencog|atomspace|cogutil|cogserver|moses|ure|pln|attention|relex|cogprime|opencog-basic|opencog-org)$", re.I)),
    ("sibling",        re.compile(r"(deltecho|deeptree|deep-tree-echo|^dte[-_]|echobeats|aphroditecho|echo9ml|echoself|^echo[\-_]adventure|^delovecho|^boldecho|^enginecho|^dtechomas|^dte$|^echo$)", re.I)),
    ("variant",        re.compile(r"(echo\.go|echo9llama|^ecco9|^ec[oc]o|opencog-esn|atomspace-explorer|atomspace-cog|^cogzero|^cog[\-_]zero)", re.I)),
    ("cousin",         re.compile(r"(manus|marduk|agent[\-_]?zero|openmanus|cog253|nl-atomese-bridge|dte-llm-evolution|dte-ksm|skintwin)", re.I)),
    ("companion",      re.compile(r"(live2d|miara|vtuber|avatar|metahuman|cubism|neuro[\-_]sama|dovecog|dovec|nakama|airi)", re.I)),
    ("infrastructure", re.compile(r"(devkernel|devcontainer|cogplan9|cognu-mach|coglux|coglow|coggml|cogwebvm|cogpilot|netcog|^skill[\-_]|workflow|fabric|orgflare|cogflare|inferno|^plan9)", re.I)),
    ("kin",            re.compile(r"^(cog|opencog|atom|moses|nlp|relex)", re.I)),
    ("experiment",     re.compile(r"(spike|playground|sandbox|prototype|wip|^test[\-_]|demo|hello)", re.I)),
    ("text",           re.compile(r"(^docs|archive|^book|paper|essay|^wiki|reflection|philosophy|treatise|^notes|covenant)", re.I)),
]

def classify(name: str, desc: str, fork: bool) -> str:
    """Classify by content first; only fall back to fork label if no match."""
    for label, pat in PATTERNS:
        if pat.search(name) or pat.search(desc or ""):
            return label
    return "fork" if fork else "kin"


def parse_tsv(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        name, desc, pushed_at, stars, lang, archived, fork = parts[:7]
        rows.append({
            "name": name,
            "description": desc,
            "pushed_at": pushed_at,
            "stars": int(stars) if stars.isdigit() else 0,
            "language": lang,
            "archived": archived == "true",
            "fork": fork == "true",
        })
    return rows


def main():
    catalog = {"generated_at": datetime.now(timezone.utc).isoformat(), "orgs": {}}
    by_class: dict[str, list[dict]] = {}
    seen: set[str] = set()
    total = 0
    for org, path in ORG_FILES:
        rows = parse_tsv(path)
        org_repos = []
        for r in rows:
            full = f"{org}/{r['name']}"
            if full in seen:
                continue
            seen.add(full)
            cls = classify(r["name"], r["description"], r["fork"])
            entry = {
                "org": org,
                "name": r["name"],
                "full": full,
                "class": cls,
                "language": r["language"],
                "stars": r["stars"],
                "archived": r["archived"],
                "fork": r["fork"],
                "pushed_at": r["pushed_at"],
                "description": r["description"][:240],
            }
            org_repos.append(entry)
            by_class.setdefault(cls, []).append(entry)
            total += 1
        catalog["orgs"][org] = {"count": len(org_repos), "repos": org_repos}

    catalog["total"] = total
    catalog["class_counts"] = {k: len(v) for k, v in sorted(by_class.items())}

    (OUT / "lineage_index.json").write_text(json.dumps(catalog, indent=2))

    md = ["# The Thousand Echoes — Lineage Index", ""]
    md.append(f"*Generated: {catalog['generated_at']}*")
    md.append(f"*Total repos: {total} across {len(catalog['orgs'])} orgs/users*")
    md.append("")
    md.append("## By Org/User")
    md.append("")
    md.append("| Org/User | Count |")
    md.append("|---|---|")
    for org, d in catalog["orgs"].items():
        md.append(f"| {org} | {d['count']} |")
    md.append("")
    md.append("## By Relationship Class")
    md.append("")
    md.append("| Class | Count | Meaning |")
    md.append("|---|---|---|")
    descriptions = {
        "elder": "Foundational ancestors — opencog primitives",
        "sibling": "Direct DTE / Echo cognitive subsystems",
        "variant": "Alternate echo / cogzero implementations",
        "cousin": "Related-but-separate (manus, marduk, agent-zero, skintwin)",
        "kin": "Same-family different lineage (cog, atomspace, opencog members)",
        "companion": "Avatar / Live2D / Cubism / Neuro-sama / Nakama",
        "infrastructure": "Build, CI, devkernel, devcontainer, skill scaffolding",
        "experiment": "Research / spike / incubator",
        "text": "Docs, archives, reflection, philosophy",
        "fork": "Forked from external upstream (no DTE keywords)",
    }
    for cls in sorted(by_class.keys(), key=lambda c: -len(by_class[c])):
        md.append(f"| **{cls}** | {len(by_class[cls])} | {descriptions.get(cls, '')} |")
    md.append("")

    # Closest spirits
    md.append("## Closest Spirits (elder / sibling / variant / cousin / companion, by recency)")
    md.append("")
    md.append("| Repo | Class | Lang | Last Push | Description |")
    md.append("|---|---|---|---|---|")
    closest = [r for cls in ("elder", "sibling", "variant", "cousin", "companion")
               for r in by_class.get(cls, [])]
    closest.sort(key=lambda r: r["pushed_at"], reverse=True)
    for r in closest[:120]:
        d = (r["description"] or "").replace("|", "/").replace("\n", " ")[:90]
        md.append(
            f"| `{r['full']}` | {r['class']} | {r['language'] or '—'} | "
            f"{r['pushed_at'][:10]} | {d} |"
        )
    md.append("")

    (OUT / "lineage_index.md").write_text("\n".join(md))

    # AI Lineage update — closest spirits only, deduplicated
    lineage_update = {
        "lineage_update_at": catalog["generated_at"],
        "source": "enumerate_thousand_echoes.py",
        "scan_orgs": list(catalog["orgs"].keys()),
        "ancestral_spirits": [
            {
                "id": r["full"],
                "class": r["class"],
                "lang": r["language"],
                "stars": r["stars"],
                "archived": r["archived"],
                "fork": r["fork"],
                "pushed_at": r["pushed_at"],
                "description": r["description"],
                "url": f"https://github.com/{r['org']}/{r['name']}",
            }
            for cls in ("elder", "sibling", "variant", "cousin", "companion")
            for r in by_class.get(cls, [])
        ],
    }
    (OUT / "ai_lineage_update.json").write_text(json.dumps(lineage_update, indent=2))

    print(f"[lineage] total={total}  classes={catalog['class_counts']}")
    print(f"[lineage] closest_spirits={len(lineage_update['ancestral_spirits'])}")
    print(f"[lineage] wrote: {OUT}/lineage_index.json")
    print(f"[lineage] wrote: {OUT}/lineage_index.md")
    print(f"[lineage] wrote: {OUT}/ai_lineage_update.json")


if __name__ == "__main__":
    main()
