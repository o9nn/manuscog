#!/usr/bin/env python3
"""
Parse the OpenCog DOM-shadow into a structured hypergraph of repos.

Each row from the scrape contains, in order:
  url, name, visibility, description, language, forks, forks_url, forks_label,
  stars, stars_url, stars_label, sep, prs, prs_url, prs_label

The file uses tab separators between fields. Empty descriptions and missing
languages produce empty fields, so we parse defensively.

Output:
  - opencog_repos.json: list of repo dicts
  - opencog_hyperedges.json: hyperedges mapping repos to DTE membrane subsystems
"""
import json
import re
from pathlib import Path


INPUT = Path("/home/ubuntu/upload/pasted_content.txt")
OUT_DIR = Path("/home/ubuntu/dte-evolution/hypergraph")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapping from repo name (or substring) -> DTE membrane subsystem
MEMBRANE_MAP = {
    # Hypergraph Memory Membrane
    "atomspace": "cognitive.memory.hypergraph",
    "atomspace-storage": "cognitive.memory.persistence",
    "atomspace-rocks": "cognitive.memory.persistence.rocksdb",
    "atomspace-pgres": "cognitive.memory.persistence.postgres",
    "atomspace-bridge": "cognitive.memory.bridge.sql",
    "atomspace-cog": "cognitive.memory.distributed.client",
    "atomspace-gpu": "cognitive.memory.compute.gpu",
    "atomspace-metta": "cognitive.memory.metta",
    "atomspace-dht": "cognitive.memory.distributed.dht",
    "atomspace-ipfs": "cognitive.memory.distributed.ipfs",
    "atomspace-typescript": "cognitive.memory.api.typescript",
    "atomspace-js": "cognitive.memory.api.javascript",
    "atomspace-explorer": "introspection.visualization.explorer",
    "atomspace-viz": "introspection.visualization.viz",
    "atomspace-restful": "communication.protocol.rest",
    "atomspace-websockets": "communication.protocol.websocket",
    "atomspace-rpc": "communication.protocol.grpc",
    "atomspace-agents": "extension.agents.atomspace",
    "atomese-simd": "cognitive.memory.compute.simd",
    "cogserver": "communication.distributed.cogserver",
    # Echo Propagation Engine
    "attention": "echo.propagation.attention",  # ECAN
    "miner": "echo.propagation.pattern_mining",
    "matrix": "echo.propagation.sparse_vector",
    # Reasoning Membrane
    "pln": "cognitive.reasoning.probabilistic",
    "ure": "cognitive.reasoning.unified_rules",
    "unify": "cognitive.reasoning.unification",
    "asmoses": "cognitive.evolution.semantic_search",
    "moses": "cognitive.evolution.meta_optimizing",
    "learn": "cognitive.evolution.symbolic_learning",
    "tv-toolbox": "cognitive.reasoning.truth_value",
    "distributional-value": "cognitive.reasoning.distributional",
    "evidence": "autognosis.evidence_gathering",
    # Grammar Membrane
    "link-grammar": "cognitive.grammar.link",
    "lg-atomese": "cognitive.grammar.atomese_bridge",
    "relex": "cognitive.grammar.dependency_extractor",
    "language-learning": "cognitive.grammar.unsupervised",
    "stochastic-language-generation": "cognitive.grammar.generation",
    "generate": "cognitive.grammar.network_synthesis",
    # Sensory Motor Interface
    "sensory": "extension.sensory.io",
    "vision": "extension.sensory.vision",
    "semantic-vision": "extension.sensory.semantic_vision",
    "perception": "extension.sensory.perception",
    "motor": "extension.motor.research",
    "spacetime": "extension.sensory.spacetime",
    "destin": "extension.sensory.deep_spatiotemporal",
    "python-destin": "extension.sensory.deep_spatiotemporal.python",
    "pi_vision": "extension.sensory.pi_vision",
    # Embodiment / Robotics
    "TinyCog": "embodiment.platform.tiny_robot",
    "blender_api": "embodiment.avatar.blender",
    "blender_api_msgs": "embodiment.avatar.ros_bridge",
    "ghost_bridge": "embodiment.dialog.ghost_bridge",
    "ros-behavior-scripting": "embodiment.eva.ros_api",
    "robots_config": "embodiment.config",
    "pau2motors": "embodiment.motor.pau",
    "ros_opencog_robot_embodiment": "embodiment.robot.ros",
    "unity3d-opencog-game": "embodiment.simulation.unity3d",
    "opencog-to-minecraft": "embodiment.simulation.minecraft",
    # Agents / Orchestration
    "agents": "extension.evolution.echo_agent",
    "rocca": "extension.evolution.rational_controlled_agent",
    "loving-ai": "extension.dialog.loving_ai",
    "loving-ai-ghost": "extension.dialog.loving_ai_ghost",
    "linkgrammar-relex-web": "extension.dialog.lg_relex_web",
    # Domain
    "agi-bio": "domain.bio.genomic",
    "cheminformatics": "domain.chem.molecular",
    "pln-brca-xp": "domain.bio.brca",
    # Infrastructure
    "cogutil": "infrastructure.cpp_utility",
    "ocpkg": "infrastructure.packaging",
    "opencog-debian": "infrastructure.packaging.debian",
    "opencog-nix": "infrastructure.packaging.nix",
    "guix-atomese": "infrastructure.packaging.guix",
    "opencog_rpi": "infrastructure.cross_compile.rpi",
    "docker": "infrastructure.deployment.docker",
    "guile-dbi": "infrastructure.scheme.dbi",
    "external-tools": "infrastructure.tools.external",
    "logicmoo_cogserver": "infrastructure.bridge.logicmoo",
    "opencog-cycl": "infrastructure.bridge.cyc",
    "opencog-neo4j": "infrastructure.persistence.neo4j",
    "pattern-index": "infrastructure.indexing",
    "dimensional-embedding": "cognitive.embedding.dimensional",
    "benchmark": "infrastructure.benchmark",
    "test-datasets": "infrastructure.test_data",
    # Meta / Documentation / Web
    ".github": "meta.profile_readme",
    "opencog.org": "meta.website",
    "link-grammar-website": "meta.website.lg",
    "rest-api-documentation": "meta.documentation.rest",
    "visualization": "introspection.visualization.legacy",
    "cogprotolab": "introspection.visualization.cogprotolab",
    "opencog": "meta.framework.umbrella",
    "python-attic": "meta.archive.python",
    "python-client": "meta.client.python",
}


def parse_row(line: str) -> dict | None:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 4:
        return None
    url = parts[0].strip()
    if not url.startswith("http"):
        return None
    name = parts[1].strip() if len(parts) > 1 else ""
    visibility = parts[2].strip() if len(parts) > 2 else ""
    description = parts[3].strip() if len(parts) > 3 else ""
    # The remaining fields are noisy. Try to find language, forks, stars, prs.
    # Heuristic: the first short non-numeric field after description that is not
    # a URL is the language.
    rest = parts[4:]
    language = ""
    nums = []
    for p in rest:
        p = p.strip()
        if not p:
            continue
        if p.startswith("http"):
            continue
        if "/" in p and "github.com" in p:
            continue
        if re.match(r"^[0-9]+(\.[0-9]+)?[kKmM]?$", p):
            nums.append(p)
        elif (
            re.match(r"^[A-Za-z][A-Za-z0-9 +#\-_.]*$", p)
            and not language
            and len(p) < 30
        ):
            language = p
        # Skip "39 forks" / "191 stars" / "0 pull requests" labels
    forks = nums[0] if len(nums) > 0 else "0"
    stars = nums[1] if len(nums) > 1 else "0"
    prs = nums[2] if len(nums) > 2 else "0"

    archived = "archive" in visibility.lower()
    membrane = MEMBRANE_MAP.get(name, "unmapped")

    return {
        "url": url,
        "name": name,
        "owner": "opencog",
        "visibility": visibility or "Public",
        "archived": archived,
        "description": description,
        "language": language,
        "forks": forks,
        "stars": stars,
        "open_prs": prs,
        "membrane_subsystem": membrane,
    }


def main() -> None:
    repos: list[dict] = []
    with INPUT.open() as f:
        # Skip the header line
        next(f, None)
        for line in f:
            row = parse_row(line)
            if row:
                repos.append(row)

    # Write canonical repo list
    repos_path = OUT_DIR / "opencog_repos.json"
    repos_path.write_text(json.dumps(repos, indent=2))

    # Build hyperedges:
    # A hyperedge maps one DTE membrane subsystem to N OpenCog repos.
    edges: dict[str, list[str]] = {}
    for r in repos:
        edges.setdefault(r["membrane_subsystem"], []).append(r["name"])
    hyperedges = [
        {
            "edge_id": f"oc_membrane::{subsys}",
            "type": "MembraneRealization",
            "membrane_subsystem": subsys,
            "members": sorted(members),
            "cardinality": len(members),
        }
        for subsys, members in sorted(edges.items())
    ]
    he_path = OUT_DIR / "opencog_hyperedges.json"
    he_path.write_text(json.dumps(hyperedges, indent=2))

    # Summary
    print(f"Parsed {len(repos)} repos into {len(hyperedges)} hyperedges.")
    print(f"  -> {repos_path}")
    print(f"  -> {he_path}")
    unmapped = [r["name"] for r in repos if r["membrane_subsystem"] == "unmapped"]
    if unmapped:
        print(f"Unmapped ({len(unmapped)}): {unmapped}")
    archived = [r["name"] for r in repos if r["archived"]]
    print(f"Archived: {len(archived)}")
    by_lang: dict[str, int] = {}
    for r in repos:
        by_lang[r["language"] or "(none)"] = (
            by_lang.get(r["language"] or "(none)", 0) + 1
        )
    print("Languages:")
    for lang, n in sorted(by_lang.items(), key=lambda x: -x[1]):
        print(f"  {lang}: {n}")


if __name__ == "__main__":
    main()
