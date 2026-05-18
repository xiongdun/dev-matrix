from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from app.code_intelligence.indexer import CodeIndexer


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str
    properties: Dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: Dict = field(default_factory=dict)


class CodeGraphBuilder:
    def __init__(self, indexer: CodeIndexer):
        self.indexer = indexer
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []

    def build(self) -> Dict:
        self._nodes.clear()
        self._edges.clear()

        all_symbols = self.indexer.get_all_symbols()
        for symbol_list in all_symbols.values():
            for symbol in symbol_list:
                node_id = f"{symbol.file_path}:{symbol.name}"
                self._nodes[node_id] = GraphNode(
                    id=node_id,
                    label=symbol.name,
                    node_type=symbol.symbol_type,
                    properties={
                        "file_path": symbol.file_path,
                        "line_start": symbol.line_start,
                        "line_end": symbol.line_end,
                        "signature": symbol.signature,
                    },
                )

        for symbol_list in all_symbols.values():
            for symbol in symbol_list:
                source_id = f"{symbol.file_path}:{symbol.name}"
                for dep in symbol.dependencies:
                    for target in self.indexer.find_symbol(dep):
                        target_id = f"{target.file_path}:{target.name}"
                        if target_id in self._nodes:
                            self._edges.append(
                                GraphEdge(
                                    source=source_id,
                                    target=target_id,
                                    relation="DEPENDS_ON",
                                )
                            )

        file_index = self.indexer._index
        for file_path, fidx in file_index.items():
            file_node_id = f"file:{file_path}"
            self._nodes[file_node_id] = GraphNode(
                id=file_node_id,
                label=file_path,
                node_type="file",
                properties={"language": fidx.language},
            )
            for symbol in fidx.symbols:
                symbol_node_id = f"{symbol.file_path}:{symbol.name}"
                self._edges.append(
                    GraphEdge(
                        source=symbol_node_id,
                        target=file_node_id,
                        relation="DEFINED_IN",
                    )
                )

        return {
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.node_type, **n.properties}
                for n in self._nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "relation": e.relation}
                for e in self._edges
            ],
        }

    def get_neighbors(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[GraphNode]:
        neighbor_ids: Set[str] = set()
        for edge in self._edges:
            if edge.source == node_id:
                if relation is None or edge.relation == relation:
                    neighbor_ids.add(edge.target)
            elif edge.target == node_id:
                if relation is None or edge.relation == relation:
                    neighbor_ids.add(edge.source)
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def find_paths(
        self, start_id: str, end_id: str, max_depth: int = 5
    ) -> List[List[str]]:
        paths: List[List[str]] = []
        visited: Set[str] = set()

        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == end_id:
                paths.append(path.copy())
                return
            for edge in self._edges:
                if edge.source == current and edge.target not in visited:
                    visited.add(edge.target)
                    path.append(edge.target)
                    dfs(edge.target, path, depth + 1)
                    path.pop()
                    visited.discard(edge.target)

        visited.add(start_id)
        dfs(start_id, [start_id], 0)
        return paths


class AbstractCodeGraph(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def add_node(self, node: GraphNode) -> None:
        pass

    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None:
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        pass

    @abstractmethod
    def query_neighbors(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[GraphNode]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class InMemoryCodeGraph(AbstractCodeGraph):
    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def add_node(self, node: GraphNode) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self._edges.append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def query_neighbors(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[GraphNode]:
        neighbor_ids: Set[str] = set()
        for edge in self._edges:
            if edge.source == node_id and (
                relation is None or edge.relation == relation
            ):
                neighbor_ids.add(edge.target)
            elif edge.target == node_id and (
                relation is None or edge.relation == relation
            ):
                neighbor_ids.add(edge.source)
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()


class Neo4jCodeGraph(AbstractCodeGraph):
    def __init__(self, uri: str, user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    def connect(self) -> None:
        try:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            if self._driver is not None:
                self._driver.verify_connectivity()
        except ImportError:
            raise RuntimeError(
                "neo4j package not installed. Install with: pip install neo4j"
            )

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    def add_node(self, node: GraphNode) -> None:
        if not self._driver:
            raise RuntimeError("Graph not connected")
        with self._driver.session() as session:
            session.run(
                "MERGE (n:CodeNode {id: $id}) "
                "SET n.label = $label, n.type = $type, n += $props",
                id=node.id,
                label=node.label,
                type=node.node_type,
                props=node.properties,
            )

    def add_edge(self, edge: GraphEdge) -> None:
        if not self._driver:
            raise RuntimeError("Graph not connected")
        with self._driver.session() as session:
            session.run(
                "MATCH (a:CodeNode {id: $source}), (b:CodeNode {id: $target}) "
                "MERGE (a)-[r:RELATES {type: $relation}]->(b) "
                "SET r += $props",
                source=edge.source,
                target=edge.target,
                relation=edge.relation,
                props=edge.properties,
            )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        if not self._driver:
            raise RuntimeError("Graph not connected")
        with self._driver.session() as session:
            result = session.run(
                "MATCH (n:CodeNode {id: $id}) RETURN n", id=node_id
            ).single()
            if result:
                data = result["n"]
                return GraphNode(
                    id=data["id"],
                    label=data["label"],
                    node_type=data["type"],
                    properties={
                        k: v
                        for k, v in data.items()
                        if k not in ("id", "label", "type")
                    },
                )
            return None

    def query_neighbors(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[GraphNode]:
        if not self._driver:
            raise RuntimeError("Graph not connected")
        with self._driver.session() as session:
            if relation:
                result = session.run(
                    "MATCH (n:CodeNode {id: $id})-[:RELATES {type: $rel}]-(m) RETURN m",
                    id=node_id,
                    rel=relation,
                )
            else:
                result = session.run(
                    "MATCH (n:CodeNode {id: $id})-[:RELATES]-(m) RETURN m",
                    id=node_id,
                )
            nodes = []
            for record in result:
                data = record["m"]
                nodes.append(
                    GraphNode(
                        id=data["id"],
                        label=data["label"],
                        node_type=data["type"],
                        properties={
                            k: v
                            for k, v in data.items()
                            if k not in ("id", "label", "type")
                        },
                    )
                )
            return nodes

    def clear(self) -> None:
        if not self._driver:
            raise RuntimeError("Graph not connected")
        with self._driver.session() as session:
            session.run("MATCH (n:CodeNode) DETACH DELETE n")
