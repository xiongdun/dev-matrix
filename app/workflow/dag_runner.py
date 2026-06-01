"""DAG 执行引擎模块。

提供基于有向无环图（DAG）的工作流执行引擎，支持拓扑排序、
并行分支执行和依赖驱动的阶段调度。

主要类：
    - DAGRunner: DAG 执行引擎，可被 Temporal Workflow 和 Pipeline 共用。
"""

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DAGNode:
    """DAG 节点，对应工作流中的一个阶段。"""

    id: str
    name: str
    agent: str
    agent_role: str = ""
    requires_approval: bool = False
    timeout_seconds: int = 300
    retries: int = 0
    condition: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_stage_dict(cls, data: dict[str, Any]) -> "DAGNode":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            agent=data.get("agent", ""),
            agent_role=data.get("agent_role", ""),
            requires_approval=data.get("requires_approval", False),
            timeout_seconds=data.get("timeout_seconds", 300),
            retries=data.get("retries", 0),
            condition=data.get("condition"),
            context=data.get("context", {}),
        )


@dataclass
class DAGEdge:
    """DAG 边，表示节点间的依赖关系。"""

    source: str
    target: str


@dataclass
class DAG:
    """有向无环图，表示工作流的拓扑结构。"""

    nodes: dict[str, DAGNode]
    edges: list[DAGEdge]
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    in_degree: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.adjacency = {nid: [] for nid in self.nodes}
        self.in_degree = dict.fromkeys(self.nodes, 0)
        for edge in self.edges:
            if edge.source in self.nodes and edge.target in self.nodes:
                self.adjacency[edge.source].append(edge.target)
                self.in_degree[edge.target] += 1

    @classmethod
    def from_flow_json(cls, flow_json_str: str) -> "DAG":
        """从 Vue Flow 的 flow_json 字符串解析 DAG。"""
        try:
            flow = json.loads(flow_json_str)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid flow_json: not valid JSON") from exc

        nodes = {}
        for node in flow.get("nodes", []):
            node_id = node.get("id", "")
            data = node.get("data", {})
            if not node_id:
                continue
            # 合并 node 顶层字段和 data 字段
            merged = {**node, **data}
            merged["id"] = node_id
            nodes[node_id] = DAGNode.from_stage_dict(merged)

        edges = []
        for edge in flow.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source and target:
                edges.append(DAGEdge(source=source, target=target))

        return cls(nodes=nodes, edges=edges)

    @classmethod
    def from_stages(cls, stages: list[dict[str, Any]]) -> "DAG":
        """从阶段列表（线性顺序）构建 DAG。"""
        nodes = {}
        edges = []
        for s in stages:
            nid = s["id"]
            nodes[nid] = DAGNode.from_stage_dict(s)
        for i in range(len(stages) - 1):
            edges.append(DAGEdge(source=stages[i]["id"], target=stages[i + 1]["id"]))
        return cls(nodes=nodes, edges=edges)

    def topological_sort(self) -> list[str]:
        """Kahn 算法拓扑排序，返回节点 ID 列表。"""
        in_deg = dict(self.in_degree)
        queue = deque([nid for nid, deg in in_deg.items() if deg == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)
            for neighbor in self.adjacency.get(current, []):
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in workflow graph")

        return result

    def get_ready_nodes(self, completed: set[str]) -> list[str]:
        """获取所有依赖已满足的节点（可并行执行）。"""
        ready = []
        for nid, node in self.nodes.items():
            if nid in completed:
                continue
            # 检查所有入边来源是否已完成
            prerequisites = [edge.source for edge in self.edges if edge.target == nid]
            if all(src in completed for src in prerequisites):
                ready.append(nid)
        return ready

    def get_predecessors(self, node_id: str) -> list[str]:
        """获取指定节点的所有前驱节点。"""
        return [edge.source for edge in self.edges if edge.target == node_id]

    def get_successors(self, node_id: str) -> list[str]:
        """获取指定节点的所有后继节点。"""
        return self.adjacency.get(node_id, [])


class DAGRunner:
    """DAG 执行引擎。

    负责解析 DAG 结构并按拓扑顺序调度阶段执行。
    本身不执行具体任务，只提供图遍历和调度逻辑。

    Example:
        dag = DAG.from_flow_json(flow_json)
        runner = DAGRunner(dag)
        for batch in runner.iter_batches():
            # batch 中的节点可以并行执行
            print(batch)
    """

    def __init__(self, dag: DAG):
        self.dag = dag
        self.completed: set[str] = set()
        self.failed: set[str] = set()

    def iter_batches(self):
        """按拓扑层级迭代，每次返回可并行执行的节点批次。"""
        while len(self.completed) + len(self.failed) < len(self.dag.nodes):
            ready = self.dag.get_ready_nodes(self.completed | self.failed)
            if not ready:
                break
            yield ready

    def mark_completed(self, node_id: str):
        """标记节点为已完成。"""
        self.completed.add(node_id)

    def mark_failed(self, node_id: str):
        """标记节点为失败。"""
        self.failed.add(node_id)

    def is_done(self) -> bool:
        """检查是否所有节点都已执行完毕。"""
        return len(self.completed) + len(self.failed) >= len(self.dag.nodes)

    def get_node(self, node_id: str) -> DAGNode | None:
        """按 ID 获取节点。"""
        return self.dag.nodes.get(node_id)
