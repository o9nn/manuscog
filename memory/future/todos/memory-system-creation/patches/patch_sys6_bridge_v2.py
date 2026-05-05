#!/usr/bin/env python3
"""Surgical patch with count-validated single-application of SynchronizationEvent."""
PATH = "/var/agi_neighborhood/deltecho-repo/deep-tree-echo-orchestrator/src/sys6-bridge/Sys6OrchestratorBridge.ts"
with open(PATH) as f:
    s = f.read()

if "SynchronizationEvent" in s:
    print("Already patched, skipping.")
    raise SystemExit(0)

SYNC_BLOCK = """/**
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

"""

# 1. Insert types BEFORE the existing "Configuration for Sys6 Orchestrator Bridge" comment block.
target_marker = "/**\n * Configuration for Sys6 Orchestrator Bridge\n */"
assert s.count(target_marker) == 1, f"Expected 1 marker, found {s.count(target_marker)}"
s = s.replace(target_marker, SYNC_BLOCK + target_marker, 1)

# 2. Add enableSynchronizationEvents to config interface
old1 = "  enableNestedAgency: boolean;\n}"
assert s.count(old1) == 1
s = s.replace(
    old1,
    "  enableNestedAgency: boolean;\n  /** Emit sync_event when channels align (default: true) */\n  enableSynchronizationEvents: boolean;\n}",
    1,
)

# 3. Add to DEFAULT_CONFIG
old2 = "  enableNestedAgency: true,\n};"
assert s.count(old2) == 1
s = s.replace(
    old2, "  enableNestedAgency: true,\n  enableSynchronizationEvents: true,\n};", 1
)

# 4. Add syncEventCount field after currentStep
old3 = "  private currentStep = 0;"
assert s.count(old3) == 1
s = s.replace(
    old3,
    "  private currentStep = 0;\n  // Synchronization event counter (Global Workspace Theory heartbeats)\n  private syncEventCount = 0;",
    1,
)

# 5. Inject sync event check inside executeStep
old4 = """  private async executeStep(): Promise<void> {
    this.currentStep++;
    const stepAddress = this.toStepAddress(this.currentStep);"""
assert s.count(old4) == 1
new4 = """  private async executeStep(): Promise<void> {
    this.currentStep++;
    const stepAddress = this.toStepAddress(this.currentStep);
    // Check for synchronization events (Global Workspace Theory heartbeats)
    if (this.config.enableSynchronizationEvents) {
      this.checkAndEmitSynchronizationEvent(this.currentStep);
    }"""
s = s.replace(old4, new4, 1)

# 6. Add checkAndEmitSynchronizationEvent method before "  /**\n   * Get current state\n   */"
sync_method = """  /**
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

"""

old5 = "  /**\n   * Get current state\n   */\n  public getState():"
assert s.count(old5) == 1
s = s.replace(old5, sync_method + old5, 1)

# 7. Add syncEventCount to getMetrics
old6 = "    streamSaliences: [number, number, number];\n  }"
assert s.count(old6) == 1
s = s.replace(
    old6,
    "    streamSaliences: [number, number, number];\n    syncEventCount: number;\n  }",
    1,
)

old7 = """      streamSaliences: [
        this.streams[0].salience,
        this.streams[1].salience,
        this.streams[2].salience,
      ],
    };
  }
}"""
assert s.count(old7) == 1
s = s.replace(
    old7,
    """      streamSaliences: [
        this.streams[0].salience,
        this.streams[1].salience,
        this.streams[2].salience,
      ],
      syncEventCount: this.syncEventCount,
    };
  }
}""",
    1,
)

with open(PATH, "w") as f:
    f.write(s)
print("V2 patch applied successfully")
print("  SynchronizedChannel exports:", s.count("export type SynchronizedChannel"))
print("  SynchronizationEvent ifc:", s.count("export interface SynchronizationEvent"))
print("  syncEventCount fields:", s.count("private syncEventCount = 0"))
print("  checkAndEmit methods:", s.count("private checkAndEmitSynchronizationEvent"))
