PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/jest.config.cjs"
with open(PATH) as f:
    s = f.read()

# Add deep-tree-echo-core mapper if not present
if "'deep-tree-echo-core'" not in s:
    old = """  moduleNameMapper: {
    '^(\\\\.{1,2}/.*)\\\\.js$': '$1',
  },"""
    new = """  moduleNameMapper: {
    '^(\\\\.{1,2}/.*)\\\\.js$': '$1',
    '^deep-tree-echo-core$': '<rootDir>/node_modules/deep-tree-echo-core/dist/index.js',
    '^deep-tree-echo-core/(.*)$': '<rootDir>/node_modules/deep-tree-echo-core/dist/$1',
    '^dove9$': '<rootDir>/../dove9/src/index.ts',
    '^dove9/(.*)$': '<rootDir>/../dove9/src/$1',
  },"""
    if old in s:
        s = s.replace(old, new, 1)
        with open(PATH, "w") as f:
            f.write(s)
        print("OK: jest moduleNameMapper extended")
    else:
        print("FAIL: lint pattern not found")
else:
    print("SKIP: already mapped")
