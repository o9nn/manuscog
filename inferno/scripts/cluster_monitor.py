#!/usr/bin/env python3
"""
Inferno-OS Cluster Monitor
A lightweight Flask-based dashboard for monitoring distributed Inferno VM clusters.
Provides real-time status of cluster nodes, 9P connections, and cognitive services.
"""

import json
import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    print("Flask not installed. Install with: pip3 install flask")
    exit(1)

app = Flask(__name__)

CLUSTER_DIR = Path(os.environ.get("CLUSTER_DIR", "/var/inferno/cluster"))
BASE_PORT = int(os.environ.get("INFERNO_9P_PORT", "6666"))
CLUSTER_NODES = int(os.environ.get("INFERNO_CLUSTER_NODES", "3"))

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Inferno-OS Cluster Monitor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; margin: 2em; }
        h1 { color: #e94560; }
        .node { border: 1px solid #333; padding: 1em; margin: 0.5em 0; border-radius: 4px; }
        .running { border-color: #0f0; background: #0a1a0a; }
        .stopped { border-color: #f00; background: #1a0a0a; }
        .status-badge { padding: 2px 8px; border-radius: 3px; font-weight: bold; }
        .status-running { background: #0f0; color: #000; }
        .status-stopped { background: #f00; color: #fff; }
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid #333; padding: 8px; text-align: left; }
        th { background: #16213e; }
        .metric { font-size: 2em; color: #e94560; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; }
    </style>
</head>
<body>
    <h1>⚡ Inferno-OS Cluster Monitor</h1>
    <p>Last updated: {{ timestamp }}</p>
    <div class="grid">
        <div class="node"><div class="metric">{{ total_nodes }}</div>Total Nodes</div>
        <div class="node"><div class="metric" style="color:#0f0">{{ running_nodes }}</div>Running</div>
        <div class="node"><div class="metric" style="color:#f00">{{ stopped_nodes }}</div>Stopped</div>
        <div class="node"><div class="metric">{{ total_nodes * 1 }}</div>9P Endpoints</div>
    </div>
    <h2>Node Status</h2>
    <table>
        <tr><th>Node</th><th>Port</th><th>PID</th><th>Status</th><th>9P</th><th>Services</th></tr>
        {% for node in nodes %}
        <tr class="{{ 'running' if node.status == 'running' else 'stopped' }}">
            <td>{{ node.name }}</td>
            <td>{{ node.port }}</td>
            <td>{{ node.pid }}</td>
            <td><span class="status-badge status-{{ node.status }}">{{ node.status }}</span></td>
            <td>{{ '✓' if node.nine_p else '✗' }}</td>
            <td>{{ node.services | join(', ') }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is open."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_node_status(node_id: int) -> dict:
    """Get status of a single cluster node."""
    node_dir = CLUSTER_DIR / f"node-{node_id}"
    port = BASE_PORT + node_id
    pid_file = node_dir / "emu.pid"

    status = {
        "name": f"node-{node_id}",
        "port": port,
        "pid": "-",
        "status": "stopped",
        "nine_p": False,
        "services": [],
    }

    # Check PID file
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            status["pid"] = str(pid)
            # Check if process is alive
            os.kill(pid, 0)
            status["status"] = "running"
        except (ValueError, ProcessLookupError, PermissionError):
            status["status"] = "dead"

    # Check 9P port
    status["nine_p"] = check_port("localhost", port)

    # Read services
    services_file = node_dir / "registry" / "services"
    if services_file.exists():
        for line in services_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                svc_name = line.split("—")[0].strip() if "—" in line else line
                status["services"].append(svc_name)

    return status


@app.route("/")
def dashboard():
    """Render the cluster dashboard."""
    nodes = [get_node_status(i) for i in range(CLUSTER_NODES)]
    running = sum(1 for n in nodes if n["status"] == "running")
    return render_template_string(
        DASHBOARD_HTML,
        nodes=nodes,
        total_nodes=CLUSTER_NODES,
        running_nodes=running,
        stopped_nodes=CLUSTER_NODES - running,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/api/status")
def api_status():
    """Return cluster status as JSON."""
    nodes = [get_node_status(i) for i in range(CLUSTER_NODES)]
    return jsonify(
        {
            "cluster": {
                "total_nodes": CLUSTER_NODES,
                "running": sum(1 for n in nodes if n["status"] == "running"),
                "timestamp": datetime.now().isoformat(),
            },
            "nodes": nodes,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("MONITOR_PORT", "9090"))
    print(f"Inferno-OS Cluster Monitor starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
