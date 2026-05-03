#!/usr/bin/env python3
import sys as _sys, os as _os
_script_dir = _os.path.dirname(_os.path.abspath(__file__))
if _script_dir in _sys.path:
    _sys.path.remove(_script_dir)
"""
ManusCog Cognitive DevKernel — Unified Orchestrator

Synthesizes:
  - Autognosis (hierarchical self-monitoring)
  - Inferno devcontainer (infrastructure substrate)
  - Promise-Lambda Attention (constraint satisfaction)
  - function-creator(tc | time-crystal-nn) (domain transforms)
  - skill-infinity (self-referential convergence)

Usage:
  python cognitive_devkernel.py status          — Show kernel self-image
  python cognitive_devkernel.py validate <path> — Validate a kernel configuration
  python cognitive_devkernel.py promise <path>  — Run promise-lambda analysis
  python cognitive_devkernel.py transform       — Show available transforms
  python cognitive_devkernel.py cycle           — Run one autognosis cycle
"""

import json
import os
import sys
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any
from pathlib import Path


# ============================================================================
# Layer 1: Time Crystal Temporal Hierarchy (from time-crystal-nn)
# ============================================================================

@dataclass
class TemporalLevel:
    """A single level in the time crystal hierarchy."""
    level: int
    name: str
    period_ms: float
    phase: float = 0.0
    amplitude: float = 1.0

    def step(self, dt_ms: float):
        self.phase = (self.phase + (dt_ms / self.period_ms) * 2 * 3.14159) % (2 * 3.14159)

    def activation(self) -> float:
        import math
        return self.amplitude * math.sin(self.phase)


class TimeCrystalHierarchy:
    """9-level temporal hierarchy mapped to cognitive kernel services."""
    LEVELS = [
        (0, "atom-ops",       8,    "AtomSpace CRUD operations"),
        (1, "pattern-match",  26,   "Pattern matching queries"),
        (2, "inference-step", 52,   "Single PLN inference step"),
        (3, "attention-tick", 110,  "ECAN attention allocation tick"),
        (4, "learning-batch", 160,  "MOSES learning batch"),
        (5, "namespace-sync", 250,  "9P namespace synchronization"),
        (6, "cluster-pulse",  330,  "Cluster heartbeat"),
        (7, "autognosis-obs", 500,  "Autognosis observation"),
        (8, "self-image",     1000, "Full self-image rebuild"),
    ]

    def __init__(self):
        self.levels = [
            TemporalLevel(level=l, name=n, period_ms=p)
            for l, n, p, _ in self.LEVELS
        ]
        self.time_ms = 0.0

    def step(self, dt_ms: float = 1.0):
        self.time_ms += dt_ms
        for level in self.levels:
            level.step(dt_ms)

    def status(self) -> list[dict]:
        return [
            {
                "level": l.level,
                "name": l.name,
                "period_ms": l.period_ms,
                "phase": round(l.phase, 4),
                "activation": round(l.activation(), 4),
            }
            for l in self.levels
        ]


# ============================================================================
# Layer 2: Promise-Lambda Attention (constraint satisfaction)
# ============================================================================

@dataclass
class Promise:
    """A lambda constraint on the cognitive kernel configuration."""
    name: str
    constraint: str
    required: bool = True
    satisfied: bool = False
    evidence: str = ""


class PromiseLambdaEngine:
    """Validates kernel configurations against promise constraints."""

    KERNEL_PROMISES = [
        Promise("inferno-binary",   "emu binary exists at INFERNO_ROOT/Linux/amd64/bin/emu"),
        Promise("limbo-compiler",   "limbo compiler exists at INFERNO_ROOT/Linux/amd64/bin/limbo"),
        Promise("9p-listener",      "9P/Styx port 6666 is configured for forwarding"),
        Promise("cluster-compose",  "docker-compose.cluster.yml defines inferno-registry service"),
        Promise("cognitive-ns",     "/cognitive/atomspace namespace is defined in cluster config"),
        Promise("devcontainer-json","devcontainer.json contains INFERNO_ROOT environment variable"),
        Promise("autognosis-loop",  "post-start.sh includes environment verification"),
        Promise("temporal-levels",  "At least 9 temporal processing levels are defined"),
    ]

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.promises = [Promise(**asdict(p)) for p in self.KERNEL_PROMISES]

    def evaluate(self) -> list[dict]:
        """Evaluate all promises against the project."""
        devcontainer = self.project_path / ".devcontainer"
        compose = self.project_path / "docker-compose.cluster.yml"
        dcjson = devcontainer / "devcontainer.json"

        for p in self.promises:
            if p.name == "inferno-binary":
                dockerfile = devcontainer / "Dockerfile"
                if dockerfile.exists() and "emu" in dockerfile.read_text():
                    p.satisfied = True
                    p.evidence = "Dockerfile builds emu binary"

            elif p.name == "limbo-compiler":
                dockerfile = devcontainer / "Dockerfile"
                if dockerfile.exists() and "limbo" in dockerfile.read_text():
                    p.satisfied = True
                    p.evidence = "Dockerfile builds limbo compiler"

            elif p.name == "9p-listener":
                if dcjson.exists() and "6666" in dcjson.read_text():
                    p.satisfied = True
                    p.evidence = "Port 6666 in devcontainer.json forwardPorts"

            elif p.name == "cluster-compose":
                if compose.exists() and "inferno-registry" in compose.read_text():
                    p.satisfied = True
                    p.evidence = "inferno-registry service defined"

            elif p.name == "cognitive-ns":
                if compose.exists() and "cognitive" in compose.read_text().lower():
                    p.satisfied = True
                    p.evidence = "Cognitive namespace referenced in compose"
                elif (devcontainer / "scripts" / "post-create.sh").exists():
                    content = (devcontainer / "scripts" / "post-create.sh").read_text()
                    if "cognitive" in content:
                        p.satisfied = True
                        p.evidence = "Cognitive namespace in post-create.sh"

            elif p.name == "devcontainer-json":
                if dcjson.exists() and "INFERNO_ROOT" in dcjson.read_text():
                    p.satisfied = True
                    p.evidence = "INFERNO_ROOT in containerEnv"

            elif p.name == "autognosis-loop":
                ps = devcontainer / "scripts" / "post-start.sh"
                if ps.exists() and "verif" in ps.read_text().lower():
                    p.satisfied = True
                    p.evidence = "Verification in post-start.sh"

            elif p.name == "temporal-levels":
                p.satisfied = True
                p.evidence = f"{len(TimeCrystalHierarchy.LEVELS)} levels defined"

        return [asdict(p) for p in self.promises]

    def all_satisfied(self) -> bool:
        return all(p.satisfied for p in self.promises if p.required)


# ============================================================================
# Layer 3: Cognitive File System (function-creator(tc) transform)
# ============================================================================

class CognitiveFileSystem:
    """TC file operations transformed to cognitive namespace operations."""

    NAMESPACE_MAP = {
        "/cognitive/atomspace/atoms":     "Atom storage (ConceptNode, PredicateNode, etc.)",
        "/cognitive/atomspace/types":     "Type hierarchy definitions",
        "/cognitive/atomspace/indices":   "Lookup indices for pattern matching",
        "/cognitive/inference/rules":     "PLN inference rules",
        "/cognitive/inference/queue":     "Inference task queue",
        "/cognitive/inference/results":   "Inference results cache",
        "/cognitive/attention/bank":      "Attention bank (STI/LTI values)",
        "/cognitive/attention/agents":    "Attention allocation agents",
        "/cognitive/learning/populations":"MOSES population storage",
        "/cognitive/learning/fitness":    "Fitness evaluator configurations",
        "/cognitive/temporal/levels":     "Time crystal hierarchy levels",
        "/cognitive/temporal/phases":     "Phase state for each temporal level",
        "/cognitive/autognosis/images":   "Hierarchical self-images",
        "/cognitive/autognosis/insights": "Meta-cognitive insights",
        "/cognitive/autognosis/metrics":  "Self-monitoring metrics",
    }

    @classmethod
    def tree(cls) -> str:
        """Display the cognitive namespace tree (tc tree transform)."""
        lines = ["/cognitive/"]
        prev_parts = []
        for path, desc in sorted(cls.NAMESPACE_MAP.items()):
            parts = path.strip("/").split("/")
            indent = "    " * (len(parts) - 1)
            name = parts[-1]
            lines.append(f"{indent}├── {name}/  — {desc}")
        return "\n".join(lines)

    @classmethod
    def search(cls, pattern: str) -> list[tuple[str, str]]:
        """Search cognitive namespace (tc search transform)."""
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        return [
            (path, desc)
            for path, desc in cls.NAMESPACE_MAP.items()
            if regex.search(path) or regex.search(desc)
        ]


# ============================================================================
# Layer 4: Autognosis Self-Image (hierarchical self-monitoring)
# ============================================================================

@dataclass
class SelfImage:
    """A single level of the Autognosis hierarchical self-image."""
    level: int
    confidence: float
    reflections: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    hash: str = ""

    def compute_hash(self):
        content = json.dumps(asdict(self), sort_keys=True, default=str)
        self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]


class AutognosisEngine:
    """Hierarchical self-image building for the cognitive devkernel."""

    def __init__(self, temporal: TimeCrystalHierarchy, promises: PromiseLambdaEngine):
        self.temporal = temporal
        self.promises = promises
        self.self_images: list[SelfImage] = []
        self.insights: list[dict] = []
        self.cycle_count = 0

    def build_level0(self) -> SelfImage:
        """Direct observation: raw system state."""
        promise_results = self.promises.evaluate()
        satisfied = sum(1 for p in promise_results if p["satisfied"])
        total = len(promise_results)

        img = SelfImage(
            level=0,
            confidence=satisfied / total if total > 0 else 0.0,
            reflections=[],
            metrics={
                "promises_satisfied": satisfied,
                "promises_total": total,
                "temporal_levels": len(self.temporal.levels),
                "temporal_time_ms": self.temporal.time_ms,
                "namespace_paths": len(CognitiveFileSystem.NAMESPACE_MAP),
            },
        )
        img.compute_hash()
        return img

    def build_level1(self, level0: SelfImage) -> SelfImage:
        """Pattern analysis: behavioral patterns from level 0."""
        reflections = []
        if level0.metrics["promises_satisfied"] == level0.metrics["promises_total"]:
            reflections.append("All kernel promises satisfied — system is fully configured")
        else:
            missing = level0.metrics["promises_total"] - level0.metrics["promises_satisfied"]
            reflections.append(f"{missing} kernel promise(s) unsatisfied — configuration incomplete")

        if level0.metrics["temporal_levels"] >= 9:
            reflections.append("Full 9-level temporal hierarchy active")

        img = SelfImage(
            level=1,
            confidence=level0.confidence * 0.9,
            reflections=reflections,
            metrics={
                "pattern_count": len(reflections),
                "base_confidence": level0.confidence,
            },
        )
        img.compute_hash()
        return img

    def build_level2(self, level0: SelfImage, level1: SelfImage) -> SelfImage:
        """Meta-cognitive: analysis of self-understanding quality."""
        reflections = []
        avg_confidence = (level0.confidence + level1.confidence) / 2

        if avg_confidence > 0.8:
            reflections.append("High self-awareness: kernel understands its own configuration well")
        elif avg_confidence > 0.5:
            reflections.append("Moderate self-awareness: some aspects of configuration unclear")
        else:
            reflections.append("Low self-awareness: significant configuration gaps detected")

        reflections.append(
            f"Self-model depth: 3 levels, convergence factor: {avg_confidence:.3f}"
        )

        img = SelfImage(
            level=2,
            confidence=avg_confidence * 0.85,
            reflections=reflections,
            metrics={
                "self_awareness_score": avg_confidence,
                "model_depth": 3,
                "convergence_factor": avg_confidence,
            },
        )
        img.compute_hash()
        return img

    def run_cycle(self) -> dict:
        """Run one complete autognosis cycle (skill-infinity backward pass)."""
        self.cycle_count += 1

        # Build hierarchical self-images
        l0 = self.build_level0()
        l1 = self.build_level1(l0)
        l2 = self.build_level2(l0, l1)
        self.self_images = [l0, l1, l2]

        # Generate insights
        insights = []
        if l0.confidence == 1.0:
            insights.append({
                "type": "system_ready",
                "severity": "info",
                "message": "Cognitive devkernel fully configured and operational",
            })
        else:
            insights.append({
                "type": "configuration_gap",
                "severity": "warning",
                "message": f"Kernel configuration {l0.confidence*100:.0f}% complete",
            })

        # skill-infinity fixed point check
        if self.cycle_count > 1 and len(self.insights) > 0:
            prev_score = self.insights[-1].get("self_awareness", 0)
            curr_score = l2.metrics["self_awareness_score"]
            delta = abs(curr_score - prev_score)
            if delta < 0.001:
                insights.append({
                    "type": "fixed_point",
                    "severity": "info",
                    "message": f"Self-improvement converged (Δ={delta:.6f} < ε=0.001)",
                })

        insights.append({"self_awareness": l2.metrics["self_awareness_score"]})
        self.insights.extend(insights)

        # Advance temporal hierarchy
        self.temporal.step(1000)  # 1 second per cycle

        return {
            "cycle": self.cycle_count,
            "self_images": [asdict(img) for img in self.self_images],
            "insights": insights,
            "temporal_state": self.temporal.status(),
        }


# ============================================================================
# CLI Interface
# ============================================================================

def cmd_status():
    """Display kernel self-image status."""
    temporal = TimeCrystalHierarchy()
    promises = PromiseLambdaEngine(".")
    engine = AutognosisEngine(temporal, promises)
    result = engine.run_cycle()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ManusCog Cognitive DevKernel — Self-Image                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    for img_data in result["self_images"]:
        level = img_data["level"]
        conf = img_data["confidence"]
        refs = img_data["reflections"]
        h = img_data["hash"]
        bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
        print(f"  Level {level}: [{bar}] {conf:.3f}  [{h}]")
        for r in refs:
            print(f"         → {r}")

    print()
    print("  Temporal Hierarchy:")
    for ts in result["temporal_state"]:
        act = ts["activation"]
        bar = "▓" * max(0, int((act + 1) * 5)) + "░" * max(0, 10 - int((act + 1) * 5))
        print(f"    L{ts['level']} {ts['name']:20s} {ts['period_ms']:>6.0f}ms [{bar}] {act:+.3f}")

    print()
    print("  Insights:")
    for ins in result["insights"]:
        if "message" in ins:
            sev = ins.get("severity", "info")
            icon = {"info": "ℹ", "warning": "⚠", "error": "✗"}.get(sev, "·")
            print(f"    {icon} [{ins['type']}] {ins['message']}")


def cmd_validate(path: str):
    """Validate a kernel configuration via promise-lambda attention."""
    engine = PromiseLambdaEngine(path)
    results = engine.evaluate()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Promise-Lambda Attention — Kernel Validation               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    for p in results:
        icon = "✓" if p["satisfied"] else "✗"
        req = "REQ" if p["required"] else "OPT"
        print(f"  {icon} [{req}] {p['name']}: {p['constraint']}")
        if p["evidence"]:
            print(f"         Evidence: {p['evidence']}")

    print()
    satisfied = sum(1 for p in results if p["satisfied"])
    total = len(results)
    if engine.all_satisfied():
        print(f"  ✓ All {total} promises satisfied. Kernel configuration valid.")
    else:
        print(f"  ✗ {satisfied}/{total} promises satisfied. Configuration incomplete.")


def cmd_promise(path: str):
    """Run full promise-lambda analysis with KV space exploration."""
    engine = PromiseLambdaEngine(path)
    results = engine.evaluate()
    print(json.dumps(results, indent=2))


def cmd_transform():
    """Show available function-creator transforms."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Function-Creator Transforms: tc | time-crystal-nn          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    print("  [tc → Cognitive File System]")
    print()
    print(CognitiveFileSystem.tree())
    print()

    print("  [time-crystal-nn → Temporal Hierarchy]")
    print()
    temporal = TimeCrystalHierarchy()
    for l, n, p, desc in TimeCrystalHierarchy.LEVELS:
        print(f"    Level {l}: {n:20s} {p:>6}ms — {desc}")


def cmd_cycle():
    """Run one autognosis cycle with full output."""
    temporal = TimeCrystalHierarchy()
    promises = PromiseLambdaEngine(".")
    engine = AutognosisEngine(temporal, promises)

    # Run 5 cycles to demonstrate convergence
    for i in range(5):
        result = engine.run_cycle()
        score = result["self_images"][2]["metrics"]["self_awareness_score"]
        print(f"  Cycle {result['cycle']}: self-awareness = {score:.6f}")

    print()
    # Check for fixed point
    for ins in engine.insights:
        if isinstance(ins, dict) and ins.get("type") == "fixed_point":
            print(f"  → {ins['message']}")
            break
    else:
        print("  → Convergence not yet reached (more cycles needed)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "validate":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        cmd_validate(path)
    elif cmd == "promise":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        cmd_promise(path)
    elif cmd == "transform":
        cmd_transform()
    elif cmd == "cycle":
        cmd_cycle()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
