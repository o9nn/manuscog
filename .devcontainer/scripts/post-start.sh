#!/usr/bin/env bash
# =============================================================================
# Inferno-OS Devcontainer: Post-Start
# Runs every time the container starts (including restarts).
# =============================================================================
set -euo pipefail

INFERNO_ROOT="${INFERNO_ROOT:-/usr/inferno}"
CLUSTER_DIR="/var/inferno/cluster"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Inferno-OS Cognitive Kernel — Starting...                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ---- Verify Inferno binaries ----
if ! command -v emu &>/dev/null; then
    echo "⚠ Warning: emu not found in PATH"
    echo "  Attempting to fix PATH..."
    export PATH="${INFERNO_ROOT}/Linux/amd64/bin:${PATH}"
fi

# ---- Ensure Docker network exists (for cluster) ----
if command -v docker &>/dev/null; then
    docker network inspect inferno-cluster-net &>/dev/null 2>&1 || \
        docker network create inferno-cluster-net 2>/dev/null || true
fi

# ---- Ensure cluster directories exist ----
CLUSTER_NODES="${INFERNO_CLUSTER_NODES:-3}"
for i in $(seq 0 $((CLUSTER_NODES - 1))); do
    mkdir -p "${CLUSTER_DIR}/node-${i}/{namespace,registry,keys,logs}"
done

# ---- Display environment info ----
echo ""
echo "Environment:"
echo "  INFERNO_ROOT:  ${INFERNO_ROOT}"
echo "  EMU:           $(which emu 2>/dev/null || echo 'not found')"
echo "  LIMBO:         $(which limbo 2>/dev/null || echo 'not found')"
echo "  Cluster Nodes: ${CLUSTER_NODES}"
echo "  Workspace:     /workspace"
echo ""
echo "Ready. Use 'inferno-cluster start' to launch the VM cluster."
