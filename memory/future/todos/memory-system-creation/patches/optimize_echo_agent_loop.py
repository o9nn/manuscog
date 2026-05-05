#!/usr/bin/env python3
"""Optimize echo-agent-loop with reentrancy guard + tick overrun telemetry."""
PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/echo-agent-loop.ts"
with open(PATH) as f:
    s = f.read()

# 1. Add tickInProgress guard field + overrunCount near other private state
old_field = "  private grandCycleTimer?: ReturnType<typeof setInterval>;"
new_field = """  private grandCycleTimer?: ReturnType<typeof setInterval>;
  // Reentrancy guard: ticks must not overlap. If processing exceeds stepDurationMs,
  // subsequent timer fires are skipped and counted as overruns for telemetry.
  private tickInProgress = false;
  private tickOverruns = 0;
  private lastTickStart = 0;"""
assert old_field in s
s = s.replace(old_field, new_field, 1)

# 2. Wrap setInterval callback with reentrancy guard
old_interval = """    this.grandCycleTimer = setInterval(() => {
      this.tick().catch(error => {
        log.error('Grand cycle tick error:', error);
      });
    }, this.config.stepDurationMs);"""
new_interval = """    this.grandCycleTimer = setInterval(() => {
      // Reentrancy guard: skip this tick if the previous one is still in flight.
      // This prevents event-loop pile-up under adverse load and surfaces the
      // overrun count as observable telemetry.
      if (this.tickInProgress) {
        this.tickOverruns++;
        if (this.tickOverruns % 10 === 0) {
          log.warn(
            `Echo agent loop tick overrun: ${this.tickOverruns} skipped ticks ` +
            `(last tick start: ${Date.now() - this.lastTickStart}ms ago)`
          );
        }
        return;
      }
      this.tickInProgress = true;
      this.lastTickStart = Date.now();
      this.tick()
        .catch((error) => {
          log.error('Grand cycle tick error:', error);
        })
        .finally(() => {
          this.tickInProgress = false;
        });
    }, this.config.stepDurationMs);"""
assert old_interval in s
s = s.replace(old_interval, new_interval, 1)

# 3. Add public getter for overrun count
# Find getMetrics method
if "public getTickOverruns" not in s:
    # Insert before "public getMetrics" if it exists, else after stop()
    insertion = """  /**
   * Total number of skipped ticks due to reentrancy guard.
   * Persistent overruns indicate the cognitive processor is exceeding step duration —
   * either reduce processor load or increase stepDurationMs.
   */
  public getTickOverruns(): number {
    return this.tickOverruns;
  }
"""
    # Insert right before "  /**\n   * Inject a stimulus"
    target = "  /**\n   * Inject a stimulus into the proactive loop"
    if target in s:
        s = s.replace(target, insertion + "\n" + target, 1)

with open(PATH, "w") as f:
    f.write(s)
print("Echo agent loop optimization applied:")
print("  - tickInProgress guard:", "this.tickInProgress = true" in s)
print("  - overrun counter:", "tickOverruns" in s)
print("  - getTickOverruns getter:", "getTickOverruns" in s)
