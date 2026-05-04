#!/usr/bin/env python3
"""Filter o9nn org repos for echo/dte/aphrodite/cog members and pull next pages."""
import json
import os
import urllib.request

TOKEN = os.environ["GH_TOKEN"]
KEYS = ["echo", "aphro", "deltec", "dte", "lucy", "dove", "marduk",
        "core-self", "coreself", "introspect", "reservoir",
        "cog", "atom", "ocnn", "cnn", "neuro", "ksm", "echobeats"]


def fetch_page(page: int) -> list[dict]:
    req = urllib.request.Request(
        f"https://api.github.com/orgs/o9nn/repos?per_page=100&page={page}",
        headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


all_repos: list[dict] = []
for p in range(1, 10):
    page = fetch_page(p)
    if not page:
        break
    all_repos.extend(page)
    print(f"page {p}: {len(page)} repos (total {len(all_repos)})")
    if len(page) < 100:
        break

# Save full list
with open("/tmp/o9nn_all_repos.json", "w") as f:
    json.dump(all_repos, f, indent=2)
print(f"Saved {len(all_repos)} repos to /tmp/o9nn_all_repos.json")

# Filter relevant
relevant = []
for r in all_repos:
    n = (r.get("name") or "").lower()
    if any(k in n for k in KEYS):
        relevant.append({
            "name": r["name"],
            "full_name": r["full_name"],
            "pushed_at": r["pushed_at"],
            "size_kb": r["size"],
            "language": r.get("language"),
            "description": r.get("description"),
            "private": r.get("private"),
            "default_branch": r.get("default_branch"),
        })

relevant.sort(key=lambda x: x["pushed_at"], reverse=True)
print(f"\n=== Relevant repos ({len(relevant)}) ===")
for r in relevant:
    name = r["name"]
    pushed = r["pushed_at"][:10]
    size = r["size_kb"]
    lang = r["language"] or "?"
    desc = (r["description"] or "")[:60]
    print(f"  o9nn/{name:35s} pushed={pushed} size={size:>8}KB lang={lang:12s} {desc}")

with open("/home/ubuntu/dte-evolution/hypergraph/o9nn_relevant.json", "w") as f:
    json.dump(relevant, f, indent=2)
