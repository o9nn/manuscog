#!/usr/bin/env python3
"""Surgical patch to add SynchronizationEvent + GWB hooks into deltecho's Sys6OrchestratorBridge."""

PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/sys6-bridge/Sys6OrchestratorBridge.ts"

with open(PATH, "r") as f:
    src = f.read()

# 1. Inject SynchronizationEvent + SynchronizedChannel types BEFORE Sys6BridgeConfig
SYNC_TYPES = """/**
 * Synchronization event — fires when ≥2 Sys6 channels align at step t.
 *
 * Channels checked (from the Sys6 scheduling formula):
 *   dyadicPhase   = t % 2        (period 2)
 *   triadicPhase  = t % 3        (period 3)
 *   pentadicBound = t % 6 === 0  (stage boundary, period 6)
 *   quadPhase     = t % 4 === 0  (double-step delay window complete, period 4)
 *
 * A sync event is emitted whenever at least two of these conditions hold
 * simultaneously. This is the concrete implementation of Global Workspace
 * Theory: at moments of highest inter-channel coherence, the full joint state
 * is made available to all subscribers.
 */
export interface SynchronizationEvent {
  /** Absolute step counter */
  step: number;
  /** Step position within the current 30-step cycle (1-30) */
  cycleStep: number;
  /** Current cycle number */
  cycleNumber: number;
  /** Which channels are aligned at this step */
  alignedChannels: SynchronizedChannel[];
  /** Number of aligned channel pairs */
  channelPairCount: number;
  /** Snapshot of stream saliences at this moment */
  streamSaliences: [number, number, number];
  /** Timestamp */
  timestamp: number;
}

/**
 * A channel that is at a phase boundary at a given step
 */
export type SynchronizedChannel = 'dyadic' | 'triadic' | 'pentadic' | 'quad';

/**
 * Configuration for Sys6 Orchestrator Bridge
 */"""

src = src.replace(
    "/**\n * Configuration for Sys6 Orchestrator Bridge\n */", SYNC_TYPES, 1
)

# 2. Add enableSynchronizationEvents to config interface (after enableNestedAgency)
src = src.replace(
    "  enableNestedAgency: boolean;\n}",
    "  enableNestedAgency: boolean;\n  /** Emit sync_event when channels align (default: true) */\n  enableSynchronizationEvents: boolean;\n}",
    1,
)

# 3. Add to DEFAULT_CONFIG
src = src.replace(
    "  enableNestedAgency: true,\n};",
    "  enableNestedAgency: true,\n  enableSynchronizationEvents: true,\n};",
    1,
)

# 4. Add syncEventCount field — insert near other counters (after currentStep declaration line ~163)
# Find: "  private currentStep = 0;" and add sync counter
src = src.replace(
    "  private currentStep = 0;",
    "  private currentStep = 0;\n  // Synchronization event counter (Global Workspace Theory heartbeats)\n  private syncEventCount = 0;",
    1,
)

# 5. Add the sync event check call inside executeStep (after currentStep++)
old_step_block = """  private async executeStep(): Promise<void> {
    this.currentStep++;
    const stepAddress = this.toStepAddress(this.currentStep);"""
new_step_block = """  private async executeStep(): Promise<void> {
    this.currentStep++;
    const stepAddress = this.toStepAddress(this.currentStep);
    // Check for synchronization events (Global Workspace Theory heartbeats)
    if (this.config.enableSynchronizationEvents) {
      this.checkAndEmitSynchronizationEvent(this.currentStep);
    }"""
src = src.replace(old_step_block, new_step_block, 1)

# 6. Add checkAndEmitSynchronizationEvent method BEFORE the final closing class brace
# Insert before "  /**\n   * Get current state\n   */\n  public getState"
SYNC_METHOD = """  /**
   * Determine which Sys6 channels are at a phase boundary at absolute step t,
   * and emit a sync_event if two or more channels align.
   *
   * Channel phase-boundary definitions (t is 1-indexed):
   *   dyadic:   t % 2 === 0  (polarity flip completes, period 2)
   *   triadic:  t % 3 === 0  (triadic rotation completes, period 3)
   *   pentadic: t % 6 === 0  (pentadic stage boundary, period 6)
   *   quad:     t % 4 === 0  (double-step delay window completes, period 4)
   *
   * Note: pentadic boundaries are a strict subset of dyadic ones, so they are
   * tracked separately to distinguish partial from full pentadic alignment.
   */
  private checkAndEmitSynchronizationEvent(t: number): void {
    const aligned: SynchronizedChannel[] = [];

    if (t % 2 === 0) aligned.push('dyadic');
    if (t % 3 === 0) aligned.push('triadic');
    if (t % 6 === 0) aligned.push('pentadic');
    if (t % 4 === 0) aligned.push('quad');

    // Early-exit guard: a synchronization event requires at least 2 channels aligning.
    if (aligned.length < 2) return;

    this.syncEventCount++;
    const cycleStep = ((t - 1) % 30) + 1;

    const event: SynchronizationEvent = {
      step: t,
      cycleStep,
      cycleNumber: this.cycleNumber,
      alignedChannels: aligned,
      channelPairCount: (aligned.length * (aligned.length - 1)) / 2,
      streamSaliences: [
        this.streams[0].salience,
        this.streams[1].salience,
        this.streams[2].salience,
      ],
      timestamp: Date.now(),
    };

    log.debug(
      `Sync event at step ${t} (cycle step ${cycleStep}): channels [${aligned.join(', ')}] aligned`,
      { channelPairCount: event.channelPairCount }
    );

    this.emit('sync_event', event);
  }

  /**
   * Get current state
   */
  public getState(): {"""

src = src.replace(
    "  /**\n   * Get current state\n   */\n  public getState(): {", SYNC_METHOD, 1
)

# 7. Add syncEventCount to getMetrics return
src = src.replace(
    "  public getMetrics(): {\n    totalCycles: number;\n    totalSteps: number;\n    averageCycleTimeMs: number;\n    activeAgents: number;\n    streamSaliences: [number, number, number];\n  }",
    "  public getMetrics(): {\n    totalCycles: number;\n    totalSteps: number;\n    averageCycleTimeMs: number;\n    activeAgents: number;\n    streamSaliences: [number, number, number];\n    syncEventCount: number;\n  }",
    1,
)
src = src.replace(
    "      streamSaliences: [\n        this.streams[0].salience,\n        this.streams[1].salience,\n        this.streams[2].salience,\n      ],\n    };\n  }\n}",
    "      streamSaliences: [\n        this.streams[0].salience,\n        this.streams[1].salience,\n        this.streams[2].salience,\n      ],\n      syncEventCount: this.syncEventCount,\n    };\n  }\n}",
    1,
)

with open(PATH, "w") as f:
    f.write(src)

print(f"Patched {PATH}")
print(
    f"  - SynchronizationEvent interface added: {'export interface SynchronizationEvent' in src}"
)
print(f"  - enableSynchronizationEvents config: {'enableSynchronizationEvents' in src}")
print(f"  - syncEventCount field: {src.count('syncEventCount')}")
print(
    f"  - checkAndEmitSynchronizationEvent method: {'checkAndEmitSynchronizationEvent' in src}"
)
