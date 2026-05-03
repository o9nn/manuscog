"""
OpenCog Inferno AGI - Cognitive Process Scheduler
=================================================

The cognitive scheduler manages cognitive processes (CogProcs),
which are the units of cognitive work in the AGI OS.

Unlike traditional OS processes, CogProcs:
- Have attention budgets instead of time slices
- Compete for cognitive resources based on importance
- Can spawn sub-processes for parallel reasoning
- Communicate through the AtomSpace

This implements attention-based scheduling where more important
cognitive tasks get more processing resources.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
import heapq
from collections import deque
import uuid

from kernel.cognitive.types import (
    Atom, AtomHandle, AtomType, TruthValue, AttentionValue,
    CognitiveContext, CognitiveProcessState, CognitiveGoal, GoalState
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# COGNITIVE PROCESS TYPES
# =============================================================================

class CogProcType(Enum):
    """Types of cognitive processes."""
    INFERENCE = auto()      # Reasoning/inference process
    ATTENTION = auto()      # Attention management
    LEARNING = auto()       # Learning process
    PERCEPTION = auto()     # Sensory processing
    ACTION = auto()         # Action execution
    GOAL = auto()           # Goal management
    MEMORY = auto()         # Memory operations
    PATTERN = auto()        # Pattern recognition
    SYSTEM = auto()         # System maintenance


class CogProcPriority(Enum):
    """Priority levels for cognitive processes."""
    CRITICAL = 0    # Must run immediately
    HIGH = 1        # Important, run soon
    NORMAL = 2      # Standard priority
    LOW = 3         # Background tasks
    IDLE = 4        # Run when nothing else to do


@dataclass
class CognitiveProcess:
    """
    A cognitive process in the AGI OS.
    
    CogProcs are the fundamental units of cognitive work,
    analogous to processes in a traditional OS but designed
    for cognitive operations.
    """
    pid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    proc_type: CogProcType = CogProcType.INFERENCE
    priority: CogProcPriority = CogProcPriority.NORMAL
    state: CognitiveProcessState = CognitiveProcessState.READY
    
    # Attention budget
    attention_budget: float = 1.0
    attention_spent: float = 0.0
    
    # Parent/child relationships
    parent_pid: Optional[str] = None
    child_pids: List[str] = field(default_factory=list)
    
    # Working context
    context: CognitiveContext = field(default_factory=CognitiveContext)
    
    # Goal this process is working toward
    goal_id: Optional[str] = None
    
    # Execution state
    entry_point: Optional[Callable[['CognitiveProcess', AtomSpace], Any]] = None
    result: Any = None
    error: Optional[str] = None
    
    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    
    # Statistics
    cycles_executed: int = 0
    atoms_accessed: int = 0
    inferences_made: int = 0
    
    def __lt__(self, other):
        """For priority queue ordering."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.attention_budget > other.attention_budget


@dataclass
class SchedulerStats:
    """Statistics for the cognitive scheduler."""
    processes_created: int = 0
    processes_completed: int = 0
    processes_failed: int = 0
    total_cycles: int = 0
    total_attention_spent: float = 0.0
    context_switches: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'processes_created': self.processes_created,
            'processes_completed': self.processes_completed,
            'processes_failed': self.processes_failed,
            'total_cycles': self.total_cycles,
            'total_attention_spent': self.total_attention_spent,
            'context_switches': self.context_switches
        }


# =============================================================================
# PROCESS TABLE
# =============================================================================

class ProcessTable:
    """
    Table of all cognitive processes.
    """
    
    def __init__(self):
        self._processes: Dict[str, CognitiveProcess] = {}
        self._by_type: Dict[CogProcType, Set[str]] = {t: set() for t in CogProcType}
        self._by_state: Dict[CognitiveProcessState, Set[str]] = {s: set() for s in CognitiveProcessState}
        self._lock = threading.RLock()
    
    def add(self, proc: CognitiveProcess):
        """Add a process to the table."""
        with self._lock:
            self._processes[proc.pid] = proc
            self._by_type[proc.proc_type].add(proc.pid)
            self._by_state[proc.state].add(proc.pid)
    
    def remove(self, pid: str) -> Optional[CognitiveProcess]:
        """Remove a process from the table."""
        with self._lock:
            proc = self._processes.pop(pid, None)
            if proc:
                self._by_type[proc.proc_type].discard(pid)
                self._by_state[proc.state].discard(pid)
            return proc
    
    def get(self, pid: str) -> Optional[CognitiveProcess]:
        """Get a process by PID."""
        return self._processes.get(pid)
    
    def update_state(self, pid: str, new_state: CognitiveProcessState):
        """Update process state."""
        with self._lock:
            proc = self._processes.get(pid)
            if proc:
                self._by_state[proc.state].discard(pid)
                proc.state = new_state
                self._by_state[new_state].add(pid)
    
    def get_by_type(self, proc_type: CogProcType) -> List[CognitiveProcess]:
        """Get processes by type."""
        with self._lock:
            return [self._processes[pid] for pid in self._by_type[proc_type] if pid in self._processes]
    
    def get_by_state(self, state: CognitiveProcessState) -> List[CognitiveProcess]:
        """Get processes by state."""
        with self._lock:
            return [self._processes[pid] for pid in self._by_state[state] if pid in self._processes]
    
    def get_ready(self) -> List[CognitiveProcess]:
        """Get all ready processes."""
        return self.get_by_state(CognitiveProcessState.READY)
    
    def get_running(self) -> List[CognitiveProcess]:
        """Get all running processes."""
        return self.get_by_state(CognitiveProcessState.RUNNING)
    
    def count(self) -> int:
        """Get total process count."""
        return len(self._processes)
    
    def all(self) -> List[CognitiveProcess]:
        """Get all processes."""
        with self._lock:
            return list(self._processes.values())


# =============================================================================
# READY QUEUE
# =============================================================================

class ReadyQueue:
    """
    Priority queue for ready processes.
    
    Processes are ordered by:
    1. Priority level
    2. Attention budget (higher budget = run first)
    """
    
    def __init__(self):
        self._queue: List[Tuple[int, float, str]] = []  # (priority, -budget, pid)
        self._pids: Set[str] = set()
        self._lock = threading.Lock()
    
    def push(self, proc: CognitiveProcess):
        """Add a process to the ready queue."""
        with self._lock:
            if proc.pid not in self._pids:
                # Negative budget for max-heap behavior
                entry = (proc.priority.value, -proc.attention_budget, proc.pid)
                heapq.heappush(self._queue, entry)
                self._pids.add(proc.pid)
    
    def pop(self) -> Optional[str]:
        """Remove and return the highest priority process PID."""
        with self._lock:
            while self._queue:
                _, _, pid = heapq.heappop(self._queue)
                if pid in self._pids:
                    self._pids.discard(pid)
                    return pid
            return None
    
    def remove(self, pid: str):
        """Remove a process from the queue."""
        with self._lock:
            self._pids.discard(pid)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._pids) == 0
    
    def size(self) -> int:
        """Get queue size."""
        with self._lock:
            return len(self._pids)


# =============================================================================
# COGNITIVE SCHEDULER
# =============================================================================

class CognitiveScheduler:
    """
    The cognitive process scheduler.
    
    Implements attention-based scheduling where processes compete
    for cognitive resources based on their importance and attention budget.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        max_concurrent: int = 4,
        cycle_budget: float = 10.0
    ):
        self.atomspace = atomspace
        self.max_concurrent = max_concurrent
        self.cycle_budget = cycle_budget  # Total attention per cycle
        
        # Process management
        self.process_table = ProcessTable()
        self.ready_queue = ReadyQueue()
        
        # Currently running process
        self._current_proc: Optional[CognitiveProcess] = None
        
        # Statistics
        self.stats = SchedulerStats()
        
        # Service state
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_process_complete: List[Callable[[CognitiveProcess], None]] = []
        self._on_process_fail: List[Callable[[CognitiveProcess, str], None]] = []
    
    # =========================================================================
    # PROCESS MANAGEMENT
    # =========================================================================
    
    def create_process(
        self,
        name: str,
        proc_type: CogProcType,
        entry_point: Callable[[CognitiveProcess, AtomSpace], Any],
        priority: CogProcPriority = CogProcPriority.NORMAL,
        attention_budget: float = 1.0,
        parent_pid: Optional[str] = None,
        goal_id: Optional[str] = None
    ) -> CognitiveProcess:
        """Create a new cognitive process."""
        proc = CognitiveProcess(
            name=name,
            proc_type=proc_type,
            priority=priority,
            attention_budget=attention_budget,
            parent_pid=parent_pid,
            goal_id=goal_id,
            entry_point=entry_point,
            state=CognitiveProcessState.READY
        )
        
        # Add to process table
        self.process_table.add(proc)
        
        # Add to ready queue
        self.ready_queue.push(proc)
        
        # Update parent's children
        if parent_pid:
            parent = self.process_table.get(parent_pid)
            if parent:
                parent.child_pids.append(proc.pid)
        
        self.stats.processes_created += 1
        return proc
    
    def terminate_process(self, pid: str, error: Optional[str] = None):
        """Terminate a process."""
        with self._lock:
            proc = self.process_table.get(pid)
            if not proc:
                return
            
            # Update state
            proc.state = CognitiveProcessState.TERMINATED
            proc.finished_at = time.time()
            proc.error = error
            
            # Remove from ready queue
            self.ready_queue.remove(pid)
            
            # Terminate children
            for child_pid in proc.child_pids:
                self.terminate_process(child_pid, "Parent terminated")
            
            # Update stats
            if error:
                self.stats.processes_failed += 1
                self._notify_process_fail(proc, error)
            else:
                self.stats.processes_completed += 1
                self._notify_process_complete(proc)
            
            # Remove from table
            self.process_table.remove(pid)
    
    def suspend_process(self, pid: str):
        """Suspend a process."""
        with self._lock:
            proc = self.process_table.get(pid)
            if proc and proc.state == CognitiveProcessState.RUNNING:
                proc.state = CognitiveProcessState.WAITING
                self.process_table.update_state(pid, CognitiveProcessState.WAITING)
                self.ready_queue.remove(pid)
    
    def resume_process(self, pid: str):
        """Resume a suspended process."""
        with self._lock:
            proc = self.process_table.get(pid)
            if proc and proc.state == CognitiveProcessState.WAITING:
                proc.state = CognitiveProcessState.READY
                self.process_table.update_state(pid, CognitiveProcessState.READY)
                self.ready_queue.push(proc)
    
    def adjust_priority(self, pid: str, new_priority: CogProcPriority):
        """Adjust process priority."""
        with self._lock:
            proc = self.process_table.get(pid)
            if proc:
                proc.priority = new_priority
                # Re-add to queue with new priority
                if proc.state == CognitiveProcessState.READY:
                    self.ready_queue.remove(pid)
                    self.ready_queue.push(proc)
    
    def add_attention_budget(self, pid: str, amount: float):
        """Add attention budget to a process."""
        proc = self.process_table.get(pid)
        if proc:
            proc.attention_budget += amount
    
    # =========================================================================
    # SCHEDULING
    # =========================================================================
    
    def schedule(self) -> Optional[CognitiveProcess]:
        """Select the next process to run."""
        with self._lock:
            # Check if we can run more processes
            running = self.process_table.get_running()
            if len(running) >= self.max_concurrent:
                return None
            
            # Get highest priority ready process
            pid = self.ready_queue.pop()
            if not pid:
                return None
            
            proc = self.process_table.get(pid)
            if not proc:
                return None
            
            # Check attention budget
            if proc.attention_budget <= 0:
                # No budget, move to waiting
                proc.state = CognitiveProcessState.WAITING
                self.process_table.update_state(pid, CognitiveProcessState.WAITING)
                return self.schedule()  # Try next process
            
            # Update state
            proc.state = CognitiveProcessState.RUNNING
            proc.started_at = proc.started_at or time.time()
            self.process_table.update_state(pid, CognitiveProcessState.RUNNING)
            
            self.stats.context_switches += 1
            return proc
    
    def run_cycle(self):
        """Run one scheduling cycle."""
        with self._lock:
            self.stats.total_cycles += 1
            
            # Distribute cycle budget among running processes
            running = self.process_table.get_running()
            if not running:
                # Schedule new processes
                while len(running) < self.max_concurrent:
                    proc = self.schedule()
                    if not proc:
                        break
                    running.append(proc)
            
            if not running:
                return
            
            # Allocate attention budget for this cycle
            budget_per_proc = self.cycle_budget / len(running)
            
            for proc in running:
                self._execute_process_step(proc, budget_per_proc)
    
    def _execute_process_step(self, proc: CognitiveProcess, budget: float):
        """Execute one step of a process."""
        if not proc.entry_point:
            self.terminate_process(proc.pid, "No entry point")
            return
        
        # Deduct attention
        attention_cost = min(budget, proc.attention_budget)
        proc.attention_budget -= attention_cost
        proc.attention_spent += attention_cost
        self.stats.total_attention_spent += attention_cost
        
        try:
            # Execute process step
            result = proc.entry_point(proc, self.atomspace)
            proc.cycles_executed += 1
            
            # Check if process completed
            if result is not None:
                proc.result = result
                self.terminate_process(proc.pid)
            elif proc.attention_budget <= 0:
                # Out of budget, suspend
                proc.state = CognitiveProcessState.WAITING
                self.process_table.update_state(proc.pid, CognitiveProcessState.WAITING)
            else:
                # Continue running, re-add to ready queue
                proc.state = CognitiveProcessState.READY
                self.process_table.update_state(proc.pid, CognitiveProcessState.READY)
                self.ready_queue.push(proc)
                
        except Exception as e:
            self.terminate_process(proc.pid, str(e))
    
    # =========================================================================
    # SERVICE INTERFACE
    # =========================================================================
    
    def start(self) -> bool:
        """Start the scheduler."""
        if self._running:
            return False
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="cognitive-scheduler"
        )
        self._scheduler_thread.start()
        return True
    
    def stop(self) -> bool:
        """Stop the scheduler."""
        if not self._running:
            return False
        
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2.0)
        return True
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                self.run_cycle()
            except Exception as e:
                pass  # Log in production
            
            time.sleep(0.01)  # 100 Hz scheduling
    
    def status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            'running': self._running,
            'stats': self.stats.to_dict(),
            'process_count': self.process_table.count(),
            'ready_count': self.ready_queue.size(),
            'running_count': len(self.process_table.get_running())
        }
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def on_process_complete(self, callback: Callable[[CognitiveProcess], None]):
        """Register callback for process completion."""
        self._on_process_complete.append(callback)
    
    def on_process_fail(self, callback: Callable[[CognitiveProcess, str], None]):
        """Register callback for process failure."""
        self._on_process_fail.append(callback)
    
    def _notify_process_complete(self, proc: CognitiveProcess):
        """Notify callbacks of process completion."""
        for callback in self._on_process_complete:
            try:
                callback(proc)
            except:
                pass
    
    def _notify_process_fail(self, proc: CognitiveProcess, error: str):
        """Notify callbacks of process failure."""
        for callback in self._on_process_fail:
            try:
                callback(proc, error)
            except:
                pass


# =============================================================================
# INTER-PROCESS COMMUNICATION
# =============================================================================

@dataclass
class CogMessage:
    """Message for inter-process communication."""
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender_pid: str = ""
    recipient_pid: str = ""
    msg_type: str = "data"
    payload: Any = None
    timestamp: float = field(default_factory=time.time)
    requires_response: bool = False
    response_to: Optional[str] = None


class MessageQueue:
    """Message queue for a process."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
    
    def send(self, msg: CogMessage) -> bool:
        """Send a message to the queue."""
        with self._lock:
            if len(self._queue) >= self.max_size:
                return False
            self._queue.append(msg)
            return True
    
    def receive(self, timeout: float = 0) -> Optional[CogMessage]:
        """Receive a message from the queue."""
        with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None
    
    def peek(self) -> Optional[CogMessage]:
        """Peek at the next message without removing."""
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None
    
    def size(self) -> int:
        """Get queue size."""
        return len(self._queue)
    
    def clear(self):
        """Clear the queue."""
        with self._lock:
            self._queue.clear()


class IPCManager:
    """
    Inter-Process Communication manager.
    
    Manages message passing between cognitive processes.
    """
    
    def __init__(self):
        self._queues: Dict[str, MessageQueue] = {}
        self._channels: Dict[str, Set[str]] = {}  # channel -> subscribers
        self._lock = threading.RLock()
    
    def create_queue(self, pid: str) -> MessageQueue:
        """Create a message queue for a process."""
        with self._lock:
            if pid not in self._queues:
                self._queues[pid] = MessageQueue()
            return self._queues[pid]
    
    def delete_queue(self, pid: str):
        """Delete a process's message queue."""
        with self._lock:
            self._queues.pop(pid, None)
            # Remove from all channels
            for channel in self._channels.values():
                channel.discard(pid)
    
    def send(self, msg: CogMessage) -> bool:
        """Send a message to a process."""
        with self._lock:
            queue = self._queues.get(msg.recipient_pid)
            if queue:
                return queue.send(msg)
            return False
    
    def receive(self, pid: str, timeout: float = 0) -> Optional[CogMessage]:
        """Receive a message for a process."""
        queue = self._queues.get(pid)
        if queue:
            return queue.receive(timeout)
        return None
    
    def broadcast(self, sender_pid: str, channel: str, payload: Any):
        """Broadcast a message to all subscribers of a channel."""
        with self._lock:
            subscribers = self._channels.get(channel, set())
            for pid in subscribers:
                if pid != sender_pid:
                    msg = CogMessage(
                        sender_pid=sender_pid,
                        recipient_pid=pid,
                        msg_type="broadcast",
                        payload=payload
                    )
                    self.send(msg)
    
    def subscribe(self, pid: str, channel: str):
        """Subscribe a process to a channel."""
        with self._lock:
            if channel not in self._channels:
                self._channels[channel] = set()
            self._channels[channel].add(pid)
    
    def unsubscribe(self, pid: str, channel: str):
        """Unsubscribe a process from a channel."""
        with self._lock:
            if channel in self._channels:
                self._channels[channel].discard(pid)
    
    def get_queue_size(self, pid: str) -> int:
        """Get the size of a process's message queue."""
        queue = self._queues.get(pid)
        return queue.size() if queue else 0


# =============================================================================
# GOAL-DIRECTED PROCESS FACTORY
# =============================================================================

class GoalDirectedProcessFactory:
    """
    Factory for creating goal-directed cognitive processes.
    """
    
    def __init__(self, scheduler: CognitiveScheduler, atomspace: AtomSpace):
        self.scheduler = scheduler
        self.atomspace = atomspace
    
    def create_inference_process(
        self,
        goal: CognitiveGoal,
        inference_fn: Callable[[CognitiveProcess, AtomSpace], Any]
    ) -> CognitiveProcess:
        """Create an inference process for a goal."""
        return self.scheduler.create_process(
            name=f"inference_{goal.goal_id}",
            proc_type=CogProcType.INFERENCE,
            entry_point=inference_fn,
            priority=self._goal_to_priority(goal),
            attention_budget=goal.priority * 10,
            goal_id=goal.goal_id
        )
    
    def create_learning_process(
        self,
        name: str,
        learning_fn: Callable[[CognitiveProcess, AtomSpace], Any],
        priority: CogProcPriority = CogProcPriority.LOW
    ) -> CognitiveProcess:
        """Create a learning process."""
        return self.scheduler.create_process(
            name=name,
            proc_type=CogProcType.LEARNING,
            entry_point=learning_fn,
            priority=priority,
            attention_budget=5.0
        )
    
    def create_attention_process(
        self,
        attention_fn: Callable[[CognitiveProcess, AtomSpace], Any]
    ) -> CognitiveProcess:
        """Create an attention management process."""
        return self.scheduler.create_process(
            name="attention_manager",
            proc_type=CogProcType.ATTENTION,
            entry_point=attention_fn,
            priority=CogProcPriority.HIGH,
            attention_budget=float('inf')  # Always runs
        )
    
    def _goal_to_priority(self, goal: CognitiveGoal) -> CogProcPriority:
        """Convert goal priority to process priority."""
        if goal.priority >= 0.8:
            return CogProcPriority.HIGH
        elif goal.priority >= 0.5:
            return CogProcPriority.NORMAL
        elif goal.priority >= 0.2:
            return CogProcPriority.LOW
        else:
            return CogProcPriority.IDLE


# Export
__all__ = [
    'CogProcType',
    'CogProcPriority',
    'CognitiveProcess',
    'SchedulerStats',
    'ProcessTable',
    'ReadyQueue',
    'CognitiveScheduler',
    'CogMessage',
    'MessageQueue',
    'IPCManager',
    'GoalDirectedProcessFactory',
]
