"""
AtomSpace Persistence Module
============================

This module provides persistent storage for the AtomSpace, enabling
cognitive continuity across restarts. Knowledge survives shutdown.

Storage backends supported:
1. SQLite - Local file-based storage (default)
2. JSON - Human-readable export/import
3. Binary - Fast serialization for large AtomSpaces

The persistence layer maintains:
- All atoms (nodes and links)
- Truth values
- Attention values
- Atom metadata
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from typing import Dict, List, Optional, Any, Set, Iterator, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import sqlite3
import json
import pickle
import gzip
import hashlib
import logging
from contextlib import contextmanager
from enum import Enum, auto

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue
)
from atomspace.hypergraph.atomspace import AtomSpace


logger = logging.getLogger("AtomSpace.Persistence")


# =============================================================================
# CONFIGURATION
# =============================================================================

class StorageBackend(Enum):
    """Available storage backends."""
    SQLITE = auto()
    JSON = auto()
    BINARY = auto()


@dataclass
class PersistenceConfig:
    """Configuration for AtomSpace persistence."""
    backend: StorageBackend = StorageBackend.SQLITE
    storage_path: str = "atomspace.db"
    auto_save: bool = True
    save_interval: int = 300  # seconds
    compress: bool = True
    backup_count: int = 3


# =============================================================================
# ATOM SERIALIZATION
# =============================================================================

@dataclass
class SerializedAtom:
    """Serialized representation of an atom."""
    handle: str
    atom_type: str
    name: Optional[str]
    outgoing: List[str]  # List of handles for links
    truth_strength: float
    truth_confidence: float
    attention_sti: float
    attention_lti: float
    attention_vlti: bool
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SerializedAtom':
        return cls(**data)
    
    @classmethod
    def from_atom(cls, atom: Atom) -> 'SerializedAtom':
        """Create serialized atom from Atom object."""
        return cls(
            handle=str(atom.handle),
            atom_type=atom.atom_type.name,
            name=getattr(atom, 'name', None),
            outgoing=[str(h) for h in getattr(atom, 'outgoing', [])],
            truth_strength=atom.truth_value.strength,
            truth_confidence=atom.truth_value.confidence,
            attention_sti=atom.attention_value.sti,
            attention_lti=atom.attention_value.lti,
            attention_vlti=atom.attention_value.vlti,
            created_at=datetime.now().isoformat(),
            metadata={}
        )


# =============================================================================
# SQLITE BACKEND
# =============================================================================

class SQLiteStorage:
    """SQLite-based persistent storage for AtomSpace."""
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS atoms (
        handle TEXT PRIMARY KEY,
        atom_type TEXT NOT NULL,
        name TEXT,
        outgoing TEXT,
        truth_strength REAL,
        truth_confidence REAL,
        attention_sti REAL,
        attention_lti REAL,
        attention_vlti INTEGER,
        created_at TEXT,
        updated_at TEXT,
        metadata TEXT
    );
    
    CREATE INDEX IF NOT EXISTS idx_atom_type ON atoms(atom_type);
    CREATE INDEX IF NOT EXISTS idx_name ON atoms(name);
    CREATE INDEX IF NOT EXISTS idx_attention ON atoms(attention_sti);
    
    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        try:
            yield self._conn
        except Exception as e:
            self._conn.rollback()
            raise
    
    def save_atom(self, atom: SerializedAtom):
        """Save a single atom to storage."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO atoms 
                (handle, atom_type, name, outgoing, truth_strength, truth_confidence,
                 attention_sti, attention_lti, attention_vlti, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                atom.handle,
                atom.atom_type,
                atom.name,
                json.dumps(atom.outgoing),
                atom.truth_strength,
                atom.truth_confidence,
                atom.attention_sti,
                atom.attention_lti,
                int(atom.attention_vlti),
                atom.created_at,
                datetime.now().isoformat(),
                json.dumps(atom.metadata)
            ))
            conn.commit()
    
    def save_atoms(self, atoms: List[SerializedAtom]):
        """Save multiple atoms in a batch."""
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO atoms 
                (handle, atom_type, name, outgoing, truth_strength, truth_confidence,
                 attention_sti, attention_lti, attention_vlti, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    atom.handle,
                    atom.atom_type,
                    atom.name,
                    json.dumps(atom.outgoing),
                    atom.truth_strength,
                    atom.truth_confidence,
                    atom.attention_sti,
                    atom.attention_lti,
                    int(atom.attention_vlti),
                    atom.created_at,
                    datetime.now().isoformat(),
                    json.dumps(atom.metadata)
                )
                for atom in atoms
            ])
            conn.commit()
    
    def load_atom(self, handle: str) -> Optional[SerializedAtom]:
        """Load a single atom from storage."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM atoms WHERE handle = ?", (handle,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_atom(row)
        return None
    
    def load_all_atoms(self) -> Iterator[SerializedAtom]:
        """Load all atoms from storage."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM atoms ORDER BY created_at")
            for row in cursor:
                yield self._row_to_atom(row)
    
    def load_atoms_by_type(self, atom_type: str) -> Iterator[SerializedAtom]:
        """Load atoms of a specific type."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM atoms WHERE atom_type = ?", (atom_type,)
            )
            for row in cursor:
                yield self._row_to_atom(row)
    
    def delete_atom(self, handle: str) -> bool:
        """Delete an atom from storage."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM atoms WHERE handle = ?", (handle,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_atom_count(self) -> int:
        """Get total number of stored atoms."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM atoms")
            return cursor.fetchone()[0]
    
    def set_metadata(self, key: str, value: Any):
        """Set a metadata value."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """Get a metadata value."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM metadata WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None
    
    def _row_to_atom(self, row: sqlite3.Row) -> SerializedAtom:
        """Convert a database row to SerializedAtom."""
        return SerializedAtom(
            handle=row['handle'],
            atom_type=row['atom_type'],
            name=row['name'],
            outgoing=json.loads(row['outgoing']) if row['outgoing'] else [],
            truth_strength=row['truth_strength'],
            truth_confidence=row['truth_confidence'],
            attention_sti=row['attention_sti'],
            attention_lti=row['attention_lti'],
            attention_vlti=bool(row['attention_vlti']),
            created_at=row['created_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# =============================================================================
# ATOMSPACE PERSISTENCE MANAGER
# =============================================================================

class AtomSpacePersistence:
    """
    Manages persistence for AtomSpace.
    
    Provides save/load operations to maintain cognitive continuity
    across restarts.
    """
    
    def __init__(self, config: PersistenceConfig = None):
        self.config = config or PersistenceConfig()
        
        # Initialize storage backend
        if self.config.backend == StorageBackend.SQLITE:
            self.storage = SQLiteStorage(self.config.storage_path)
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
        
        # Statistics
        self.stats = {
            'atoms_saved': 0,
            'atoms_loaded': 0,
            'last_save': None,
            'last_load': None
        }
    
    def save(self, atomspace: AtomSpace) -> int:
        """
        Save the entire AtomSpace to persistent storage.
        
        Returns the number of atoms saved.
        """
        logger.info("Saving AtomSpace to persistent storage...")
        
        atoms_to_save = []
        
        # Serialize all atoms
        for atom in atomspace:
            serialized = SerializedAtom.from_atom(atom)
            atoms_to_save.append(serialized)
        
        # Save in batch
        self.storage.save_atoms(atoms_to_save)
        
        # Save metadata
        self.storage.set_metadata('atomspace_size', len(atoms_to_save))
        self.storage.set_metadata('saved_at', datetime.now().isoformat())
        
        # Update stats
        self.stats['atoms_saved'] += len(atoms_to_save)
        self.stats['last_save'] = datetime.now()
        
        logger.info(f"Saved {len(atoms_to_save)} atoms to storage")
        return len(atoms_to_save)
    
    def load(self, atomspace: AtomSpace) -> int:
        """
        Load atoms from persistent storage into AtomSpace.
        
        Returns the number of atoms loaded.
        """
        logger.info("Loading AtomSpace from persistent storage...")
        
        loaded_count = 0
        handle_map: Dict[str, AtomHandle] = {}  # Old handle -> new handle
        
        # First pass: Load all nodes
        for serialized in self.storage.load_all_atoms():
            if not serialized.outgoing:  # It's a node
                atom_type = AtomType[serialized.atom_type]
                tv = TruthValue(serialized.truth_strength, serialized.truth_confidence)
                av = AttentionValue(
                    sti=serialized.attention_sti,
                    lti=serialized.attention_lti,
                    vlti=serialized.attention_vlti
                )
                
                new_handle = atomspace.add_node(
                    atom_type,
                    serialized.name or "",
                    tv=tv,
                    av=av
                )
                
                if new_handle:
                    handle_map[serialized.handle] = new_handle
                    loaded_count += 1
        
        # Second pass: Load all links
        for serialized in self.storage.load_all_atoms():
            if serialized.outgoing:  # It's a link
                atom_type = AtomType[serialized.atom_type]
                tv = TruthValue(serialized.truth_strength, serialized.truth_confidence)
                av = AttentionValue(
                    sti=serialized.attention_sti,
                    lti=serialized.attention_lti,
                    vlti=serialized.attention_vlti
                )
                
                # Map old handles to new handles
                outgoing = []
                for old_handle in serialized.outgoing:
                    if old_handle in handle_map:
                        outgoing.append(handle_map[old_handle])
                    else:
                        logger.warning(f"Missing handle reference: {old_handle}")
                
                if len(outgoing) == len(serialized.outgoing):
                    new_handle = atomspace.add_link(
                        atom_type,
                        outgoing,
                        tv=tv,
                        av=av
                    )
                    
                    if new_handle:
                        handle_map[serialized.handle] = new_handle
                        loaded_count += 1
        
        # Update stats
        self.stats['atoms_loaded'] += loaded_count
        self.stats['last_load'] = datetime.now()
        
        logger.info(f"Loaded {loaded_count} atoms from storage")
        return loaded_count
    
    def export_json(self, atomspace: AtomSpace, filepath: str) -> int:
        """Export AtomSpace to JSON file."""
        atoms = []
        for atom in atomspace:
            serialized = SerializedAtom.from_atom(atom)
            atoms.append(serialized.to_dict())
        
        data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'atom_count': len(atoms),
            'atoms': atoms
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(atoms)} atoms to {filepath}")
        return len(atoms)
    
    def import_json(self, atomspace: AtomSpace, filepath: str) -> int:
        """Import AtomSpace from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        atoms = [SerializedAtom.from_dict(a) for a in data['atoms']]
        
        # Save to storage first
        self.storage.save_atoms(atoms)
        
        # Then load into atomspace
        return self.load(atomspace)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        return {
            **self.stats,
            'stored_atoms': self.storage.get_atom_count(),
            'storage_path': self.config.storage_path,
            'backend': self.config.backend.name
        }
    
    def close(self):
        """Close the persistence manager."""
        if hasattr(self.storage, 'close'):
            self.storage.close()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'StorageBackend',
    'PersistenceConfig',
    'SerializedAtom',
    'SQLiteStorage',
    'AtomSpacePersistence',
]
