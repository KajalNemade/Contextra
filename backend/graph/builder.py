"""
Dependency graph builder using NetworkX.
Builds file-level and module-level import graphs.
Works completely offline — no AI needed.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import networkx as nx
import structlog

log = structlog.get_logger()


class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_file(self, path: str, language: str, loc: int):
        self.graph.add_node(path, type="file", language=language, loc=loc)

    def add_import(self, from_file: str, imported_module: str):
        """Add an edge: from_file depends on imported_module."""
        if not self.graph.has_node(imported_module):
            self.graph.add_node(imported_module, type="module")
        self.graph.add_edge(from_file, imported_module, relation="imports")

    def get_dependencies(self, path: str) -> List[str]:
        """What does path import?"""
        return list(self.graph.successors(path))

    def get_dependents(self, path: str) -> List[str]:
        """What imports path?"""
        return list(self.graph.predecessors(path))

    def impact_analysis(self, path: str) -> Dict[str, Any]:
        """What breaks if path changes?"""
        # BFS reverse — everything that depends (transitively) on path
        affected = set()
        queue = [path]
        while queue:
            current = queue.pop(0)
            for pred in self.graph.predecessors(current):
                if pred not in affected:
                    affected.add(pred)
                    queue.append(pred)
        files = [n for n in affected if self.graph.nodes[n].get("type") == "file"]
        return {
            "changed_file": path,
            "affected_files": files,
            "affected_count": len(files),
        }

    def get_entry_points(self) -> List[str]:
        """Files that nothing imports — likely entry points."""
        return [
            n for n in self.graph.nodes
            if self.graph.in_degree(n) == 0
            and self.graph.nodes[n].get("type") == "file"
        ]

    def detect_circular(self) -> List[List[str]]:
        """Return list of circular dependency cycles."""
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph for API response / React Flow."""
        nodes = []
        edges = []

        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "type": data.get("type", "unknown"),
                "language": data.get("language"),
                "loc": data.get("loc", 0),
            })

        for src, dst, data in self.graph.edges(data=True):
            edges.append({
                "source": src,
                "target": dst,
                "relation": data.get("relation", "imports"),
            })

        return {"nodes": nodes, "edges": edges}

    def get_architecture_layers(self) -> Dict[str, Any]:
        """
        Heuristic layer detection from folder structure.
        frontend/ → UI layer
        api/ routes/ → API layer
        services/ → Service layer
        models/ db/ → Data layer
        """
        layers: Dict[str, List[str]] = {
            "ui": [],
            "api": [],
            "services": [],
            "data": [],
            "utils": [],
            "other": [],
        }

        for node_id in self.graph.nodes:
            if self.graph.nodes[node_id].get("type") != "file":
                continue
            p = node_id.lower()
            if any(k in p for k in ("frontend", "ui", "component", "page", "view")):
                layers["ui"].append(node_id)
            elif any(k in p for k in ("api", "route", "endpoint", "controller")):
                layers["api"].append(node_id)
            elif any(k in p for k in ("service", "handler", "manager")):
                layers["services"].append(node_id)
            elif any(k in p for k in ("model", "db", "database", "schema", "migration", "repo")):
                layers["data"].append(node_id)
            elif any(k in p for k in ("util", "helper", "common", "shared", "lib")):
                layers["utils"].append(node_id)
            else:
                layers["other"].append(node_id)

        return {k: v for k, v in layers.items() if v}


def build_graph_from_files(file_imports: List[Dict]) -> DependencyGraph:
    """
    file_imports: list of {path, language, loc, imports: [{module, is_relative}]}
    """
    g = DependencyGraph()
    for fi in file_imports:
        g.add_file(fi["path"], fi["language"], fi.get("loc", 0))
        for imp in fi.get("imports", []):
            module = imp["module"]
            if imp.get("is_relative"):
                # Resolve relative import to a likely path
                base = "/".join(fi["path"].split("/")[:-1])
                resolved = f"{base}/{module.replace('.', '/')}" if base else module
                g.add_import(fi["path"], resolved)
            else:
                g.add_import(fi["path"], module)
    return g
