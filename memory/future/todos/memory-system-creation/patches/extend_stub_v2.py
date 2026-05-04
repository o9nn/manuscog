PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/__mocks__/deep-tree-echo-core/index.cjs"
with open(PATH) as f: s = f.read()

# Replace StubClass with a more complete one
old_stub = """class StubClass {
  constructor() {}
  generateResponse() { return Promise.resolve('stub-response'); }
  store() { return Promise.resolve('stub-id'); }
  search() { return Promise.resolve([]); }
  retrieve() { return Promise.resolve(null); }
  initialize() { return Promise.resolve(); }
  update() { return Promise.resolve(); }
  getState() { return {}; }
  on() {}
  emit() {}
  off() {}
  removeAllListeners() {}
}"""

new_stub = """class StubClass {
  constructor() { this._enabled = true; }
  generateResponse() { return Promise.resolve('stub-response'); }
  store() { return Promise.resolve('stub-id'); }
  search() { return Promise.resolve([]); }
  retrieve() { return Promise.resolve(null); }
  initialize() { return Promise.resolve(); }
  update() { return Promise.resolve(); }
  getState() { return {}; }
  setEnabled(v) { this._enabled = v; }
  isEnabled() { return this._enabled; }
  enable() { this._enabled = true; }
  disable() { this._enabled = false; }
  reset() {}
  shutdown() { return Promise.resolve(); }
  start() { return Promise.resolve(); }
  stop() { return Promise.resolve(); }
  pause() {}
  resume() {}
  configure() {}
  setOptions() {}
  on() { return this; }
  emit() { return true; }
  off() { return this; }
  once() { return this; }
  addListener() { return this; }
  removeAllListeners() { return this; }
}"""

if old_stub in s:
    s = s.replace(old_stub, new_stub, 1)
    with open(PATH, "w") as f: f.write(s)
    print("OK: StubClass enhanced")
else:
    print("SKIP/FAIL: stub already updated or pattern changed")
