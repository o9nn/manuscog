#!/usr/bin/env python3
"""Apply CI_WORKFLOW_UPDATES.md changes to ci.yml."""
PATH = "/var/agi_neighborhood/deltecho-repo/.github/workflows/ci.yml"
with open(PATH) as f: s = f.read()

# 1. Lint step continue-on-error
old_lint = '''      - name: Lint code
        run: pnpm run lint || echo "::warning::Linting not fully configured"'''
new_lint = '''      - name: Lint code
        run: pnpm run lint || echo "::warning::Linting issues detected - see logs for details"
        continue-on-error: true'''
if old_lint in s:
    s = s.replace(old_lint, new_lint, 1)
    print("OK: lint continue-on-error applied")
else:
    print("SKIP: lint already updated or pattern changed")

# 2. Add CI/TLS env vars to every e2e step. Easiest: inject after every existing
#    "WEB_PASSWORD: ${{ secrets.WEB_PASSWORD || 'test-password' }}" line if no
#    NODE_TLS_REJECT_UNAUTHORIZED line is already present after it.
import re
PATTERN = "WEB_PASSWORD: ${{ secrets.WEB_PASSWORD || 'test-password' }}"
INSERTION = (
    "WEB_PASSWORD: ${{ secrets.WEB_PASSWORD || 'test-password' }}\n"
    "          CI: true\n"
    "          NODE_TLS_REJECT_UNAUTHORIZED: '0'"
)
# Replace only those occurrences that don't already have CI: true on the next line.
# Iterate manually:
lines = s.split("\n")
out = []
i = 0
patches = 0
while i < len(lines):
    out.append(lines[i])
    if PATTERN in lines[i]:
        # Check if next non-blank lines already contain CI: true / NODE_TLS_REJECT
        nxt1 = lines[i+1] if i+1 < len(lines) else ""
        nxt2 = lines[i+2] if i+2 < len(lines) else ""
        if "CI: true" not in nxt1 and "NODE_TLS_REJECT_UNAUTHORIZED" not in nxt2:
            out.append("          CI: true")
            out.append("          NODE_TLS_REJECT_UNAUTHORIZED: '0'")
            patches += 1
    i += 1
s2 = "\n".join(out)
if patches > 0:
    with open(PATH, "w") as f: f.write(s2)
    print(f"OK: {patches} e2e steps updated with CI/TLS env vars")
else:
    print("SKIP: e2e steps already updated")
