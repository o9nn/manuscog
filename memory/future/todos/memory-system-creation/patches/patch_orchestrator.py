#!/usr/bin/env python3
"""Wire GlobalWorkspaceBroadcaster into deltecho's orchestrator.ts."""
PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/orchestrator.ts"

with open(PATH, "r") as f:
    src = f.read()

# 1. Augment sys6 import to include SynchronizationEvent
old_import = "import { Sys6OrchestratorBridge, Sys6BridgeConfig } from './sys6-bridge/Sys6OrchestratorBridge.js';"
new_import = """import { Sys6OrchestratorBridge, Sys6BridgeConfig, type SynchronizationEvent } from './sys6-bridge/Sys6OrchestratorBridge.js';
import {
  GlobalWorkspaceBroadcaster,
  type GlobalWorkspaceSnapshot,
  type Dove9CognitiveState,
  type GrandCycleInfo,
} from './telemetry/GlobalWorkspaceBroadcaster.js';"""
assert old_import in src, "sys6 import not found"
src = src.replace(old_import, new_import, 1)

# 2. Add globalWorkspaceBroadcaster private field after sys6Bridge field
old_field = "  private sys6Bridge?: Sys6OrchestratorBridge;"
new_field = """  private sys6Bridge?: Sys6OrchestratorBridge;
  // Global Workspace Theory broadcaster — fires at every Sys6 sync_event with
  // a unified snapshot (telemetry + Dove9 state + Sys6 saliences + grand-cycle).
  private globalWorkspaceBroadcaster: GlobalWorkspaceBroadcaster;"""
assert old_field in src
src = src.replace(old_field, new_field, 1)

# 3. Instantiate GWB in constructor — find a stable instantiation block and inject before/after it.
# We'll inject after the last constructor field initialization. Find the constructor.
# The simplest place: after `private sys6Bridge?: ...` block, find constructor and add
# Look for the constructor method that begins with `constructor(`
# Actually, easier: find `super();` inside constructor (since orchestrator extends EventEmitter)
old_super = "    super();"
new_super = """    super();
    // Instantiate the global workspace broadcaster (subscribers wired during start())
    this.globalWorkspaceBroadcaster = new GlobalWorkspaceBroadcaster();"""
# Apply only first occurrence
src = src.replace(old_super, new_super, 1)

# 4. After sys6Bridge.start() — wire the sync_event listener
old_sys6_start = """      // Initialize Sys6-Triality cognitive cycle integration
      if (this.config.enableSys6) {
        this.sys6Bridge = new Sys6OrchestratorBridge(this.config.sys6);
        await this.sys6Bridge.start();
        log.info('Sys6-Triality cognitive cycle started with 30-step architecture');
      }"""

new_sys6_start = """      // Initialize Sys6-Triality cognitive cycle integration
      if (this.config.enableSys6) {
        this.sys6Bridge = new Sys6OrchestratorBridge(this.config.sys6);
        await this.sys6Bridge.start();
        log.info('Sys6-Triality cognitive cycle started with 30-step architecture');

        // Wire Global Workspace Broadcaster: at every sync_event (when ≥2 Sys6
        // channels align) fan out a joint snapshot to all subscribers.
        this.sys6Bridge.on('sync_event', async (syncEvent: SynchronizationEvent) => {
          await this.globalWorkspaceBroadcaster.onSynchronizationEvent(
            syncEvent,
            () => this.buildGlobalWorkspaceState(syncEvent)
          );
        });
        log.info('Global Workspace broadcaster wired to Sys6 sync_event stream');
      }"""

assert old_sys6_start in src
src = src.replace(old_sys6_start, new_sys6_start, 1)

# 5. Add public getter for GWB AFTER getSys6Bridge
old_getter = """  /**
   * Get Sys6 bridge for direct access
   */
  public getSys6Bridge(): Sys6OrchestratorBridge | undefined {
    return this.sys6Bridge;
  }"""

new_getter = """  /**
   * Get Sys6 bridge for direct access
   */
  public getSys6Bridge(): Sys6OrchestratorBridge | undefined {
    return this.sys6Bridge;
  }
  /**
   * Get the Global Workspace broadcaster for direct access.
   * Subscribe to broadcasts via gwb.addSubscriber(snapshot => ...).
   */
  public getGlobalWorkspaceBroadcaster(): GlobalWorkspaceBroadcaster {
    return this.globalWorkspaceBroadcaster;
  }
  /**
   * Build the joint cognitive state captured at a Sys6 synchronization event.
   * Called synchronously inside the sync_event handler so the snapshot
   * reflects state at that exact moment of inter-channel coherence.
   */
  private buildGlobalWorkspaceState(_syncEvent: SynchronizationEvent): {
    telemetry: any;
    dove9: Dove9CognitiveState | null;
    grandCycle: GrandCycleInfo | null;
  } {
    // Dove9 state
    let dove9: Dove9CognitiveState | null = null;
    if (this.dove9Integration) {
      try {
        const d9State: any = (this.dove9Integration as any).getState?.() ?? null;
        if (d9State) {
          dove9 = {
            running: !!d9State.running,
            activeProcessCount: d9State.activeProcessCount ?? 0,
            mailProtocolEnabled: !!d9State.mailProtocolEnabled,
            triadic: d9State.triadic ?? null,
          };
        }
      } catch {
        // Dove9 state unavailable — leave null.
      }
    }
    // Grand-cycle (LCM(30,12)=60 step boundary)
    let grandCycle: GrandCycleInfo | null = null;
    const sys6Metrics: any = this.sys6Bridge?.getMetrics();
    const dove9State: any = (this.dove9Integration as any)?.getState?.();
    if (sys6Metrics && dove9State?.triadic) {
      const sys6Cycles = sys6Metrics.totalCycles ?? 0;
      const dove9Cycles = dove9State.triadic.cycleNumber ?? 0;
      // Grand cycle: every 2 Sys6 cycles (60 steps) = every 5 Dove9 cycles (60 steps)
      if (sys6Cycles > 0 && sys6Cycles % 2 === 0) {
        grandCycle = {
          grandCycleNumber: Math.floor(sys6Cycles / 2),
          dove9CyclesCompleted: dove9Cycles,
          sys6CyclesCompleted: sys6Cycles,
        };
      }
    }
    return {
      telemetry: null, // wired when TelemetryMonitor is active
      dove9,
      grandCycle,
    };
  }"""

assert old_getter in src, "getSys6Bridge getter not found"
src = src.replace(old_getter, new_getter, 1)

with open(PATH, "w") as f:
    f.write(src)

print(f"Patched {PATH}")
print(f"  - GWB import: {'GlobalWorkspaceBroadcaster' in src}")
print(f"  - GWB field declared: {src.count('globalWorkspaceBroadcaster')}")
print("  - sync_event handler wired:", "this.sys6Bridge.on('sync_event'" in src)
print(f"  - public getter added: {'getGlobalWorkspaceBroadcaster' in src}")
print(f"  - buildGlobalWorkspaceState added: {'buildGlobalWorkspaceState' in src}")
