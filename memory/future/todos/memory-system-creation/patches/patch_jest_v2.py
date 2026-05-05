PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/jest.config.cjs"
with open(PATH) as f:
    s = f.read()

# Add transformIgnorePatterns so deep-tree-echo-core is transformed to CJS-friendly
if "transformIgnorePatterns" not in s:
    old = "  testMatch: ['**/__tests__/**/*.test.ts'],"
    new = """  testMatch: ['**/__tests__/**/*.test.ts'],
  transformIgnorePatterns: [
    'node_modules/(?!(deep-tree-echo-core|dove9)/)',
  ],"""
    if old in s:
        s = s.replace(old, new, 1)
        with open(PATH, "w") as f:
            f.write(s)
        print("OK: transformIgnorePatterns added")
    else:
        print("FAIL: testMatch pattern not found")
else:
    print("SKIP: already has transformIgnorePatterns")
