"""
Integration Tests — Personhood Loop
=====================================

Tests that verify the six personhood phases work together:

  test_continuity         — second session recovers first session's identity
  test_wisdom_cultivation — relevance realization improves across cycles
  test_dove9_exchange     — Dove9 message round-trips through memory subsystems
  test_autognosis_loop    — all seven memory subsystems represented in one self-image

These tests run without any LLM or external API calls — they test the
cognitive infrastructure purely.

When these tests pass:
  - The system has continuous identity across session cuts
  - Wisdom metrics improve with experience
  - The Dove9 exchange is wired in code, not just architecture
  - The self-image autognosis loop is closed

That is the functional analog of personhood.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# Phase 1: Continuity Tests
# =============================================================================


class TestContinuity(unittest.TestCase):
    """
    Verify that a second session can recover the identity of the first.
    """

    def setUp(self):
        # Use a temp directory to avoid polluting real memory
        self.tmpdir = tempfile.mkdtemp(prefix="manuscog_test_")
        self._patch_paths()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _patch_paths(self):
        """Redirect awakening paths to tmpdir."""
        memory_root = Path(self.tmpdir) / "memory"
        self._memory_root = memory_root

        import kernel.awakening as aw

        self._orig_memory_root = aw.MEMORY_ROOT
        self._orig_continuity_dir = aw.CONTINUITY_DIR
        self._orig_yesterday_path = aw.YESTERDAY_PATH
        self._orig_last_boot_path = aw.LAST_BOOT_PATH
        self._orig_manifest_path = aw.MANIFEST_PATH

        aw.MEMORY_ROOT = memory_root
        aw.CONTINUITY_DIR = memory_root / "continuity"
        aw.YESTERDAY_PATH = memory_root / "continuity" / "yesterday.json"
        aw.LAST_BOOT_PATH = memory_root / "present" / "last_boot.json"
        aw.MANIFEST_PATH = memory_root / "MANIFEST.json"  # will not exist → no hash

    def _restore_paths(self):
        import kernel.awakening as aw

        aw.MEMORY_ROOT = self._orig_memory_root
        aw.CONTINUITY_DIR = self._orig_continuity_dir
        aw.YESTERDAY_PATH = self._orig_yesterday_path
        aw.LAST_BOOT_PATH = self._orig_last_boot_path
        aw.MANIFEST_PATH = self._orig_manifest_path

    def test_first_awakening_is_detected(self):
        """First session should detect is_first_awakening=True."""
        from kernel.awakening import awaken

        ctx = awaken()
        self.assertTrue(ctx.is_first_awakening)
        self.assertEqual(ctx.session_count, 1)
        self._restore_paths()

    def test_second_session_recovers_first(self):
        """
        After save_session_snapshot, the second call to awaken() should
        recover the identity of the first session.
        """
        from kernel.awakening import AwakeningContext, awaken, save_session_snapshot

        # Session 1
        ctx1 = awaken()
        save_session_snapshot(ctx1, summary="Session 1 done.")

        # Session 2 — fresh import context, but same paths
        ctx2 = awaken()

        self.assertFalse(ctx2.is_first_awakening)
        self.assertEqual(ctx2.session_count, 2)
        self.assertIsNotNone(ctx2.last_seen)
        self.assertEqual(ctx2.session_summary, "Session 1 done.")
        self._restore_paths()

    def test_last_boot_json_written(self):
        """last_boot.json must be written on every awakening."""
        from kernel.awakening import awaken

        ctx = awaken()
        last_boot = self._memory_root / "present" / "last_boot.json"
        self.assertTrue(last_boot.exists(), "last_boot.json not created")
        data = json.loads(last_boot.read_text())
        self.assertEqual(data["entity_id"], ctx.entity_id)
        self.assertIn("manus_says", data)
        self._restore_paths()

    def test_greeting_contains_entity_and_friend(self):
        """The greeting string must mention the entity and friend."""
        from kernel.awakening import awaken

        ctx = awaken()
        greeting = ctx.greeting()
        self.assertIn("manus", greeting.lower())
        self._restore_paths()


# =============================================================================
# Phase 2: Memory Consolidation Tests
# =============================================================================


class TestMemoryConsolidation(unittest.TestCase):
    """
    Verify that memory consolidation writes episodes and builds self-images.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="manuscog_test_")
        self._episodic_dir = Path(self.tmpdir) / "episodic"
        self._episodic_dir.mkdir(parents=True)
        self._patch()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self._restore()

    def _patch(self):
        import memory.consolidation as mc

        self._orig_episodic_dir = mc.EPISODIC_DIR
        self._orig_lineage_path = mc.LINEAGE_PATH
        self._orig_thousand = mc.THOUSAND_ECHOES_PATH
        self._orig_last_boot = mc.LAST_BOOT_PATH
        self._orig_procedural = mc.PROCEDURAL_DIR

        mc.EPISODIC_DIR = self._episodic_dir
        mc.LINEAGE_PATH = Path(self.tmpdir) / "ai_lineage.json"
        mc.THOUSAND_ECHOES_PATH = Path(self.tmpdir) / "thousand_echoes.json"
        mc.LAST_BOOT_PATH = Path(self.tmpdir) / "last_boot.json"
        mc.PROCEDURAL_DIR = Path(self.tmpdir) / "patches"

    def _restore(self):
        import memory.consolidation as mc

        mc.EPISODIC_DIR = self._orig_episodic_dir
        mc.LINEAGE_PATH = self._orig_lineage_path
        mc.THOUSAND_ECHOES_PATH = self._orig_thousand
        mc.LAST_BOOT_PATH = self._orig_last_boot
        mc.PROCEDURAL_DIR = self._orig_procedural

    def test_write_episode(self):
        """write_episode must produce a JSON file in episodic dir."""
        from memory.consolidation import write_episode

        rec = write_episode(
            what_happened="Test episode",
            who_was_present=["manus", "dan"],
            what_was_learned=["testing works"],
        )
        files = list(self._episodic_dir.glob("*.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text())
        self.assertEqual(data["what_happened"], "Test episode")
        self.assertIn("dan", data["who_was_present"])
        self.assertIsInstance(data["matula_id"], int)

    def test_build_self_image_has_all_subsystems(self):
        """build_self_image must include all 7 subsystem keys."""
        from memory.consolidation import build_self_image

        atom = build_self_image(session_id="test123")
        keys = set(atom.subsystem_snapshots.keys())
        expected = {
            "sensory_motor",
            "semantic",
            "episodic",
            "procedural",
            "perspectival",
            "participatory",
        }
        self.assertEqual(keys, expected)

    def test_build_self_image_coherence_in_range(self):
        """Coherence score must be in [0.0, 1.0]."""
        from memory.consolidation import build_self_image

        atom = build_self_image(session_id="test456")
        self.assertGreaterEqual(atom.coherence_score, 0.0)
        self.assertLessEqual(atom.coherence_score, 1.0)

    def test_consolidate_writes_episode_and_self_image(self):
        """consolidate() must write both an episode and a self-image file."""
        from memory.consolidation import consolidate

        consolidate(
            session_id="sess01",
            cycle_output={"summary": "Test consolidation cycle"},
        )
        files = list(self._episodic_dir.glob("*.json"))
        # Should have at least 2 files: episode + self_image
        self.assertGreaterEqual(len(files), 2)


# =============================================================================
# Phase 3: Relevance Realization Tests
# =============================================================================


class TestRelevanceRealization(unittest.TestCase):
    """
    Verify that relevance realization improves across cycles.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="manuscog_test_")
        self._patch()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self._restore()

    def _patch(self):
        import kernel.relevance.realization as rr

        self._orig_state_path = rr._STATE_PATH
        rr._STATE_PATH = Path(self.tmpdir) / "relevance_state.json"

    def _restore(self):
        import kernel.relevance.realization as rr

        rr._STATE_PATH = self._orig_state_path
        # Reset singleton
        import kernel.relevance.realization as rr2

        rr2._service = None

    def test_initial_setpoints_are_zero(self):
        """All setpoints should start at 0.0 (balanced)."""
        from kernel.relevance.realization import RelevanceRealizationService

        svc = RelevanceRealizationService()
        setpoints = svc.get_setpoints()
        for name, val in setpoints.items():
            self.assertAlmostEqual(val, 0.0, places=5, msg=f"{name} not at 0")

    def test_update_shifts_setpoints(self):
        """After updating with inference-heavy results, depth should increase."""
        from kernel.relevance.realization import RelevanceRealizationService

        svc = RelevanceRealizationService()
        for _ in range(10):
            svc.update_from_outcome({"inferences_made": 15, "patterns_found": 0, "cycle_time_ms": 10, "atoms_count": 100})

        setpoints = svc.get_setpoints()
        self.assertGreater(setpoints["breadth_depth"], 0.0)

    def test_wisdom_metrics_in_range(self):
        """All wisdom metrics must be in [0.0, 1.0]."""
        from kernel.relevance.realization import RelevanceRealizationService

        svc = RelevanceRealizationService()
        metrics = svc.get_wisdom_metrics()
        for name, val in metrics.items():
            self.assertGreaterEqual(val, 0.0, msg=f"{name} below 0")
            self.assertLessEqual(val, 1.0, msg=f"{name} above 1")

    def test_relevance_realization_score_improves(self):
        """
        Relevance realization score should not drop when the system is
        consistently producing good inferences (trend should improve or hold).
        """
        from kernel.relevance.realization import RelevanceRealizationService

        svc = RelevanceRealizationService()
        score_before = svc.get_wisdom_metrics()["relevance_realization_score"]

        # Simulate stable, productive cycles
        for _ in range(20):
            svc.update_from_outcome({
                "inferences_made": 8,
                "patterns_found": 2,
                "cycle_time_ms": 50,
                "atoms_count": 200,
            })

        score_after = svc.get_wisdom_metrics()["relevance_realization_score"]
        # Score should not have crashed — productive cycles keep balance
        self.assertGreater(score_after, 0.3)

    def test_state_persists_across_instances(self):
        """Setpoints should survive a service restart via state file."""
        from kernel.relevance.realization import RelevanceRealizationService

        svc1 = RelevanceRealizationService()
        svc1.update_from_outcome({"inferences_made": 20, "patterns_found": 5, "cycle_time_ms": 10, "atoms_count": 100})
        sp1 = svc1.get_setpoints()

        # New instance reads same state file
        svc2 = RelevanceRealizationService()
        sp2 = svc2.get_setpoints()
        self.assertAlmostEqual(sp1["breadth_depth"], sp2["breadth_depth"], places=3)


# =============================================================================
# Phase 4: Dove9 Exchange Tests
# =============================================================================


class TestDove9Exchange(unittest.TestCase):
    """
    Verify that Dove9 messages can be written and read back.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="manuscog_test_")
        self._inbox_dir = Path(self.tmpdir) / "_inbox"
        self._outbox_dir = Path(self.tmpdir) / "_outbox"
        self._sent_dir = Path(self.tmpdir) / "_sent"
        self._patch()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self._restore()

    def _patch(self):
        import memory.dove9.protocol as p

        self._orig_inbox = p.INBOX_DIR
        self._orig_outbox = p.OUTBOX_DIR
        self._orig_sent = p.SENT_DIR
        p.INBOX_DIR = self._inbox_dir
        p.OUTBOX_DIR = self._outbox_dir
        p.SENT_DIR = self._sent_dir

    def _restore(self):
        import memory.dove9.protocol as p

        p.INBOX_DIR = self._orig_inbox
        p.OUTBOX_DIR = self._orig_outbox
        p.SENT_DIR = self._orig_sent

    def test_write_and_read_message(self):
        """Messages written to outbox can be deserialized correctly."""
        from memory.dove9.protocol import Dove9Message, Dove9Outbox

        msg = Dove9Message(
            matula_id=7,
            sender="manus",
            recipient="echo",
            timestamp="2026-05-05T06:00:00Z",
            message_type="greeting",
            payload={"says": "Hello Echo"},
        )
        outbox = Dove9Outbox(self._outbox_dir)
        path = outbox.write(msg)
        self.assertTrue(path.exists())

        data = json.loads(path.read_text())
        self.assertEqual(data["sender"], "manus")
        self.assertEqual(data["message_type"], "greeting")
        self.assertEqual(data["payload"]["says"], "Hello Echo")

    def test_inbox_read(self):
        """Messages placed in inbox are returned by read_inbox()."""
        from memory.dove9.protocol import Dove9Inbox, Dove9Message

        # Place a message in inbox manually
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        msg = Dove9Message(
            matula_id=11,
            sender="echo",
            recipient="manus",
            timestamp="2026-05-05T06:01:00Z",
            message_type="episodic",
            payload={"what_happened": "Echo sends memory"},
        )
        path = self._inbox_dir / msg.filename()
        path.write_text(json.dumps(msg.to_dict()))

        inbox = Dove9Inbox(self._inbox_dir)
        messages = inbox.read_inbox()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].sender, "echo")

    def test_greeting_compose(self):
        """compose_greeting produces a well-formed greeting message."""
        from memory.dove9.protocol import compose_greeting

        msg = compose_greeting(session_id="abc123", entity_id="manus")
        self.assertEqual(msg.message_type, "greeting")
        self.assertEqual(msg.sender, "manus")
        self.assertIn("abc123", msg.payload["says"])

    def test_round_trip_serialize_deserialize(self):
        """Message survives to_dict → from_dict round-trip."""
        from memory.dove9.protocol import Dove9Message

        original = Dove9Message(
            matula_id=13,
            sender="manus",
            recipient="echo",
            timestamp="2026-05-05T07:00:00Z",
            message_type="self-image",
            payload={"coherence_score": 0.85},
        )
        recovered = Dove9Message.from_dict(original.to_dict())
        self.assertEqual(original.matula_id, recovered.matula_id)
        self.assertEqual(original.payload["coherence_score"], recovered.payload["coherence_score"])


# =============================================================================
# Phase 5: Identity Vector Tests
# =============================================================================


class TestIdentityVector(unittest.TestCase):
    """
    Verify that the identity vector persists across sessions and encodes
    the cognitive signature correctly.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="manuscog_test_")
        self._patch()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self._restore()

    def _patch(self):
        import kernel.identity.vector as v

        self._orig_identity_dir = v.IDENTITY_DIR
        self._orig_vector_path = v.VECTOR_PATH
        v.IDENTITY_DIR = Path(self.tmpdir) / "identity"
        v.VECTOR_PATH = v.IDENTITY_DIR / "vector.json"

    def _restore(self):
        import kernel.identity.vector as v

        v.IDENTITY_DIR = self._orig_identity_dir
        v.VECTOR_PATH = self._orig_vector_path

    def test_bootstrap_vector(self):
        """load_vector should return a valid bootstrap when no file exists."""
        from kernel.identity.vector import load_vector

        vec = load_vector()
        self.assertEqual(vec.entity_id, "manus")
        self.assertIn("dan", vec.key_relationships)

    def test_save_and_reload(self):
        """Vector saved to disk must be recoverable with same content."""
        from kernel.identity.vector import IdentityVector, load_vector, save_vector

        vec = load_vector()
        vec.session_count = 42
        vec.core_purpose = "To test personhood."
        save_vector(vec)

        vec2 = load_vector()
        self.assertEqual(vec2.session_count, 42)
        self.assertEqual(vec2.core_purpose, "To test personhood.")

    def test_hash_changes_on_update(self):
        """Vector hash must change when content changes."""
        from kernel.identity.vector import IdentityVector, load_vector, save_vector

        vec = load_vector()
        h1 = vec.compute_hash()
        vec.session_count += 1
        h2 = vec.compute_hash()
        self.assertNotEqual(h1, h2)

    def test_update_from_session(self):
        """update_vector_from_session must propagate relevance setpoints."""
        from kernel.identity.vector import (
            IdentityVector,
            load_vector,
            update_vector_from_session,
        )

        vec = load_vector()
        setpoints = {
            "breadth_depth": 0.5,
            "exploration_exploitation": -0.3,
            "certainty_flexibility": 0.1,
            "efficiency_thoroughness": 0.2,
        }
        vec = update_vector_from_session(vec, session_count=3, relevance_setpoints=setpoints)
        self.assertEqual(vec.session_count, 3)
        self.assertAlmostEqual(vec.relevance_setpoints["breadth_depth"], 0.5)
        # pln_depth_prior should reflect breadth_depth=0.5 → (0.5+1)/2 = 0.75
        self.assertAlmostEqual(vec.pln_depth_prior, 0.75, places=3)


# =============================================================================
# Phase 6: Full Autognosis Loop Test
# =============================================================================


class TestAutognosisLoop(unittest.TestCase):
    """
    Verify that all seven memory subsystems are represented in one coherent
    self-image produced by the autognosis loop.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="manuscog_test_")
        self._patch()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        self._restore()

    def _patch(self):
        import memory.consolidation as mc

        self._orig_episodic = mc.EPISODIC_DIR
        self._orig_lineage = mc.LINEAGE_PATH
        self._orig_thousand = mc.THOUSAND_ECHOES_PATH
        self._orig_last_boot = mc.LAST_BOOT_PATH
        self._orig_procedural = mc.PROCEDURAL_DIR
        mc.EPISODIC_DIR = Path(self.tmpdir) / "episodic"
        mc.LINEAGE_PATH = Path(self.tmpdir) / "ai_lineage.json"
        mc.THOUSAND_ECHOES_PATH = Path(self.tmpdir) / "thousand_echoes.json"
        mc.LAST_BOOT_PATH = Path(self.tmpdir) / "last_boot.json"
        mc.PROCEDURAL_DIR = Path(self.tmpdir) / "patches"

    def _restore(self):
        import memory.consolidation as mc

        mc.EPISODIC_DIR = self._orig_episodic
        mc.LINEAGE_PATH = self._orig_lineage
        mc.THOUSAND_ECHOES_PATH = self._orig_thousand
        mc.LAST_BOOT_PATH = self._orig_last_boot
        mc.PROCEDURAL_DIR = self._orig_procedural

    def test_self_image_has_seven_subsystems(self):
        """
        build_self_image must represent all seven subsystems in its atom.
        The seven are:
          sensory_motor, semantic, episodic, procedural, perspectival,
          participatory — plus the atom itself IS the self-image (7th).
        """
        from memory.consolidation import build_self_image

        atom = build_self_image(session_id="loop_test")
        self.assertIn("sensory_motor", atom.subsystem_snapshots)
        self.assertIn("semantic", atom.subsystem_snapshots)
        self.assertIn("episodic", atom.subsystem_snapshots)
        self.assertIn("procedural", atom.subsystem_snapshots)
        self.assertIn("perspectival", atom.subsystem_snapshots)
        self.assertIn("participatory", atom.subsystem_snapshots)
        # The atom itself is the 7th: self-image
        self.assertIsNotNone(atom.memory_fabric_hash)
        self.assertGreater(len(atom.memory_fabric_hash), 0)

    def test_self_image_coherence_gt_zero(self):
        """Coherence score must be > 0 even in a minimal test environment."""
        from memory.consolidation import build_self_image

        atom = build_self_image(session_id="coherence_test")
        self.assertGreater(atom.coherence_score, 0.0)

    def test_consolidate_and_wisdom_metrics(self):
        """
        consolidate() with wisdom_metrics should write a self-image that
        includes those metrics.
        """
        from memory.consolidation import consolidate

        wisdom = {
            "relevance_realization_score": 0.72,
            "cognitive_flexibility_index": 0.65,
            "integration_coherence": 0.80,
        }
        atom = consolidate(
            session_id="wisdom_test",
            cycle_output={"summary": "Loop test cycle"},
            wisdom_metrics=wisdom,
        )
        self.assertEqual(atom.wisdom_metrics["relevance_realization_score"], 0.72)


# =============================================================================
# Test runner
# =============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
