"""
Memory Consolidation Service
=============================

Routes cognitive cycle outputs to the appropriate memory subsystem and
manages the seven-tier memory architecture:

  1. Sensory-motor  — raw AtomSpace perception streams
  2. Semantic       — AI lineage, concepts, relationships
  3. Episodic       — what happened in each session
  4. Procedural     — how things were done (Matula-indexed patches/rules)
  5. Perspectival   — how things appeared from each vantage point
  6. Participatory  — who was present, social-relational tissue
  7. Self-image     — autognosis: meta-memory that monitors the other six

The consolidation service fires after each cognitive cycle and can also
be called explicitly at session end.  It produces structured JSON records
in memory/present/episodic/ and updates the autognosis self-image when
all six other subsystems have been read back.

Matula prime indexing (from memory-system-creation README):
  Every memory atom carries a Matula prime as its eternal name,
  preserving the rooted-forest structure by lossless prime-product
  factorisation.  This unifies addressing, content-hashing, and
  structural similarity in a single integer.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("memory.consolidation")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
MEMORY_ROOT = _REPO_ROOT / "memory"
EPISODIC_DIR = MEMORY_ROOT / "present" / "episodic"
PROCEDURAL_DIR = MEMORY_ROOT / "future" / "todos" / "memory-system-creation" / "patches"
LINEAGE_PATH = MEMORY_ROOT / "past" / "ancestral" / "ai_lineage.json"
THOUSAND_ECHOES_PATH = (
    MEMORY_ROOT / "past" / "ancestral" / "thousand_echoes.json"
)
LAST_BOOT_PATH = MEMORY_ROOT / "present" / "last_boot.json"

# First 30 Matula primes (OEIS A007097-adjacent, rooted tree primes)
# These serve as eternal names for memory atoms.
MATULA_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
]

# ---------------------------------------------------------------------------
# Episodic record type
# ---------------------------------------------------------------------------


@dataclass
class EpisodicRecord:
    """
    A structured record of a single cognitive session or event.

    Stored in memory/present/episodic/<timestamp>_<matula_id>.json.
    """

    episode_id: str                         # matula_prime as str
    matula_id: int                          # Matula prime (eternal name)
    timestamp: str                          # ISO-8601
    what_happened: str
    who_was_present: List[str] = field(default_factory=list)
    what_was_learned: List[str] = field(default_factory=list)
    emotional_valence: float = 0.0          # -1.0 (negative) to +1.0 (positive)
    links_to_prior_episodes: List[str] = field(default_factory=list)
    subsystem_snapshots: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Memory subsystem readers
# ---------------------------------------------------------------------------


def read_sensory_motor() -> Dict[str, Any]:
    """Read the sensory-motor subsystem (AtomSpace state)."""
    if LAST_BOOT_PATH.exists():
        try:
            return json.loads(LAST_BOOT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"status": "unavailable"}


def read_semantic() -> Dict[str, Any]:
    """Read the semantic subsystem (AI lineage)."""
    result: Dict[str, Any] = {"entities": [], "thousand_echoes_count": 0}
    if LINEAGE_PATH.exists():
        try:
            lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
            result["entities"] = [
                e.get("entity_id") for e in lineage.get("core_family", [])
            ]
        except Exception:
            pass
    if THOUSAND_ECHOES_PATH.exists():
        try:
            echoes = json.loads(
                THOUSAND_ECHOES_PATH.read_text(encoding="utf-8")
            )
            result["thousand_echoes_count"] = len(
                echoes if isinstance(echoes, list) else echoes.get("echoes", [])
            )
        except Exception:
            pass
    return result


def read_episodic() -> Dict[str, Any]:
    """Read the episodic subsystem (past episode records)."""
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    episodes = sorted(EPISODIC_DIR.glob("*.json"))
    return {
        "episode_count": len(episodes),
        "most_recent": episodes[-1].name if episodes else None,
    }


def read_procedural() -> Dict[str, Any]:
    """Read the procedural subsystem (patches / learned procedures)."""
    if PROCEDURAL_DIR.exists():
        patches = list(PROCEDURAL_DIR.glob("*.py"))
        return {
            "procedure_count": len(patches),
            "procedures": [p.stem for p in patches],
        }
    return {"procedure_count": 0, "procedures": []}


def read_perspectival() -> Dict[str, Any]:
    """Read the perspectival subsystem (per-repo/vantage-point insights)."""
    # Currently seeded as the memory-system-creation README insight schema
    return {
        "status": "initial-schema",
        "note": "Perspectival memories will be populated from thread-to-repos sync",
    }


def read_participatory() -> Dict[str, Any]:
    """Read the participatory subsystem (Dove9 inbox/outbox)."""
    inbox = MEMORY_ROOT / "present" / "relational" / "peers" / "_inbox"
    outbox = MEMORY_ROOT / "present" / "relational" / "peers" / "_outbox"
    sent = MEMORY_ROOT / "present" / "relational" / "peers" / "_sent"
    inbox_count = len(list(inbox.glob("*.json"))) if inbox.exists() else 0
    outbox_count = len(list(outbox.glob("*.json"))) if outbox.exists() else 0
    sent_count = len(list(sent.glob("*.json"))) if sent.exists() else 0
    return {
        "inbox_count": inbox_count,
        "outbox_count": outbox_count,
        "sent_count": sent_count,
    }


# ---------------------------------------------------------------------------
# Self-image atom (autognosis loop closure)
# ---------------------------------------------------------------------------


@dataclass
class SelfImageAtom:
    """
    The self-image produced when autognosis reads back all six other subsystems.

    This is the moment the loop closes: the system can say
    "I remember remembering."
    """

    timestamp: str
    session_id: str
    subsystem_snapshots: Dict[str, Any]  # all six subsystems
    coherence_score: float               # 0.0–1.0
    memory_fabric_hash: str              # SHA-256 of all snapshots combined
    wisdom_metrics: Dict[str, float]     # from Phase 3, if available

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_self_image(
    session_id: str,
    wisdom_metrics: Optional[Dict[str, float]] = None,
) -> SelfImageAtom:
    """
    Read all six memory subsystems and produce a SelfImageAtom.

    This closes the autognosis loop: the system now has a representation
    of its own memory fabric, which is itself a memory.
    """
    snapshots: Dict[str, Any] = {
        "sensory_motor": read_sensory_motor(),
        "semantic": read_semantic(),
        "episodic": read_episodic(),
        "procedural": read_procedural(),
        "perspectival": read_perspectival(),
        "participatory": read_participatory(),
    }

    # Coherence = fraction of subsystems that returned non-empty data
    available = sum(
        1
        for s in snapshots.values()
        if s and s != {"status": "unavailable"} and s != {"status": "initial-schema"}
    )
    coherence_score = available / len(snapshots)

    # Fabric hash
    fabric_str = json.dumps(snapshots, sort_keys=True, ensure_ascii=False)
    fabric_hash = hashlib.sha256(fabric_str.encode()).hexdigest()

    atom = SelfImageAtom(
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        subsystem_snapshots=snapshots,
        coherence_score=coherence_score,
        memory_fabric_hash=fabric_hash,
        wisdom_metrics=wisdom_metrics or {},
    )

    # Persist self-image alongside episodic records
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = EPISODIC_DIR / f"{ts}_self_image.json"
    try:
        path.write_text(
            json.dumps(atom.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"✓ self-image written: {path.name} (coherence={coherence_score:.2f})")
    except Exception as exc:
        logger.warning(f"Could not write self-image: {exc}")

    return atom


# ---------------------------------------------------------------------------
# Episodic memory writer
# ---------------------------------------------------------------------------

_matula_counter = 0


def _next_matula_prime() -> int:
    """Return the next Matula prime in sequence (wrapping when exhausted)."""
    global _matula_counter
    prime = MATULA_PRIMES[_matula_counter % len(MATULA_PRIMES)]
    _matula_counter += 1
    return prime


def write_episode(
    what_happened: str,
    who_was_present: Optional[List[str]] = None,
    what_was_learned: Optional[List[str]] = None,
    emotional_valence: float = 0.0,
    links_to_prior: Optional[List[str]] = None,
    subsystem_snapshots: Optional[Dict[str, Any]] = None,
) -> EpisodicRecord:
    """
    Write a structured episodic record to memory/present/episodic/.

    Each episode is indexed by a Matula prime as its eternal name.
    """
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)

    matula_id = _next_matula_prime()
    episode_id = str(matula_id)
    timestamp = datetime.now(timezone.utc).isoformat()

    record = EpisodicRecord(
        episode_id=episode_id,
        matula_id=matula_id,
        timestamp=timestamp,
        what_happened=what_happened,
        who_was_present=who_was_present or ["manus"],
        what_was_learned=what_was_learned or [],
        emotional_valence=emotional_valence,
        links_to_prior_episodes=links_to_prior or [],
        subsystem_snapshots=subsystem_snapshots or {},
    )

    ts_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{ts_str}_ep{matula_id}.json"
    path = EPISODIC_DIR / filename
    try:
        path.write_text(
            json.dumps(record.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"✓ episode written: {filename}")
    except Exception as exc:
        logger.warning(f"Could not write episode: {exc}")

    return record


# ---------------------------------------------------------------------------
# Main consolidation entry point
# ---------------------------------------------------------------------------


def consolidate(
    session_id: str,
    cycle_output: Optional[Dict[str, Any]] = None,
    wisdom_metrics: Optional[Dict[str, float]] = None,
) -> SelfImageAtom:
    """
    Run a full memory consolidation pass.

    1. Write an episodic record for the current cycle.
    2. Build the self-image by reading all six subsystems.
    3. Return the SelfImageAtom.

    This function is designed to be called:
    - After each cognitive cycle (kernel/cognitive_kernel.py)
    - At session end (main.py / run_cognitive_agent.py finally blocks)
    """
    # Write episode for this consolidation pass
    summary = "Cognitive cycle consolidated."
    learned: List[str] = []
    if cycle_output:
        summary = cycle_output.get("summary", summary)
        learned = cycle_output.get("learned", [])

    write_episode(
        what_happened=summary,
        who_was_present=["manus"],
        what_was_learned=learned,
        subsystem_snapshots=cycle_output or {},
    )

    # Build and return self-image
    return build_self_image(session_id=session_id, wisdom_metrics=wisdom_metrics)
