PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/telemetry/GlobalWorkspaceBroadcaster.ts"
with open(PATH) as f:
    s = f.read()

old = """    // Fan-out to all subscribers concurrently
    const promises = this.subscribers.map((fn) =>
      Promise.resolve(fn(snapshot)).catch((err: unknown) => {
        log.warn('Global workspace subscriber threw an error', { error: err });
      })
    );

    await Promise.all(promises);"""

new = """    // Fan-out to all subscribers concurrently. Wrap each call in a
    // try/catch so synchronous throws are also isolated — a failing subscriber
    // must never block the others.
    const promises = this.subscribers.map((fn) => {
      try {
        return Promise.resolve(fn(snapshot)).catch((err: unknown) => {
          log.warn('Global workspace subscriber threw an error', { error: err });
        });
      } catch (err) {
        log.warn('Global workspace subscriber threw synchronously', { error: err });
        return Promise.resolve();
      }
    });

    await Promise.all(promises);"""

if old in s:
    s = s.replace(old, new, 1)
    with open(PATH, "w") as f:
        f.write(s)
    print("OK: subscriber isolation patched")
else:
    print("FAIL: pattern still not found")
    print("--- search for 'subscribers.map' context: ---")
    idx = s.find("subscribers.map")
    if idx > 0:
        print(repr(s[idx : idx + 250]))
