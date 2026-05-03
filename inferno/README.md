# Inferno-OS Cognitive Kernel Development

This directory contains Inferno-OS / Limbo source code and tooling for the ManusCog cognitive kernel, bridging the Python-based cognitive architecture with native Inferno distributed services.

## Directory Structure

```
inferno/
├── src/            ← Limbo source files (.b)
│   └── cogkernel.b ← Cognitive kernel demo module
├── dis/            ← Compiled Dis bytecode (.dis)
├── scripts/        ← Management and monitoring tools
│   └── cluster_monitor.py
├── mkfile          ← Inferno build file
└── README.md
```

## Quick Start

Inside the devcontainer:

```bash
# Compile the demo module
limbo-build compile inferno/src/cogkernel.b

# Run it in emu
limbo-build run inferno/src/cogkernel.b

# Start the distributed cluster
inferno-cluster start

# Check cluster status
inferno-cluster status
```

## Relationship to ManusCog

The Inferno layer provides native distributed OS capabilities that complement the Python cognitive kernel:

| ManusCog Component | Inferno Equivalent |
|-------------------|--------------------|
| `kernel/cognitive_kernel.py` | `inferno/src/cogkernel.b` (Limbo bindings) |
| `distributed/styx/` | Native 9P/Styx protocol |
| `distributed/coordination/` | Inferno namespace composition |
| `atomspace/` | Distributed AtomSpace via 9P |
| `net/` | Inferno network stack |

## Building

Use `mk` (Inferno's build tool) from within the devcontainer:

```bash
cd /workspace/inferno
mk install
```

Or use the `limbo-build` CLI wrapper for individual files.
