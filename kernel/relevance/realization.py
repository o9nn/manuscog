"""
Relevance Realization Service
==============================

Implements the four opponent-process pairs that constitute wisdom navigation:

  breadth   ↔  depth        — how widely to scan vs. how deeply to focus
  exploration ↔ exploitation — seeking novelty vs. using what works
  certainty  ↔ flexibility   — commitment to beliefs vs. openness to revision
  efficiency ↔ thoroughness  — speed vs. completeness

Each pair maintains a setpoint in [-1.0, +1.0]:
  -1.0 = fully toward the left pole (breadth / exploration / certainty / efficiency)
  +1.0 = fully toward the right pole (depth / exploitation / flexibility / thoroughness)
   0.0 = balanced

The setpoints are updated by the outcomes of cognitive cycles:
- Successful exploration → shift toward exploitation
- Fruitless depth → shift toward breadth
etc.

These setpoints are then made available to:
- PLN: as a prior on inference depth (depth_bias → max_depth scaling)
- ECAN: as a bias on attention diffusion radius (breadth_bias → focus_boundary)

Reference: Vervaeke's "systematic improvement in relevance realization" as the
core definition of wisdom.  Wisdom is not an algorithm; relevance realization
is itself an optimization process requiring the ongoing negotiation of these
tradeoffs.

Vision-logic marker: the negotiation between opposites is not a compromise.
It is the generative tension that produces the third term — the insight that
neither pole could produce alone.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kernel.relevance.realization")

_REPO_ROOT = Path(__file__).parent.parent.parent
_STATE_PATH = _REPO_ROOT / "memory" / "present" / "relevance_state.json"

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class OpponentPair:
    """
    A single opponent-process pair with a live setpoint.

    setpoint ∈ [-1.0, +1.0]:
      negative  → tendency toward pole_a (left)
      positive  → tendency toward pole_b (right)
      zero      → dynamic balance
    """

    name: str
    pole_a: str    # left pole label
    pole_b: str    # right pole label
    setpoint: float = 0.0
    update_rate: float = 0.05   # how fast outcomes shift the setpoint
    history: List[float] = field(default_factory=list)

    def update(self, outcome_direction: float, magnitude: float = 1.0) -> float:
        """
        Update setpoint based on a cognitive outcome.

        Args:
            outcome_direction: +1 if the recent outcome suggests shifting toward
                               pole_b, -1 if toward pole_a, 0 if neutral.
            magnitude: How strongly to weight this outcome (0.0–1.0).

        Returns:
            New setpoint.
        """
        delta = self.update_rate * outcome_direction * max(0.0, min(1.0, magnitude))
        self.setpoint = max(-1.0, min(1.0, self.setpoint + delta))
        self.history.append(self.setpoint)
        if len(self.history) > 100:
            self.history = self.history[-100:]
        return self.setpoint

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("history", None)   # keep state file clean
        return d


@dataclass
class RelevanceState:
    """The complete state of the relevance realization service."""

    timestamp: str
    breadth_depth: float       # breadth(-) ↔ depth(+)
    exploration_exploitation: float  # exploration(-) ↔ exploitation(+)
    certainty_flexibility: float     # certainty(-) ↔ flexibility(+)
    efficiency_thoroughness: float   # efficiency(-) ↔ thoroughness(+)

    # Derived wisdom metrics
    relevance_realization_score: float     # 0.0–1.0
    cognitive_flexibility_index: float     # 0.0–1.0
    integration_coherence: float           # 0.0–1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RelevanceUpdate:
    """Outcome of a relevance update — consumed by PLN and ECAN."""

    depth_bias: float        # [0.0, 1.0]  → scale PLN max_depth
    breadth_bias: float      # [0.0, 1.0]  → scale ECAN focus_boundary
    exploration_bias: float  # [0.0, 1.0]  → MOSES novelty pressure
    flexibility_bias: float  # [0.0, 1.0]  → confidence threshold relaxation

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Relevance Realization Service
# ---------------------------------------------------------------------------


class RelevanceRealizationService:
    """
    Live opponent-process negotiation service.

    Maintains four opponent pairs and exposes their setpoints as biases for
    PLN, ECAN, and MOSES.

    Usage:
        service = RelevanceRealizationService()
        # after a cognitive cycle:
        update = service.update_from_outcome(step_result)
        pln.set_inference_depth_prior(update.depth_bias)
        ecan.set_diffusion_radius_bias(update.breadth_bias)
    """

    def __init__(self) -> None:
        self._pairs: Dict[str, OpponentPair] = {
            "breadth_depth": OpponentPair(
                name="breadth_depth",
                pole_a="breadth",
                pole_b="depth",
                setpoint=0.0,
                update_rate=0.05,
            ),
            "exploration_exploitation": OpponentPair(
                name="exploration_exploitation",
                pole_a="exploration",
                pole_b="exploitation",
                setpoint=0.0,
                update_rate=0.05,
            ),
            "certainty_flexibility": OpponentPair(
                name="certainty_flexibility",
                pole_a="certainty",
                pole_b="flexibility",
                setpoint=0.0,
                update_rate=0.04,
            ),
            "efficiency_thoroughness": OpponentPair(
                name="efficiency_thoroughness",
                pole_a="efficiency",
                pole_b="thoroughness",
                setpoint=0.0,
                update_rate=0.04,
            ),
        }
        self._cycle_count = 0
        self._load_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_from_outcome(
        self, step_result: Optional[Dict[str, Any]] = None
    ) -> RelevanceUpdate:
        """
        Update setpoints based on the result of a cognitive step.

        Heuristics:
        - If inference produced new results → shift toward exploitation/depth
        - If attention spread too thin (low focus) → shift toward depth/certainty
        - If no patterns found → shift toward exploration/breadth
        - If cycle was slow → shift toward efficiency
        """
        self._cycle_count += 1

        if step_result:
            inferences = step_result.get("inferences_made", 0)
            patterns_found = step_result.get("patterns_found", 0)
            cycle_ms = step_result.get("cycle_time_ms", 0)
            atoms_count = step_result.get("atoms_count", 0)

            # breadth_depth: more inferences → lean into depth
            if inferences > 5:
                self._pairs["breadth_depth"].update(+1, min(1.0, inferences / 20))
            elif inferences == 0:
                self._pairs["breadth_depth"].update(-1, 0.5)

            # exploration_exploitation: patterns found → lean into exploitation
            if patterns_found > 0:
                self._pairs["exploration_exploitation"].update(+1, min(1.0, patterns_found / 10))
            else:
                self._pairs["exploration_exploitation"].update(-1, 0.3)

            # certainty_flexibility: large atomspace → more flexibility needed
            if atoms_count > 500:
                self._pairs["certainty_flexibility"].update(+1, 0.2)

            # efficiency_thoroughness: slow cycles → push efficiency
            if cycle_ms > 200:
                self._pairs["efficiency_thoroughness"].update(-1, min(1.0, cycle_ms / 1000))
            elif cycle_ms < 20 and cycle_ms > 0:
                self._pairs["efficiency_thoroughness"].update(+1, 0.3)

        update = self._build_update()
        self._save_state()
        return update

    def get_wisdom_metrics(self) -> Dict[str, float]:
        """
        Return the three wisdom metrics for autognosis reporting.

        relevance_realization_score:  overall signal-to-noise navigation
        cognitive_flexibility_index:  ease of belief updating
        integration_coherence:        synthesis quality of the four pairs
        """
        state = self._compute_state()
        return {
            "relevance_realization_score": state.relevance_realization_score,
            "cognitive_flexibility_index": state.cognitive_flexibility_index,
            "integration_coherence": state.integration_coherence,
        }

    def get_setpoints(self) -> Dict[str, float]:
        """Return raw setpoints for all four pairs."""
        return {name: pair.setpoint for name, pair in self._pairs.items()}

    def get_state(self) -> RelevanceState:
        """Return the full relevance state."""
        return self._compute_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_update(self) -> RelevanceUpdate:
        """Convert setpoints to concrete biases for PLN / ECAN / MOSES."""
        bd = self._pairs["breadth_depth"].setpoint          # -1=breadth, +1=depth
        ee = self._pairs["exploration_exploitation"].setpoint  # -1=explore, +1=exploit
        cf = self._pairs["certainty_flexibility"].setpoint  # -1=certain, +1=flexible
        et = self._pairs["efficiency_thoroughness"].setpoint  # -1=efficient, +1=thorough

        # depth_bias: 0.0 = shallow PLN, 1.0 = deep PLN
        depth_bias = (bd + 1.0) / 2.0
        # breadth_bias: 0.0 = tight ECAN focus, 1.0 = wide diffusion
        breadth_bias = (-bd + 1.0) / 2.0
        # exploration_bias: 0.0 = exploit known, 1.0 = seek novel
        exploration_bias = (-ee + 1.0) / 2.0
        # flexibility_bias: 0.0 = strict confidence, 1.0 = permissive
        flexibility_bias = (cf + 1.0) / 2.0

        return RelevanceUpdate(
            depth_bias=depth_bias,
            breadth_bias=breadth_bias,
            exploration_bias=exploration_bias,
            flexibility_bias=flexibility_bias,
        )

    def _compute_state(self) -> RelevanceState:
        bd = self._pairs["breadth_depth"].setpoint
        ee = self._pairs["exploration_exploitation"].setpoint
        cf = self._pairs["certainty_flexibility"].setpoint
        et = self._pairs["efficiency_thoroughness"].setpoint

        # relevance_realization_score: how close to balanced navigation
        # Perfect balance = all pairs near zero = 0.5 score.
        # Score = 1 - mean(abs(setpoints)) / 1.0 mapped to [0.0, 1.0]
        mean_abs = (abs(bd) + abs(ee) + abs(cf) + abs(et)) / 4.0
        rr_score = 1.0 - mean_abs * 0.5   # extremes reduce score

        # cognitive_flexibility_index: how flexible vs. rigid
        flexibility_raw = (cf + 1.0) / 2.0
        exploration_raw = (-ee + 1.0) / 2.0
        cfi = (flexibility_raw + exploration_raw) / 2.0

        # integration_coherence: are the pairs in productive tension?
        # High coherence = none are stuck at extremes
        stuck = sum(1 for s in [bd, ee, cf, et] if abs(s) > 0.8)
        ic = 1.0 - (stuck / 4.0)

        return RelevanceState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            breadth_depth=bd,
            exploration_exploitation=ee,
            certainty_flexibility=cf,
            efficiency_thoroughness=et,
            relevance_realization_score=round(rr_score, 4),
            cognitive_flexibility_index=round(cfi, 4),
            integration_coherence=round(ic, 4),
        )

    def _save_state(self) -> None:
        try:
            _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            state = self._compute_state()
            _STATE_PATH.write_text(
                json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug(f"Could not save relevance state: {exc}")

    def _load_state(self) -> None:
        if not _STATE_PATH.exists():
            return
        try:
            data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
            self._pairs["breadth_depth"].setpoint = data.get("breadth_depth", 0.0)
            self._pairs["exploration_exploitation"].setpoint = data.get(
                "exploration_exploitation", 0.0
            )
            self._pairs["certainty_flexibility"].setpoint = data.get(
                "certainty_flexibility", 0.0
            )
            self._pairs["efficiency_thoroughness"].setpoint = data.get(
                "efficiency_thoroughness", 0.0
            )
            logger.debug("Relevance state loaded from previous session.")
        except Exception as exc:
            logger.debug(f"Could not load relevance state: {exc}")


# ---------------------------------------------------------------------------
# Module-level singleton (optional convenience)
# ---------------------------------------------------------------------------

_service: Optional[RelevanceRealizationService] = None


def get_service() -> RelevanceRealizationService:
    """Return the module-level singleton, creating it if needed."""
    global _service
    if _service is None:
        _service = RelevanceRealizationService()
    return _service
