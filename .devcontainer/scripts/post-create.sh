#!/usr/bin/env bash
# =============================================================================
# Inferno-OS Devcontainer: Post-Create Setup
# Runs once after the container is first created.
# =============================================================================
set -euo pipefail

INFERNO_ROOT="${INFERNO_ROOT:-/usr/inferno}"
CLUSTER_NODES="${INFERNO_CLUSTER_NODES:-3}"
CLUSTER_DIR="/var/inferno/cluster"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Inferno-OS Cognitive Kernel — Post-Create Setup            ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ---- 1. Verify Inferno installation ----
echo "[1/6] Verifying Inferno-OS installation..."
if command -v emu &>/dev/null; then
    echo "  ✓ emu found at $(which emu)"
else
    echo "  ✗ emu not found — check INFERNO_ROOT and PATH"
    exit 1
fi

if command -v limbo &>/dev/null; then
    echo "  ✓ limbo compiler found at $(which limbo)"
else
    echo "  ✗ limbo compiler not found"
    exit 1
fi

# ---- 2. Create workspace structure ----
echo "[2/6] Creating workspace structure..."
mkdir -p /workspace/{src,dis,doc,tests,scripts,cluster}
mkdir -p /workspace/src/{appl,lib,module}

cat > /workspace/src/hello.b << 'LIMBO'
implement Hello;

include "sys.m";
    sys: Sys;
include "draw.m";

Hello: module {
    init: fn(nil: ref Draw->Context, nil: list of string);
};

init(nil: ref Draw->Context, nil: list of string)
{
    sys = load Sys Sys->PATH;
    sys->print("Hello from Inferno-OS Cognitive Kernel!\n");
}
LIMBO

echo "  ✓ Workspace structure created with sample hello.b"

# ---- 3. Create Limbo module template ----
echo "[3/6] Creating Limbo module templates..."
cat > /workspace/src/module/cogkernel.m << 'MODULE'
#
# Cognitive Kernel Module Interface
# Provides Limbo bindings for the OpenCog-Inferno kernel services.
#
CogKernel: module {
    PATH: con "/dis/lib/cogkernel.dis";

    # Atom types
    CONCEPT_NODE:       con 2;
    PREDICATE_NODE:     con 3;
    SCHEMA_NODE:        con 4;
    INHERITANCE_LINK:   con 101;
    SIMILARITY_LINK:    con 102;
    EVALUATION_LINK:    con 103;

    # Truth value
    TruthValue: adt {
        strength:   real;
        confidence: real;
    };

    # Attention value
    AttentionValue: adt {
        sti: int;
        lti: int;
    };

    # Core operations
    init:           fn(): int;
    shutdown:       fn();
    create_atom:    fn(atype: int, name: string, tv: TruthValue): big;
    get_atom:       fn(handle: big): (int, string, TruthValue);
    delete_atom:    fn(handle: big): int;
    pattern_match:  fn(pattern: big): list of big;
    infer:          fn(rule: big, premises: list of big): big;
};
MODULE

echo "  ✓ Limbo module templates created"

# ---- 4. Create cluster configuration ----
echo "[4/6] Configuring cluster (${CLUSTER_NODES} nodes)..."
for i in $(seq 0 $((CLUSTER_NODES - 1))); do
    NODE_DIR="${CLUSTER_DIR}/node-${i}"
    PORT=$((6666 + i))

    cat > "${NODE_DIR}/namespace/config" << EOF
# Inferno Cluster Node ${i} Configuration
# 9P/Styx listener on port ${PORT}
bind '#I' /net
listen -A tcp!*!${PORT} { export / & }
EOF

    cat > "${NODE_DIR}/registry/services" << EOF
# Services exported by Node ${i}
/cognitive/atomspace    — Distributed AtomSpace partition
/cognitive/inference    — PLN inference engine
/cognitive/attention    — ECAN attention allocation
/net/9p                 — 9P file service
EOF

    echo "  ✓ Node ${i} configured (port ${PORT})"
done

# ---- 5. Create cluster management script ----
echo "[5/6] Installing cluster management CLI..."
cat > /workspace/scripts/inferno-cluster << 'CLUSTER_CLI'
#!/usr/bin/env bash
# inferno-cluster — Manage distributed Inferno VM cluster
set -euo pipefail

CLUSTER_DIR="/var/inferno/cluster"
CLUSTER_NODES="${INFERNO_CLUSTER_NODES:-3}"
BASE_PORT=6666

usage() {
    cat << EOF
Usage: inferno-cluster <command> [options]

Commands:
  start [--nodes N]     Start the cluster (default: ${CLUSTER_NODES} nodes)
  stop                  Stop all cluster nodes
  status                Show cluster status
  connect <node-id>     Connect to a specific node
  deploy <file.dis>     Deploy a Dis module to all nodes
  logs [node-id]        Show logs (all or specific node)
  namespace <node-id>   Show namespace of a node
  mount <src> <dst>     Mount remote namespace
  export <path>         Export path via 9P

Examples:
  inferno-cluster start --nodes 5
  inferno-cluster deploy /workspace/dis/myapp.dis
  inferno-cluster connect 0
  inferno-cluster mount tcp!node-1!6667 /mnt/remote
EOF
}

cmd_start() {
    local nodes=${1:-$CLUSTER_NODES}
    echo "Starting Inferno cluster with ${nodes} nodes..."
    for i in $(seq 0 $((nodes - 1))); do
        local port=$((BASE_PORT + i))
        local logfile="${CLUSTER_DIR}/node-${i}/logs/emu.log"
        echo "  Starting node-${i} on port ${port}..."
        emu -c1 -r /usr/inferno \
            "bind '#I' /net; listen -A tcp!*!${port} { export / & }" \
            > "${logfile}" 2>&1 &
        echo $! > "${CLUSTER_DIR}/node-${i}/emu.pid"
        echo "  ✓ Node ${i} started (PID: $!, port: ${port})"
    done
    echo "Cluster started with ${nodes} nodes."
}

cmd_stop() {
    echo "Stopping Inferno cluster..."
    for pidfile in ${CLUSTER_DIR}/node-*/emu.pid; do
        if [ -f "${pidfile}" ]; then
            local pid=$(cat "${pidfile}")
            local node=$(basename $(dirname "${pidfile}"))
            if kill -0 "${pid}" 2>/dev/null; then
                kill "${pid}"
                echo "  ✓ Stopped ${node} (PID: ${pid})"
            fi
            rm -f "${pidfile}"
        fi
    done
    echo "Cluster stopped."
}

cmd_status() {
    echo "Inferno Cluster Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "%-10s %-8s %-8s %-20s\n" "NODE" "PID" "PORT" "STATUS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for i in $(seq 0 $((CLUSTER_NODES - 1))); do
        local port=$((BASE_PORT + i))
        local pidfile="${CLUSTER_DIR}/node-${i}/emu.pid"
        local status="stopped"
        local pid="-"
        if [ -f "${pidfile}" ]; then
            pid=$(cat "${pidfile}")
            if kill -0 "${pid}" 2>/dev/null; then
                status="running"
            else
                status="dead"
            fi
        fi
        printf "%-10s %-8s %-8s %-20s\n" "node-${i}" "${pid}" "${port}" "${status}"
    done
}

cmd_connect() {
    local node_id=${1:?Node ID required}
    local port=$((BASE_PORT + node_id))
    echo "Connecting to node-${node_id} on port ${port}..."
    emu -c1 -r /usr/inferno "mount tcp!localhost!${port} /mnt/node-${node_id}"
}

cmd_deploy() {
    local disfile=${1:?Dis file required}
    echo "Deploying ${disfile} to all nodes..."
    for i in $(seq 0 $((CLUSTER_NODES - 1))); do
        local port=$((BASE_PORT + i))
        echo "  Deploying to node-${i}..."
        # Copy dis file via 9P mount
        emu -c1 -r /usr/inferno \
            "mount tcp!localhost!${port} /mnt/deploy; cp ${disfile} /mnt/deploy/dis/"
        echo "  ✓ Deployed to node-${i}"
    done
}

cmd_logs() {
    local node_id=${1:-}
    if [ -n "${node_id}" ]; then
        tail -f "${CLUSTER_DIR}/node-${node_id}/logs/emu.log"
    else
        tail -f ${CLUSTER_DIR}/node-*/logs/emu.log
    fi
}

case "${1:-help}" in
    start)    shift; cmd_start "$@" ;;
    stop)     cmd_stop ;;
    status)   cmd_status ;;
    connect)  shift; cmd_connect "$@" ;;
    deploy)   shift; cmd_deploy "$@" ;;
    logs)     shift; cmd_logs "$@" ;;
    help|*)   usage ;;
esac
CLUSTER_CLI

chmod +x /workspace/scripts/inferno-cluster
sudo ln -sf /workspace/scripts/inferno-cluster /usr/local/bin/inferno-cluster
echo "  ✓ inferno-cluster CLI installed"

# ---- 6. Create Limbo build helper ----
echo "[6/6] Installing Limbo build tools..."
cat > /workspace/scripts/limbo-build << 'LIMBO_BUILD'
#!/usr/bin/env bash
# limbo-build — Compile and run Limbo programs
set -euo pipefail

usage() {
    cat << EOF
Usage: limbo-build <command> <file.b>

Commands:
  compile <file.b>      Compile Limbo source to Dis bytecode
  run <file.b>          Compile and run in emu
  check <file.b>        Type-check without generating code
  clean                 Remove all .dis and .sbl files

Examples:
  limbo-build compile src/hello.b
  limbo-build run src/hello.b
EOF
}

cmd_compile() {
    local src=${1:?Source file required}
    local dis="${src%.b}.dis"
    echo "Compiling ${src} → ${dis}"
    limbo -g -o "${dis}" "${src}"
    echo "✓ Compiled: ${dis}"
}

cmd_run() {
    local src=${1:?Source file required}
    local dis="${src%.b}.dis"
    cmd_compile "${src}"
    echo "Running ${dis} in emu..."
    emu -c1 -r /usr/inferno "${dis}"
}

cmd_check() {
    local src=${1:?Source file required}
    echo "Type-checking ${src}..."
    limbo -w "${src}"
    echo "✓ Type check passed"
}

cmd_clean() {
    echo "Cleaning build artifacts..."
    find /workspace -name "*.dis" -delete
    find /workspace -name "*.sbl" -delete
    echo "✓ Clean complete"
}

case "${1:-help}" in
    compile)  shift; cmd_compile "$@" ;;
    run)      shift; cmd_run "$@" ;;
    check)    shift; cmd_check "$@" ;;
    clean)    cmd_clean ;;
    help|*)   usage ;;
esac
LIMBO_BUILD

chmod +x /workspace/scripts/limbo-build
sudo ln -sf /workspace/scripts/limbo-build /usr/local/bin/limbo-build
echo "  ✓ limbo-build CLI installed"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Setup complete! Available commands:                        ║"
echo "║                                                             ║"
echo "║  limbo-build compile src/hello.b   — Compile Limbo source  ║"
echo "║  limbo-build run src/hello.b       — Compile and run       ║"
echo "║  inferno-cluster start             — Start VM cluster      ║"
echo "║  inferno-cluster status            — Show cluster status    ║"
echo "║  inferno-cluster deploy app.dis    — Deploy to cluster     ║"
echo "║  emu -c1                           — Start Inferno shell   ║"
echo "║                                                             ║"
echo "║  Workspace: /workspace                                     ║"
echo "║  Inferno:   ${INFERNO_ROOT}                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
