PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/__mocks__/deep-tree-echo-core/index.cjs"
with open(PATH) as f: s = f.read()

# Add more stub exports based on what tests actually import
extras = """
class StubStorage {
  constructor() { this._store = new Map(); }
  store(key, val) { this._store.set(key, val); return Promise.resolve(); }
  retrieve(key) { return Promise.resolve(this._store.get(key) || null); }
  delete(key) { this._store.delete(key); return Promise.resolve(); }
  clear() { this._store.clear(); return Promise.resolve(); }
  list() { return Promise.resolve(Array.from(this._store.keys())); }
}

module.exports.InMemoryStorage = StubStorage;
module.exports.PersistentStorage = StubStorage;
module.exports.RedisStorage = StubStorage;
module.exports.SQLiteStorage = StubStorage;
module.exports.HypergraphStorage = StubStorage;
module.exports.CognitiveStorage = StubStorage;
module.exports.MemoryStorage = StubStorage;
module.exports.AtomSpace = StubStorage;
module.exports.PatternMatcher = class {
  match() { return []; }
  addPattern() {}
};
module.exports.CognitiveAgent = class {
  constructor() {}
  async think() { return {}; }
  async respond() { return ''; }
  async observe() {}
};
module.exports.AgentRegistry = class {
  constructor() { this._agents = new Map(); }
  register(id, agent) { this._agents.set(id, agent); }
  get(id) { return this._agents.get(id); }
  list() { return Array.from(this._agents.keys()); }
};
"""

if "InMemoryStorage" not in s:
    s = s + extras
    with open(PATH, "w") as f: f.write(s)
    print("OK: stub extended")
else:
    print("SKIP: already extended")
