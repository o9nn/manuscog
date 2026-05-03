#!/usr/bin/env python3
"""
Performance Benchmarking Suite
==============================

Comprehensive benchmarks for:
- AtomSpace scalability
- Inference throughput
- Attention allocation performance
- Cognitive cycle timing
- Memory efficiency
"""

import sys
import os
import time
import gc
import statistics
from dataclasses import dataclass
from typing import List, Dict, Any, Callable
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from atomspace.hypergraph.atomspace import AtomSpace
from kernel.reasoning.pln import PLNEngine, PLNConfig, PLNFormulas
from kernel.attention.ecan import ECANService, ECANParameters
from kernel.pattern.recognition import PatternRecognitionService
from kernel.learning.moses import MOSESEngine
from kernel.cognitive_kernel import boot_kernel


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    ops_per_second: float
    memory_mb: float = 0.0
    
    def __str__(self):
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total time: {self.total_time:.3f}s\n"
            f"  Avg time: {self.avg_time*1000:.3f}ms\n"
            f"  Min time: {self.min_time*1000:.3f}ms\n"
            f"  Max time: {self.max_time*1000:.3f}ms\n"
            f"  Std dev: {self.std_dev*1000:.3f}ms\n"
            f"  Ops/sec: {self.ops_per_second:.1f}\n"
            f"  Memory: {self.memory_mb:.1f}MB"
        )


class Benchmark:
    """Benchmark runner."""
    
    def __init__(self, name: str, warmup: int = 5, iterations: int = 100):
        self.name = name
        self.warmup = warmup
        self.iterations = iterations
        self.times: List[float] = []
        
    def run(self, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """Run the benchmark."""
        # Warmup
        for _ in range(self.warmup):
            func(*args, **kwargs)
        
        # Force GC before measurement
        gc.collect()
        
        # Measure
        self.times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            self.times.append(elapsed)
        
        # Calculate statistics
        total_time = sum(self.times)
        avg_time = statistics.mean(self.times)
        min_time = min(self.times)
        max_time = max(self.times)
        std_dev = statistics.stdev(self.times) if len(self.times) > 1 else 0
        ops_per_second = self.iterations / total_time if total_time > 0 else 0
        
        return BenchmarkResult(
            name=self.name,
            iterations=self.iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            ops_per_second=ops_per_second
        )


class AtomSpaceBenchmarks:
    """Benchmarks for AtomSpace operations."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def run_all(self) -> List[BenchmarkResult]:
        """Run all AtomSpace benchmarks."""
        print("\n=== AtomSpace Benchmarks ===\n")
        
        self.results = []
        self.results.append(self.bench_node_creation())
        self.results.append(self.bench_link_creation())
        self.results.append(self.bench_atom_lookup())
        self.results.append(self.bench_type_query())
        self.results.append(self.bench_large_atomspace())
        
        return self.results
        
    def bench_node_creation(self) -> BenchmarkResult:
        """Benchmark node creation."""
        atomspace = AtomSpace()
        counter = [0]
        
        def create_node():
            counter[0] += 1
            atomspace.add_node(AtomType.CONCEPT_NODE, f"Node_{counter[0]}")
        
        bench = Benchmark("Node Creation", warmup=10, iterations=1000)
        result = bench.run(create_node)
        print(result)
        return result
        
    def bench_link_creation(self) -> BenchmarkResult:
        """Benchmark link creation."""
        atomspace = AtomSpace()
        
        # Pre-create nodes
        nodes = []
        for i in range(100):
            nodes.append(atomspace.add_node(AtomType.CONCEPT_NODE, f"Node_{i}"))
        
        counter = [0]
        
        def create_link():
            counter[0] += 1
            i = counter[0] % len(nodes)
            j = (counter[0] + 1) % len(nodes)
            atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [nodes[i], nodes[j]],
                tv=TruthValue(0.9, 0.9)
            )
        
        bench = Benchmark("Link Creation", warmup=10, iterations=1000)
        result = bench.run(create_link)
        print(result)
        return result
        
    def bench_atom_lookup(self) -> BenchmarkResult:
        """Benchmark atom lookup by handle."""
        atomspace = AtomSpace()
        
        # Create atoms
        handles = []
        for i in range(1000):
            h = atomspace.add_node(AtomType.CONCEPT_NODE, f"Lookup_{i}")
            handles.append(h)
        
        counter = [0]
        
        def lookup_atom():
            counter[0] += 1
            h = handles[counter[0] % len(handles)]
            atomspace.get_atom(h)
        
        bench = Benchmark("Atom Lookup", warmup=10, iterations=10000)
        result = bench.run(lookup_atom)
        print(result)
        return result
        
    def bench_type_query(self) -> BenchmarkResult:
        """Benchmark querying atoms by type."""
        atomspace = AtomSpace()
        
        # Create mixed atoms
        for i in range(500):
            atomspace.add_node(AtomType.CONCEPT_NODE, f"Concept_{i}")
            atomspace.add_node(AtomType.PREDICATE_NODE, f"Predicate_{i}")
        
        def query_type():
            atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE)
        
        bench = Benchmark("Type Query", warmup=5, iterations=100)
        result = bench.run(query_type)
        print(result)
        return result
        
    def bench_large_atomspace(self) -> BenchmarkResult:
        """Benchmark operations on large AtomSpace."""
        atomspace = AtomSpace()
        
        # Create large atomspace
        print("  Creating large AtomSpace (10000 atoms)...")
        start = time.time()
        for i in range(10000):
            atomspace.add_node(AtomType.CONCEPT_NODE, f"Large_{i}")
        creation_time = time.time() - start
        print(f"  Created in {creation_time:.2f}s")
        
        def mixed_operations():
            # Add
            atomspace.add_node(AtomType.CONCEPT_NODE, f"New_{time.time()}")
            # Query
            atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE)
        
        bench = Benchmark("Large AtomSpace Ops", warmup=5, iterations=100)
        result = bench.run(mixed_operations)
        print(result)
        return result


class PLNBenchmarks:
    """Benchmarks for PLN reasoning."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def run_all(self) -> List[BenchmarkResult]:
        """Run all PLN benchmarks."""
        print("\n=== PLN Reasoning Benchmarks ===\n")
        
        self.results = []
        self.results.append(self.bench_deduction())
        self.results.append(self.bench_forward_chain())
        self.results.append(self.bench_revision())
        
        return self.results
        
    def bench_deduction(self) -> BenchmarkResult:
        """Benchmark deduction inference."""
        atomspace = AtomSpace()
        pln = PLNEngine(atomspace, PLNConfig())
        
        # Setup
        a = atomspace.add_node(AtomType.CONCEPT_NODE, "A")
        b = atomspace.add_node(AtomType.CONCEPT_NODE, "B")
        atomspace.add_link(
            AtomType.INHERITANCE_LINK, [a, b],
            tv=TruthValue(0.9, 0.9)
        )
        
        def run_deduction():
            pln.deduction(a, b)
        
        bench = Benchmark("PLN Deduction", warmup=5, iterations=100)
        result = bench.run(run_deduction)
        print(result)
        return result
        
    def bench_forward_chain(self) -> BenchmarkResult:
        """Benchmark forward chaining."""
        atomspace = AtomSpace()
        pln = PLNEngine(atomspace, PLNConfig())
        
        # Setup knowledge base
        nodes = []
        for i in range(20):
            nodes.append(atomspace.add_node(AtomType.CONCEPT_NODE, f"FC_{i}"))
        
        for i in range(len(nodes) - 1):
            atomspace.add_link(
                AtomType.INHERITANCE_LINK, [nodes[i], nodes[i+1]],
                tv=TruthValue(0.9, 0.9)
            )
        
        def run_forward_chain():
            pln.forward_chain(max_steps=10, focus_atoms={nodes[0]})
        
        bench = Benchmark("PLN Forward Chain", warmup=3, iterations=50)
        result = bench.run(run_forward_chain)
        print(result)
        return result
        
    def bench_revision(self) -> BenchmarkResult:
        """Benchmark truth value revision."""
        atomspace = AtomSpace()
        pln = PLNEngine(atomspace, PLNConfig())
        
        tv1 = TruthValue(0.8, 0.7)
        tv2 = TruthValue(0.75, 0.6)
        
        def run_revision():
            PLNFormulas.revision(tv1, tv2)
        
        bench = Benchmark("PLN Revision", warmup=10, iterations=1000)
        result = bench.run(run_revision)
        print(result)
        return result


class ECANBenchmarks:
    """Benchmarks for ECAN attention system."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def run_all(self) -> List[BenchmarkResult]:
        """Run all ECAN benchmarks."""
        print("\n=== ECAN Attention Benchmarks ===\n")
        
        self.results = []
        self.results.append(self.bench_stimulation())
        self.results.append(self.bench_focus_query())
        self.results.append(self.bench_attention_cycle())
        
        return self.results
        
    def bench_stimulation(self) -> BenchmarkResult:
        """Benchmark attention stimulation."""
        atomspace = AtomSpace()
        ecan = ECANService(atomspace, ECANParameters())
        
        # Create atoms
        atoms = []
        for i in range(100):
            h = atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Stim_{i}",
                av=AttentionValue(sti=0.3, lti=0.5)
            )
            atoms.append(h)
        
        counter = [0]
        
        def stimulate():
            counter[0] += 1
            ecan.stimulate(atoms[counter[0] % len(atoms)], 0.3)
        
        bench = Benchmark("ECAN Stimulation", warmup=10, iterations=1000)
        result = bench.run(stimulate)
        print(result)
        return result
        
    def bench_focus_query(self) -> BenchmarkResult:
        """Benchmark attentional focus query."""
        atomspace = AtomSpace()
        ecan = ECANService(atomspace, ECANParameters(focus_boundary=0.5))
        
        # Create atoms with varying attention
        for i in range(500):
            atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Focus_{i}",
                av=AttentionValue(sti=i/500, lti=0.5)
            )
        
        def query_focus():
            ecan.get_attentional_focus()
        
        bench = Benchmark("ECAN Focus Query", warmup=5, iterations=500)
        result = bench.run(query_focus)
        print(result)
        return result
        
    def bench_attention_cycle(self) -> BenchmarkResult:
        """Benchmark full attention cycle."""
        atomspace = AtomSpace()
        ecan = ECANService(atomspace, ECANParameters())
        
        # Create atoms
        for i in range(200):
            atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Cycle_{i}",
                av=AttentionValue(sti=i/200, lti=0.5)
            )
        
        def run_cycle():
            ecan.run_cycle()
        
        bench = Benchmark("ECAN Full Cycle", warmup=3, iterations=50)
        result = bench.run(run_cycle)
        print(result)
        return result


class CognitiveCycleBenchmarks:
    """Benchmarks for full cognitive cycles."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def run_all(self) -> List[BenchmarkResult]:
        """Run all cognitive cycle benchmarks."""
        print("\n=== Cognitive Cycle Benchmarks ===\n")
        
        self.results = []
        self.results.append(self.bench_single_cycle())
        self.results.append(self.bench_think_operation())
        self.results.append(self.bench_sustained_cycles())
        
        return self.results
        
    def bench_single_cycle(self) -> BenchmarkResult:
        """Benchmark single cognitive cycle."""
        kernel = boot_kernel(kernel_id="bench-single", log_level="ERROR")
        
        # Add some knowledge
        for i in range(50):
            kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"BenchConcept_{i}",
                av=AttentionValue(sti=i/50, lti=0.5)
            )
        
        def run_single_cycle():
            kernel.run_cycle()
        
        bench = Benchmark("Single Cognitive Cycle", warmup=3, iterations=30)
        result = bench.run(run_single_cycle)
        
        kernel.shutdown()
        print(result)
        return result
        
    def bench_think_operation(self) -> BenchmarkResult:
        """Benchmark think operation."""
        kernel = boot_kernel(kernel_id="bench-think", log_level="ERROR")
        
        # Add knowledge
        for i in range(50):
            kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"ThinkConcept_{i}",
                av=AttentionValue(sti=i/50, lti=0.5)
            )
        
        def run_think():
            kernel.think()
        
        bench = Benchmark("Think Operation", warmup=3, iterations=30)
        result = bench.run(run_think)
        
        kernel.shutdown()
        print(result)
        return result
        
    def bench_sustained_cycles(self) -> BenchmarkResult:
        """Benchmark sustained cognitive cycles."""
        kernel = boot_kernel(kernel_id="bench-sustained", log_level="ERROR")
        
        # Add knowledge
        for i in range(100):
            kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Sustained_{i}",
                av=AttentionValue(sti=i/100, lti=0.5)
            )
        
        def run_sustained():
            for _ in range(10):
                kernel.run_cycle()
                kernel.think()
        
        bench = Benchmark("Sustained Cycles (10)", warmup=2, iterations=10)
        result = bench.run(run_sustained)
        
        kernel.shutdown()
        print(result)
        return result


class ScalabilityBenchmarks:
    """Benchmarks for scalability testing."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def run_all(self) -> List[BenchmarkResult]:
        """Run all scalability benchmarks."""
        print("\n=== Scalability Benchmarks ===\n")
        
        self.results = []
        self.results.append(self.bench_scaling_atoms())
        self.results.append(self.bench_concurrent_access())
        
        return self.results
        
    def bench_scaling_atoms(self) -> BenchmarkResult:
        """Benchmark scaling with atom count."""
        sizes = [100, 1000, 5000, 10000]
        times = []
        
        for size in sizes:
            atomspace = AtomSpace()
            
            start = time.perf_counter()
            for i in range(size):
                atomspace.add_node(AtomType.CONCEPT_NODE, f"Scale_{i}")
            elapsed = time.perf_counter() - start
            
            times.append(elapsed)
            print(f"  {size} atoms: {elapsed:.3f}s ({size/elapsed:.0f} atoms/sec)")
        
        # Return result for largest size
        return BenchmarkResult(
            name="Atom Scaling",
            iterations=sizes[-1],
            total_time=times[-1],
            avg_time=times[-1]/sizes[-1],
            min_time=min(times)/min(sizes),
            max_time=max(times)/max(sizes),
            std_dev=0,
            ops_per_second=sizes[-1]/times[-1]
        )
        
    def bench_concurrent_access(self) -> BenchmarkResult:
        """Benchmark concurrent access."""
        atomspace = AtomSpace()
        
        # Pre-populate
        for i in range(1000):
            atomspace.add_node(AtomType.CONCEPT_NODE, f"Concurrent_{i}")
        
        errors = []
        operations = [0]
        lock = threading.Lock()
        
        def worker(worker_id):
            try:
                for i in range(100):
                    # Read
                    atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE)
                    # Write
                    atomspace.add_node(
                        AtomType.CONCEPT_NODE, 
                        f"Worker_{worker_id}_{i}"
                    )
                    with lock:
                        operations[0] += 2
            except Exception as e:
                errors.append(e)
        
        start = time.perf_counter()
        
        threads = []
        for i in range(4):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.perf_counter() - start
        
        result = BenchmarkResult(
            name="Concurrent Access (4 threads)",
            iterations=operations[0],
            total_time=elapsed,
            avg_time=elapsed/operations[0],
            min_time=0,
            max_time=0,
            std_dev=0,
            ops_per_second=operations[0]/elapsed
        )
        
        print(result)
        print(f"  Errors: {len(errors)}")
        return result


def run_all_benchmarks() -> Dict[str, List[BenchmarkResult]]:
    """Run all benchmark suites."""
    print("=" * 60)
    print(" OpenCog Inferno AGI - Performance Benchmarks")
    print("=" * 60)
    
    results = {}
    
    # AtomSpace benchmarks
    atomspace_bench = AtomSpaceBenchmarks()
    results['atomspace'] = atomspace_bench.run_all()
    
    # PLN benchmarks
    pln_bench = PLNBenchmarks()
    results['pln'] = pln_bench.run_all()
    
    # ECAN benchmarks
    ecan_bench = ECANBenchmarks()
    results['ecan'] = ecan_bench.run_all()
    
    # Cognitive cycle benchmarks
    cycle_bench = CognitiveCycleBenchmarks()
    results['cognitive_cycle'] = cycle_bench.run_all()
    
    # Scalability benchmarks
    scale_bench = ScalabilityBenchmarks()
    results['scalability'] = scale_bench.run_all()
    
    # Summary
    print("\n" + "=" * 60)
    print(" Benchmark Summary")
    print("=" * 60)
    
    for category, bench_results in results.items():
        print(f"\n{category.upper()}:")
        for r in bench_results:
            print(f"  {r.name}: {r.ops_per_second:.1f} ops/sec")
    
    return results


def generate_benchmark_report(results: Dict[str, List[BenchmarkResult]]) -> str:
    """Generate a markdown benchmark report."""
    report = []
    report.append("# OpenCog Inferno AGI - Performance Benchmark Report\n")
    report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for category, bench_results in results.items():
        report.append(f"\n## {category.replace('_', ' ').title()}\n")
        report.append("| Benchmark | Iterations | Avg Time (ms) | Ops/sec |")
        report.append("|-----------|------------|---------------|---------|")
        
        for r in bench_results:
            report.append(
                f"| {r.name} | {r.iterations} | {r.avg_time*1000:.2f} | {r.ops_per_second:.1f} |"
            )
    
    return "\n".join(report)


if __name__ == '__main__':
    results = run_all_benchmarks()
    
    # Generate report
    report = generate_benchmark_report(results)
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'benchmark_report.md')
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
