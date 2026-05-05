#!/usr/bin/env python3
"""Enable the git pat beast connector and GitHub connector for this session."""
import json


PATH = "/home/ubuntu/.manus/config/config.json"
with open(PATH) as f:
    cfg = json.load(f)

targets = {"git pat beast", "GitHub"}
for c in cfg.get("connectors", []):
    if c.get("name") in targets:
        c["enabled"] = True
        print(f"Enabled: {c.get('name')}")

with open(PATH, "w") as f:
    json.dump(cfg, f, indent=2)
print("Config saved.")
