#!/usr/bin/env python3
PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/__tests__/cognitive-tier-integration.test.ts"
with open(PATH) as f: s = f.read()
old = """type Orchestrator = import('../orchestrator.js').Orchestrator;
type CognitiveTierMode = import('../orchestrator.js').CognitiveTierMode;

let OrchestratorClass: typeof import('../orchestrator.js').Orchestrator;

describe('Cognitive Tier Integration', () => {
  let orchestrator: InstanceType<typeof OrchestratorClass>;

  beforeEach(async () => {
    jest.clearAllMocks();
    const mod = await import('../orchestrator.js');
    OrchestratorClass = mod.Orchestrator;
  });"""
new = """type Orchestrator = import('../orchestrator.js').Orchestrator;
type CognitiveTierMode = import('../orchestrator.js').CognitiveTierMode;

let OrchestratorClass: typeof import('../orchestrator.js').Orchestrator;

beforeAll(async () => {
  // Import once at module load so all describe blocks (including outer ones)
  // see OrchestratorClass — fixes scope-of-assignment bug in the original file.
  const mod = await import('../orchestrator.js');
  OrchestratorClass = mod.Orchestrator;
});

describe('Cognitive Tier Integration', () => {
  let orchestrator: InstanceType<typeof OrchestratorClass>;

  beforeEach(() => {
    jest.clearAllMocks();
  });"""
if old not in s:
    raise SystemExit("pattern still not found")
s = s.replace(old, new, 1)
with open(PATH, "w") as f: f.write(s)
print("OK: cognitive-tier test fixed")
