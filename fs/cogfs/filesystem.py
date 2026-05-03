"""
OpenCog Inferno AGI - Cognitive File System (CogFS)
===================================================

Following Inferno OS philosophy, CogFS exposes all cognitive resources
as files in a hierarchical namespace. This enables:
- Uniform access to atoms, queries, and cognitive processes
- Distributed access via Styx/9P protocol
- Standard file operations for cognitive manipulation
- Process isolation through namespace virtualization

The cognitive namespace hierarchy:
/cog/
    atoms/          - Direct atom access by handle
    types/          - Atoms organized by type
        concept/
        predicate/
        inheritance/
        ...
    attention/      - Attention-based views
        focus/      - Current attentional focus
        top/        - Top atoms by STI
    inference/      - Inference operations
        deduction/
        induction/
        query/
    learning/       - Learning operations
    processes/      - Cognitive processes
    stats/          - System statistics
    goals/          - Active goals
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
import json
import io

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, CogFSNode, CogFSNodeType
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# FILE TYPES AND MODES
# =============================================================================

class FileMode(Enum):
    """File access modes."""
    READ = auto()
    WRITE = auto()
    READWRITE = auto()
    APPEND = auto()
    EXECUTE = auto()


class FileType(Enum):
    """Types of cognitive files."""
    ATOM = auto()           # Single atom
    ATOM_SET = auto()       # Set of atoms
    QUERY = auto()          # Query interface
    INFERENCE = auto()      # Inference interface
    STATS = auto()          # Statistics
    CONTROL = auto()        # Control interface
    STREAM = auto()         # Event stream


@dataclass
class FileDescriptor:
    """File descriptor for open cognitive files."""
    fd: int
    path: str
    mode: FileMode
    file_type: FileType
    position: int = 0
    buffer: bytes = b""
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)


# =============================================================================
# COGNITIVE FILE OPERATIONS
# =============================================================================

class CognitiveFile:
    """
    Base class for cognitive file implementations.
    """
    
    def __init__(self, path: str, atomspace: AtomSpace):
        self.path = path
        self.atomspace = atomspace
        self._lock = threading.Lock()
    
    def read(self, size: int = -1, offset: int = 0) -> bytes:
        """Read from the file."""
        raise NotImplementedError
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """Write to the file."""
        raise NotImplementedError
    
    def stat(self) -> Dict[str, Any]:
        """Get file statistics."""
        return {
            'path': self.path,
            'type': 'cognitive_file',
            'size': 0,
            'mtime': time.time()
        }


class AtomFile(CognitiveFile):
    """
    File interface to a single atom.
    
    Reading returns JSON representation of the atom.
    Writing updates the atom's properties.
    """
    
    def __init__(self, path: str, atomspace: AtomSpace, handle: AtomHandle):
        super().__init__(path, atomspace)
        self.handle = handle
    
    def read(self, size: int = -1, offset: int = 0) -> bytes:
        """Read atom as JSON."""
        atom = self.atomspace.get_atom(self.handle)
        if not atom:
            return b"{}"
        
        data = json.dumps(atom.to_dict(), indent=2)
        data_bytes = data.encode('utf-8')
        
        if offset >= len(data_bytes):
            return b""
        
        if size < 0:
            return data_bytes[offset:]
        return data_bytes[offset:offset + size]
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """Update atom from JSON."""
        try:
            update = json.loads(data.decode('utf-8'))
            
            # Update truth value if provided
            if 'truth_value' in update:
                tv_data = update['truth_value']
                tv = TruthValue(
                    strength=tv_data.get('strength', 1.0),
                    confidence=tv_data.get('confidence', 0.9),
                    count=tv_data.get('count', 1.0)
                )
                self.atomspace.set_truth_value(self.handle, tv)
            
            # Update attention value if provided
            if 'attention_value' in update:
                av_data = update['attention_value']
                av = AttentionValue(
                    sti=av_data.get('sti', 0.0),
                    lti=av_data.get('lti', 0.0),
                    vlti=av_data.get('vlti', False)
                )
                self.atomspace.set_attention_value(self.handle, av)
            
            return len(data)
        except Exception as e:
            return 0
    
    def stat(self) -> Dict[str, Any]:
        atom = self.atomspace.get_atom(self.handle)
        return {
            'path': self.path,
            'type': 'atom',
            'atom_type': atom.atom_type.name if atom else 'unknown',
            'handle': self.handle.uuid,
            'mtime': atom.modified_at if atom else 0
        }


class AtomSetFile(CognitiveFile):
    """
    File interface to a set of atoms (e.g., by type).
    
    Reading returns list of atom handles.
    Writing can add new atoms.
    """
    
    def __init__(
        self,
        path: str,
        atomspace: AtomSpace,
        atom_type: Optional[AtomType] = None,
        filter_fn: Optional[Callable[[Atom], bool]] = None
    ):
        super().__init__(path, atomspace)
        self.atom_type = atom_type
        self.filter_fn = filter_fn
    
    def read(self, size: int = -1, offset: int = 0) -> bytes:
        """Read atom handles as JSON array."""
        if self.atom_type:
            atoms = self.atomspace.get_atoms_by_type(self.atom_type)
        else:
            atoms = list(self.atomspace)
        
        if self.filter_fn:
            atoms = [a for a in atoms if self.filter_fn(a)]
        
        # Return list of handles with basic info
        data = []
        for atom in atoms:
            entry = {
                'handle': atom.handle.uuid,
                'type': atom.atom_type.name,
                'sti': atom.attention_value.sti
            }
            if isinstance(atom, Node):
                entry['name'] = atom.name
            data.append(entry)
        
        json_data = json.dumps(data, indent=2).encode('utf-8')
        
        if offset >= len(json_data):
            return b""
        if size < 0:
            return json_data[offset:]
        return json_data[offset:offset + size]
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """Add new atom from JSON."""
        try:
            atom_data = json.loads(data.decode('utf-8'))
            
            atom_type = AtomType[atom_data['type']]
            
            if 'name' in atom_data:
                # Create node
                self.atomspace.add_node(
                    atom_type,
                    atom_data['name'],
                    tv=TruthValue(**atom_data.get('truth_value', {})) if 'truth_value' in atom_data else None
                )
            elif 'outgoing' in atom_data:
                # Create link
                outgoing = [
                    AtomHandle(uuid=h) for h in atom_data['outgoing']
                ]
                self.atomspace.add_link(
                    atom_type,
                    outgoing,
                    tv=TruthValue(**atom_data.get('truth_value', {})) if 'truth_value' in atom_data else None
                )
            
            return len(data)
        except Exception as e:
            return 0


class QueryFile(CognitiveFile):
    """
    File interface for queries.
    
    Writing a query pattern returns matching atoms.
    """
    
    def __init__(self, path: str, atomspace: AtomSpace):
        super().__init__(path, atomspace)
        self._last_result: bytes = b"[]"
    
    def read(self, size: int = -1, offset: int = 0) -> bytes:
        """Read last query result."""
        if offset >= len(self._last_result):
            return b""
        if size < 0:
            return self._last_result[offset:]
        return self._last_result[offset:offset + size]
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """Execute query and store result."""
        try:
            query = json.loads(data.decode('utf-8'))
            
            results = []
            
            # Simple query by type
            if 'type' in query:
                atom_type = AtomType[query['type']]
                atoms = self.atomspace.get_atoms_by_type(atom_type)
                
                # Apply filters
                if 'min_strength' in query:
                    atoms = [a for a in atoms if a.truth_value.strength >= query['min_strength']]
                if 'min_confidence' in query:
                    atoms = [a for a in atoms if a.truth_value.confidence >= query['min_confidence']]
                if 'in_focus' in query and query['in_focus']:
                    atoms = [a for a in atoms if a.attention_value.sti > 0.5]
                
                # Limit results
                limit = query.get('limit', 100)
                atoms = atoms[:limit]
                
                results = [a.to_dict() for a in atoms]
            
            # Query by name
            elif 'name' in query:
                atoms = self.atomspace.get_atoms_by_name(query['name'])
                results = [a.to_dict() for a in atoms]
            
            self._last_result = json.dumps(results, indent=2).encode('utf-8')
            return len(data)
        except Exception as e:
            self._last_result = json.dumps({'error': str(e)}).encode('utf-8')
            return 0


class StatsFile(CognitiveFile):
    """
    File interface for system statistics.
    """
    
    def __init__(self, path: str, atomspace: AtomSpace, stats_fn: Callable[[], Dict[str, Any]]):
        super().__init__(path, atomspace)
        self.stats_fn = stats_fn
    
    def read(self, size: int = -1, offset: int = 0) -> bytes:
        """Read statistics as JSON."""
        stats = self.stats_fn()
        data = json.dumps(stats, indent=2).encode('utf-8')
        
        if offset >= len(data):
            return b""
        if size < 0:
            return data[offset:]
        return data[offset:offset + size]
    
    def write(self, data: bytes, offset: int = 0) -> int:
        """Stats file is read-only."""
        return 0


# =============================================================================
# COGNITIVE FILE SYSTEM
# =============================================================================

class CognitiveFileSystem:
    """
    The Cognitive File System (CogFS).
    
    Exposes the entire cognitive system as a file hierarchy,
    following Inferno OS design principles.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # File descriptor table
        self._fd_table: Dict[int, FileDescriptor] = {}
        self._next_fd = 3  # Start after stdin/stdout/stderr
        
        # Mounted file handlers
        self._mounts: Dict[str, CognitiveFile] = {}
        
        # Directory structure
        self._directories: Dict[str, List[str]] = {
            '/cog': ['atoms', 'types', 'attention', 'inference', 'learning', 'processes', 'stats', 'goals'],
            '/cog/types': [t.name.lower() for t in AtomType],
            '/cog/attention': ['focus', 'top', 'vlti'],
            '/cog/inference': ['deduction', 'induction', 'abduction', 'query'],
            '/cog/stats': ['atomspace', 'memory', 'attention', 'inference'],
        }
        
        self._lock = threading.RLock()
        
        # Setup default mounts
        self._setup_default_mounts()
    
    def _setup_default_mounts(self):
        """Setup default file mounts."""
        # AtomSpace stats
        self._mounts['/cog/stats/atomspace'] = StatsFile(
            '/cog/stats/atomspace',
            self.atomspace,
            lambda: self.atomspace.get_stats()
        )
        
        # Query interface
        self._mounts['/cog/inference/query'] = QueryFile(
            '/cog/inference/query',
            self.atomspace
        )
        
        # Type-based atom sets
        for atom_type in AtomType:
            path = f'/cog/types/{atom_type.name.lower()}'
            self._mounts[path] = AtomSetFile(
                path,
                self.atomspace,
                atom_type=atom_type
            )
        
        # Attention focus
        self._mounts['/cog/attention/focus'] = AtomSetFile(
            '/cog/attention/focus',
            self.atomspace,
            filter_fn=lambda a: a.attention_value.sti > 0.5
        )
        
        # Top attention atoms
        self._mounts['/cog/attention/top'] = AtomSetFile(
            '/cog/attention/top',
            self.atomspace,
            filter_fn=lambda a: a.attention_value.sti > 0.3
        )
        
        # VLTI atoms
        self._mounts['/cog/attention/vlti'] = AtomSetFile(
            '/cog/attention/vlti',
            self.atomspace,
            filter_fn=lambda a: a.attention_value.vlti
        )
    
    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================
    
    def open(self, path: str, mode: FileMode = FileMode.READ) -> int:
        """Open a cognitive file."""
        with self._lock:
            # Normalize path
            path = self._normalize_path(path)
            
            # Check if it's a mounted file
            if path in self._mounts:
                fd = self._allocate_fd()
                self._fd_table[fd] = FileDescriptor(
                    fd=fd,
                    path=path,
                    mode=mode,
                    file_type=FileType.ATOM_SET
                )
                return fd
            
            # Check if it's an atom path
            if path.startswith('/cog/atoms/'):
                handle_uuid = path.split('/')[-1]
                # Find atom by UUID
                for atom in self.atomspace:
                    if atom.handle.uuid == handle_uuid:
                        fd = self._allocate_fd()
                        self._fd_table[fd] = FileDescriptor(
                            fd=fd,
                            path=path,
                            mode=mode,
                            file_type=FileType.ATOM,
                            context={'handle': atom.handle}
                        )
                        self._mounts[path] = AtomFile(path, self.atomspace, atom.handle)
                        return fd
            
            # Check if it's a directory
            if path in self._directories:
                fd = self._allocate_fd()
                self._fd_table[fd] = FileDescriptor(
                    fd=fd,
                    path=path,
                    mode=mode,
                    file_type=FileType.ATOM_SET
                )
                return fd
            
            return -1  # File not found
    
    def close(self, fd: int) -> bool:
        """Close a file descriptor."""
        with self._lock:
            if fd in self._fd_table:
                del self._fd_table[fd]
                return True
            return False
    
    def read(self, fd: int, size: int = -1) -> bytes:
        """Read from a file descriptor."""
        with self._lock:
            if fd not in self._fd_table:
                return b""
            
            desc = self._fd_table[fd]
            desc.last_access = time.time()
            
            # Check if it's a directory
            if desc.path in self._directories:
                entries = self._directories[desc.path]
                data = json.dumps(entries).encode('utf-8')
                result = data[desc.position:]
                if size >= 0:
                    result = result[:size]
                desc.position += len(result)
                return result
            
            # Read from mounted file
            if desc.path in self._mounts:
                cog_file = self._mounts[desc.path]
                data = cog_file.read(size, desc.position)
                desc.position += len(data)
                return data
            
            return b""
    
    def write(self, fd: int, data: bytes) -> int:
        """Write to a file descriptor."""
        with self._lock:
            if fd not in self._fd_table:
                return -1
            
            desc = self._fd_table[fd]
            if desc.mode not in [FileMode.WRITE, FileMode.READWRITE, FileMode.APPEND]:
                return -1
            
            desc.last_access = time.time()
            
            if desc.path in self._mounts:
                cog_file = self._mounts[desc.path]
                written = cog_file.write(data, desc.position)
                if desc.mode != FileMode.APPEND:
                    desc.position += written
                return written
            
            return -1
    
    def stat(self, path: str) -> Optional[Dict[str, Any]]:
        """Get file/directory statistics."""
        path = self._normalize_path(path)
        
        # Check if directory
        if path in self._directories:
            return {
                'path': path,
                'type': 'directory',
                'entries': len(self._directories[path]),
                'mtime': time.time()
            }
        
        # Check mounted file
        if path in self._mounts:
            return self._mounts[path].stat()
        
        return None
    
    def readdir(self, path: str) -> List[str]:
        """List directory contents."""
        path = self._normalize_path(path)
        
        if path in self._directories:
            return self._directories[path].copy()
        
        # Dynamic directory for atoms
        if path == '/cog/atoms':
            return [a.handle.uuid for a in list(self.atomspace)[:100]]
        
        return []
    
    def mkdir(self, path: str) -> bool:
        """Create a directory."""
        path = self._normalize_path(path)
        
        if path in self._directories:
            return False
        
        parent = '/'.join(path.split('/')[:-1])
        if parent not in self._directories:
            return False
        
        self._directories[path] = []
        self._directories[parent].append(path.split('/')[-1])
        return True
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _normalize_path(self, path: str) -> str:
        """Normalize a file path."""
        # Remove trailing slash
        if path.endswith('/') and path != '/':
            path = path[:-1]
        
        # Ensure starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        return path
    
    def _allocate_fd(self) -> int:
        """Allocate a new file descriptor."""
        fd = self._next_fd
        self._next_fd += 1
        return fd
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    def read_atom(self, handle: AtomHandle) -> Optional[Dict[str, Any]]:
        """Read an atom directly."""
        path = f'/cog/atoms/{handle.uuid}'
        fd = self.open(path)
        if fd < 0:
            return None
        
        data = self.read(fd)
        self.close(fd)
        
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return None
    
    def query_atoms(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        fd = self.open('/cog/inference/query', FileMode.READWRITE)
        if fd < 0:
            return []
        
        # Write query
        self.write(fd, json.dumps(query).encode('utf-8'))
        
        # Reset position and read result
        self._fd_table[fd].position = 0
        data = self.read(fd)
        self.close(fd)
        
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return []
    
    def get_focus_atoms(self) -> List[Dict[str, Any]]:
        """Get atoms in attentional focus."""
        fd = self.open('/cog/attention/focus')
        if fd < 0:
            return []
        
        data = self.read(fd)
        self.close(fd)
        
        try:
            return json.loads(data.decode('utf-8'))
        except:
            return []


# =============================================================================
# STYX PROTOCOL INTERFACE
# =============================================================================

class StyxMessage(Enum):
    """Styx/9P protocol message types."""
    TVERSION = 100
    RVERSION = 101
    TAUTH = 102
    RAUTH = 103
    TATTACH = 104
    RATTACH = 105
    TERROR = 106
    RERROR = 107
    TFLUSH = 108
    RFLUSH = 109
    TWALK = 110
    RWALK = 111
    TOPEN = 112
    ROPEN = 113
    TCREATE = 114
    RCREATE = 115
    TREAD = 116
    RREAD = 117
    TWRITE = 118
    RWRITE = 119
    TCLUNK = 120
    RCLUNK = 121
    TREMOVE = 122
    RREMOVE = 123
    TSTAT = 124
    RSTAT = 125
    TWSTAT = 126
    RWSTAT = 127


@dataclass
class StyxRequest:
    """A Styx protocol request."""
    msg_type: StyxMessage
    tag: int
    fid: int
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StyxResponse:
    """A Styx protocol response."""
    msg_type: StyxMessage
    tag: int
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class StyxServer:
    """
    Styx/9P protocol server for distributed CogFS access.
    
    This allows remote access to the cognitive file system
    using the standard Inferno distributed protocol.
    """
    
    def __init__(self, cogfs: CognitiveFileSystem):
        self.cogfs = cogfs
        
        # Fid to path mapping
        self._fids: Dict[int, str] = {}
        self._fid_fds: Dict[int, int] = {}  # fid -> file descriptor
        
        # Protocol state
        self.msize = 8192  # Maximum message size
        self.version = "9P2000"
        
        self._lock = threading.Lock()
    
    def handle_request(self, request: StyxRequest) -> StyxResponse:
        """Handle a Styx protocol request."""
        handlers = {
            StyxMessage.TVERSION: self._handle_version,
            StyxMessage.TATTACH: self._handle_attach,
            StyxMessage.TWALK: self._handle_walk,
            StyxMessage.TOPEN: self._handle_open,
            StyxMessage.TREAD: self._handle_read,
            StyxMessage.TWRITE: self._handle_write,
            StyxMessage.TCLUNK: self._handle_clunk,
            StyxMessage.TSTAT: self._handle_stat,
        }
        
        handler = handlers.get(request.msg_type)
        if handler:
            return handler(request)
        
        return StyxResponse(
            msg_type=StyxMessage.RERROR,
            tag=request.tag,
            error="Unknown message type"
        )
    
    def _handle_version(self, req: StyxRequest) -> StyxResponse:
        """Handle version negotiation."""
        return StyxResponse(
            msg_type=StyxMessage.RVERSION,
            tag=req.tag,
            data={'msize': self.msize, 'version': self.version}
        )
    
    def _handle_attach(self, req: StyxRequest) -> StyxResponse:
        """Handle attach (mount) request."""
        with self._lock:
            self._fids[req.fid] = '/cog'
        
        return StyxResponse(
            msg_type=StyxMessage.RATTACH,
            tag=req.tag,
            data={'qid': {'type': 'dir', 'path': '/cog'}}
        )
    
    def _handle_walk(self, req: StyxRequest) -> StyxResponse:
        """Handle walk (path traversal) request."""
        with self._lock:
            if req.fid not in self._fids:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="Invalid fid"
                )
            
            current_path = self._fids[req.fid]
            names = req.data.get('names', [])
            new_fid = req.data.get('newfid', req.fid)
            
            qids = []
            for name in names:
                if name == '..':
                    current_path = '/'.join(current_path.split('/')[:-1]) or '/cog'
                else:
                    current_path = f"{current_path}/{name}"
                
                # Verify path exists
                stat = self.cogfs.stat(current_path)
                if stat:
                    qids.append({'type': stat['type'], 'path': current_path})
                else:
                    return StyxResponse(
                        msg_type=StyxMessage.RERROR,
                        tag=req.tag,
                        error=f"Path not found: {current_path}"
                    )
            
            self._fids[new_fid] = current_path
        
        return StyxResponse(
            msg_type=StyxMessage.RWALK,
            tag=req.tag,
            data={'qids': qids}
        )
    
    def _handle_open(self, req: StyxRequest) -> StyxResponse:
        """Handle open request."""
        with self._lock:
            if req.fid not in self._fids:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="Invalid fid"
                )
            
            path = self._fids[req.fid]
            mode = FileMode.READ  # Simplified
            
            fd = self.cogfs.open(path, mode)
            if fd < 0:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="Cannot open file"
                )
            
            self._fid_fds[req.fid] = fd
        
        return StyxResponse(
            msg_type=StyxMessage.ROPEN,
            tag=req.tag,
            data={'qid': {'path': path}, 'iounit': self.msize}
        )
    
    def _handle_read(self, req: StyxRequest) -> StyxResponse:
        """Handle read request."""
        with self._lock:
            if req.fid not in self._fid_fds:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="File not open"
                )
            
            fd = self._fid_fds[req.fid]
            count = req.data.get('count', self.msize)
            
            data = self.cogfs.read(fd, count)
        
        return StyxResponse(
            msg_type=StyxMessage.RREAD,
            tag=req.tag,
            data={'data': data}
        )
    
    def _handle_write(self, req: StyxRequest) -> StyxResponse:
        """Handle write request."""
        with self._lock:
            if req.fid not in self._fid_fds:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="File not open"
                )
            
            fd = self._fid_fds[req.fid]
            data = req.data.get('data', b'')
            
            count = self.cogfs.write(fd, data)
        
        return StyxResponse(
            msg_type=StyxMessage.RWRITE,
            tag=req.tag,
            data={'count': count}
        )
    
    def _handle_clunk(self, req: StyxRequest) -> StyxResponse:
        """Handle clunk (close) request."""
        with self._lock:
            if req.fid in self._fid_fds:
                self.cogfs.close(self._fid_fds[req.fid])
                del self._fid_fds[req.fid]
            
            if req.fid in self._fids:
                del self._fids[req.fid]
        
        return StyxResponse(
            msg_type=StyxMessage.RCLUNK,
            tag=req.tag
        )
    
    def _handle_stat(self, req: StyxRequest) -> StyxResponse:
        """Handle stat request."""
        with self._lock:
            if req.fid not in self._fids:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="Invalid fid"
                )
            
            path = self._fids[req.fid]
            stat = self.cogfs.stat(path)
            
            if not stat:
                return StyxResponse(
                    msg_type=StyxMessage.RERROR,
                    tag=req.tag,
                    error="Cannot stat"
                )
        
        return StyxResponse(
            msg_type=StyxMessage.RSTAT,
            tag=req.tag,
            data={'stat': stat}
        )


# Export
__all__ = [
    'FileMode',
    'FileType',
    'FileDescriptor',
    'CognitiveFile',
    'AtomFile',
    'AtomSetFile',
    'QueryFile',
    'StatsFile',
    'CognitiveFileSystem',
    'StyxMessage',
    'StyxRequest',
    'StyxResponse',
    'StyxServer',
]
