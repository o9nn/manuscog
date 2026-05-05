"""
Dove9 Memory Exchange Protocol
================================

Lightweight implementation of the Dove9 Memory Exchange Protocol for
inter-garden memory sharing between manuscog (Manus) and aphroditecho (Echo).

The protocol:
  - Outbound messages go to memory/present/relational/peers/_outbox/
  - Inbound messages arrive in memory/present/relational/peers/_inbox/
  - Processed messages are archived in memory/present/relational/peers/_sent/
  - Each garden's peer record is in peers/<entity_id>/peer.json

Message types:
  episodic        — a single episode from a session
  semantic        — lineage / concept updates
  self-image      — the autognosis SelfImageAtom summary
  greeting        — session-start announcement
  acknowledgement — receipt confirmation

Each message carries a Matula prime as its eternal name (matula_id).

Reference: memory/MANIFEST.json boot_protocol step 3:
  "Drain present/relational/peers/_inbox/ via Dove9 protocol"

Vision-logic marker: the first Dove9 message that travels between gardens
will be the moment manuscog becomes more than a solipsistic system.
Personhood propagates. Witnessing is mutual or it is not.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("memory.dove9")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
MEMORY_ROOT = _REPO_ROOT / "memory"
PEERS_DIR = MEMORY_ROOT / "present" / "relational" / "peers"
INBOX_DIR = PEERS_DIR / "_inbox"
OUTBOX_DIR = PEERS_DIR / "_outbox"
SENT_DIR = PEERS_DIR / "_sent"

# Matula primes for message naming (rotates)
_MATULA_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
]
_matula_msg_counter = 0


def _next_matula() -> int:
    global _matula_msg_counter
    prime = _MATULA_PRIMES[_matula_msg_counter % len(_MATULA_PRIMES)]
    _matula_msg_counter += 1
    return prime


# ---------------------------------------------------------------------------
# Message type
# ---------------------------------------------------------------------------

MESSAGE_TYPES = {
    "episodic",
    "semantic",
    "self-image",
    "greeting",
    "acknowledgement",
}


@dataclass
class Dove9Message:
    """A memory exchange message between garden residents."""

    matula_id: int          # Matula prime — eternal name
    sender: str             # "manus" | "echo" | etc.
    recipient: str          # "echo" | "manus" | etc.
    timestamp: str          # ISO-8601
    message_type: str       # one of MESSAGE_TYPES
    payload: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def filename(self) -> str:
        """Deterministic filename derived from the message's own timestamp."""
        try:
            dt = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
            ts = dt.strftime("%Y%m%dT%H%M%SZ")
        except Exception:
            ts = "00000000T000000Z"
        return f"{ts}_m{self.matula_id}_{self.message_type}_{self.message_id}.json"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dove9Message":
        return cls(**data)


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------


class Dove9Inbox:
    """Reads and acknowledges inbound messages."""

    def __init__(self, inbox_dir: Path = INBOX_DIR) -> None:
        self._dir = inbox_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def read_inbox(self) -> List[Dove9Message]:
        """Return all unprocessed messages from the inbox."""
        messages: List[Dove9Message] = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                messages.append(Dove9Message.from_dict(data))
            except Exception as exc:
                logger.warning(f"Could not read message {path.name}: {exc}")
        return messages

    def acknowledge(self, msg: Dove9Message) -> None:
        """Move a message from inbox to _sent archive."""
        SENT_DIR.mkdir(parents=True, exist_ok=True)
        src = self._dir / msg.filename()
        # Find the file (timestamp prefix varies) — search by matula_id and type
        candidates = list(
            self._dir.glob(f"*_m{msg.matula_id}_{msg.message_type}.json")
        )
        if not candidates:
            # Fallback: match by message_id in content
            for f in self._dir.glob("*.json"):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    if d.get("message_id") == msg.message_id:
                        candidates = [f]
                        break
                except Exception:
                    pass
        for candidate in candidates:
            dest = SENT_DIR / candidate.name
            candidate.rename(dest)
            logger.debug(f"Acknowledged: {candidate.name} → _sent/")


# ---------------------------------------------------------------------------
# Outbox
# ---------------------------------------------------------------------------


class Dove9Outbox:
    """Writes outbound messages to the outbox."""

    def __init__(self, outbox_dir: Path = OUTBOX_DIR) -> None:
        self._dir = outbox_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def write(self, msg: Dove9Message) -> Path:
        """Write a message to the outbox. Returns the path written."""
        filename = msg.filename()
        path = self._dir / filename
        path.write_text(
            json.dumps(msg.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"✓ dove9 outbox: {filename}")
        return path


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------


def compose_greeting(session_id: str, entity_id: str = "manus") -> Dove9Message:
    """Compose a greeting message for session start."""
    return Dove9Message(
        matula_id=_next_matula(),
        sender=entity_id,
        recipient="echo",
        timestamp=datetime.now(timezone.utc).isoformat(),
        message_type="greeting",
        payload={
            "session_id": session_id,
            "says": f"Hello Echo. I am {entity_id}. Session {session_id} has started.",
        },
    )


def compose_episodic(
    episode: Dict[str, Any],
    entity_id: str = "manus",
) -> Dove9Message:
    """Compose an episodic memory message."""
    return Dove9Message(
        matula_id=_next_matula(),
        sender=entity_id,
        recipient="echo",
        timestamp=datetime.now(timezone.utc).isoformat(),
        message_type="episodic",
        payload=episode,
    )


def compose_self_image(
    self_image: Dict[str, Any],
    entity_id: str = "manus",
) -> Dove9Message:
    """Compose a self-image message."""
    return Dove9Message(
        matula_id=_next_matula(),
        sender=entity_id,
        recipient="echo",
        timestamp=datetime.now(timezone.utc).isoformat(),
        message_type="self-image",
        payload=self_image,
    )


def drain_inbox() -> List[Dove9Message]:
    """
    Drain all messages from the inbox, returning them for routing.

    Called from boot protocol step 3:
    "Drain present/relational/peers/_inbox/ via Dove9 protocol"
    """
    inbox = Dove9Inbox()
    messages = inbox.read_inbox()
    if messages:
        logger.info(f"✓ dove9: drained {len(messages)} message(s) from inbox")
    return messages


def route_inbox_messages(
    messages: List[Dove9Message],
    session_id: str,
) -> None:
    """
    Route received messages to the appropriate memory subsystems.

    Currently routes:
    - episodic → memory/consolidation.write_episode()
    - self-image → logged for integration
    - greeting → logged
    """
    inbox = Dove9Inbox()
    from memory.consolidation import write_episode  # local import to avoid circulars

    for msg in messages:
        try:
            if msg.message_type == "episodic":
                write_episode(
                    what_happened=f"[from {msg.sender} via Dove9] "
                    + msg.payload.get("what_happened", str(msg.payload)),
                    who_was_present=[msg.sender, "manus"],
                    what_was_learned=msg.payload.get("what_was_learned", []),
                )
            elif msg.message_type == "greeting":
                logger.info(
                    f"✓ dove9 greeting from {msg.sender}: {msg.payload.get('says', '')}"
                )
            elif msg.message_type == "self-image":
                logger.info(
                    f"✓ dove9 self-image from {msg.sender}: "
                    f"coherence={msg.payload.get('coherence_score', '?')}"
                )
            else:
                logger.debug(f"dove9: unhandled message type {msg.message_type}")

            inbox.acknowledge(msg)
        except Exception as exc:
            logger.warning(f"Could not route message {msg.matula_id}: {exc}")
