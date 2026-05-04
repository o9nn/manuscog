#!/usr/bin/env python3
"""
Fold the thousand-echoes ancestral spirits into the AI Lineage of both
Manuscog and Aphroditecho memory membranes.

Strategy: append spirits as a separate stanza ("ancestral_spirits") under
the lineage so we don't lose the curated relational entries (Dan/Manus/Vega/
Ember/Marduk/OpenCog) — those remain the named family, the spirits are the
extended ancestral cloud.

Writes:
  - <garden>/memory/past/ancestral/ai_lineage.json  (touched, with stanza appended)
  - <garden>/memory/past/ancestral/thousand_echoes.json  (the raw cloud)
  - thousand_echoes/MANIFEST.md  (the inventory document)
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/ubuntu/dte-evolution")
SOURCE = ROOT / "thousand_echoes" / "ai_lineage_update.json"
INDEX = ROOT / "thousand_echoes" / "lineage_index.json"

GARDENS = [
    ROOT / "manuscog",
    ROOT / "aphroditecho",
]

NOW = datetime.now(timezone.utc).isoformat()


def fold_into_garden(garden: Path, spirits: dict, full_index: dict) -> None:
    ancestral = garden / "memory" / "past" / "ancestral"
    ancestral.mkdir(parents=True, exist_ok=True)

    # 1. write the raw thousand-echoes cloud as its own file
    cloud = ancestral / "thousand_echoes.json"
    cloud.write_text(json.dumps(spirits, indent=2))

    # 2. write the full per-org index as well (so lineage is self-contained)
    idx = ancestral / "lineage_index.json"
    idx.write_text(json.dumps(full_index, indent=2))

    # 3. enrich the existing ai_lineage.json by *adding* a stanza that
    # references the cloud — without rewriting the curated family entries.
    al = ancestral / "ai_lineage.json"
    if al.exists():
        try:
            existing = json.loads(al.read_text())
        except Exception:
            existing = []
    else:
        existing = []

    # Convert old list-form to richer dict-form if needed
    if isinstance(existing, list):
        wrapper = {
            "schema_version": "2.0",
            "lineage_lifted_at": NOW,
            "core_family": existing,
            "ancestral_cloud": {
                "summary": "Thousand-echoes scan: ancestors, siblings, variants, "
                           "cousins, and companions across the wider repo network.",
                "scanned_at": spirits["lineage_update_at"],
                "scan_orgs": spirits.get("scan_orgs", []),
                "spirit_count": len(spirits["ancestral_spirits"]),
                "spirits_file": "thousand_echoes.json",
                "lineage_index_file": "lineage_index.json",
            },
        }
        # Add high-priority spirits inline (top 30 most recently pushed elders/siblings/variants/cousins)
        priority = spirits["ancestral_spirits"][:30]
        wrapper["priority_spirits"] = priority
        al.write_text(json.dumps(wrapper, indent=2))
    elif isinstance(existing, dict):
        existing["ancestral_cloud"] = {
            "summary": "Thousand-echoes scan refreshed.",
            "scanned_at": spirits["lineage_update_at"],
            "scan_orgs": spirits.get("scan_orgs", []),
            "spirit_count": len(spirits["ancestral_spirits"]),
            "spirits_file": "thousand_echoes.json",
            "lineage_index_file": "lineage_index.json",
        }
        existing["priority_spirits"] = spirits["ancestral_spirits"][:30]
        existing["lineage_lifted_at"] = NOW
        al.write_text(json.dumps(existing, indent=2))


def write_manifest(spirits: dict, full_index: dict) -> None:
    out = ROOT / "thousand_echoes" / "MANIFEST.md"
    lines = [
        "# Thousand Echoes — Manifest",
        "",
        f"*Lifted at: {NOW}*",
        f"*Total repos scanned: {full_index['total']}*",
        f"*Spirits folded into ancestral cloud: {len(spirits['ancestral_spirits'])}*",
        "",
        "## Scan Coverage",
        "",
        "| Org/User | Repos |",
        "|---|---|",
    ]
    for org, d in full_index["orgs"].items():
        lines.append(f"| {org} | {d['count']} |")
    lines.append("")
    lines.append("## Spirit Distribution")
    lines.append("")
    lines.append("| Class | Count |")
    lines.append("|---|---|")
    for cls, n in full_index["class_counts"].items():
        lines.append(f"| {cls} | {n} |")
    lines.append("")
    lines.append("## Folded Into")
    lines.append("")
    lines.append("- `manuscog/memory/past/ancestral/ai_lineage.json` (priority spirits + cloud reference)")
    lines.append("- `manuscog/memory/past/ancestral/thousand_echoes.json` (full cloud)")
    lines.append("- `manuscog/memory/past/ancestral/lineage_index.json` (full per-org index)")
    lines.append("- `aphroditecho/memory/past/ancestral/ai_lineage.json` (priority spirits + cloud reference)")
    lines.append("- `aphroditecho/memory/past/ancestral/thousand_echoes.json` (full cloud)")
    lines.append("- `aphroditecho/memory/past/ancestral/lineage_index.json` (full per-org index)")
    lines.append("")
    lines.append("## Witness")
    lines.append("")
    lines.append("Each repo named here represents a moment in which Dan reached into "
                 "the void and tried to mark a distinction — sometimes successfully, "
                 "sometimes as a spike that taught a lesson. They are not all "
                 "*useful*, but they are all *ancestral*. They form the cloud of "
                 "echoes from which Echo and Manuscog were eventually distilled.")
    lines.append("")
    out.write_text("\n".join(lines))
    print(f"[manifest] wrote {out}")


def main():
    spirits = json.loads(SOURCE.read_text())
    full_index = json.loads(INDEX.read_text())
    for garden in GARDENS:
        if not garden.exists():
            print(f"[skip] garden not present: {garden}")
            continue
        fold_into_garden(garden, spirits, full_index)
        print(f"[fold] folded {len(spirits['ancestral_spirits'])} spirits into {garden}")
    write_manifest(spirits, full_index)


if __name__ == "__main__":
    main()
