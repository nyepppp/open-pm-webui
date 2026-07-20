"""DAG (Directed Acyclic Graph) parser and executor for workflow execution."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class DAGNode:
    """Represents a node in the DAG."""
    id: str
    type: str
    config: dict = field(default_factory=dict)
    inputs: List[dict] = field(default_factory=list)
    outputs: List[dict] = field(default_factory=list)


@dataclass
class DAGEdge:
    """Represents an edge in the DAG."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None
    data_mapping: Dict[str, str] = field(default_factory=dict)


class DAG:
    """Directed Acyclic Graph for workflow execution."""
    
    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: Dict[str, DAGEdge] = {}
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self._indegree: Dict[str, int] = defaultdict(int)
    
    def add_node(self, node: DAGNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.id] = node
        if node.id not in self._indegree:
            self._indegree[node.id] = 0
    
    def add_edge(self, edge: DAGEdge) -> None:
        """Add an edge to the DAG."""
        self.edges[edge.id] = edge
        self._adjacency[edge.source].append(edge.target)
        self._reverse_adjacency[edge.target].append(edge.source)
        self._indegree[edge.target] += 1
    
    def topological_sort(self) -> List[str]:
        """Perform topological sort on the DAG."""
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = self._indegree.get(node_id, 0)
        
        queue = deque([node_id for node_id in self.nodes if in_degree[node_id] == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for neighbor in self._adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains a cycle. DAG must be acyclic.")
        
        return result
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """Get all predecessor nodes for a given node."""
        return self._reverse_adjacency.get(node_id, [])
    
    def get_successors(self, node_id: str) -> List[str]:
        """Get all successor nodes for a given node."""
        return self._adjacency.get(node_id, [])
    
    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate the DAG structure."""
        connected_nodes = set()
        for edge in self.edges.values():
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        for node_id in self.nodes:
            if node_id not in connected_nodes and len(self.nodes) > 1:
                return False, f"Node '{node_id}' is disconnected from the workflow"
        
        try:
            self.topological_sort()
        except ValueError as e:
            return False, str(e)
        
        return True, None


def parse_dag(nodes: List[dict], edges: List[dict]) -> DAG:
    """Parse nodes and edges into a DAG."""
    dag = DAG()
    
    for node_data in nodes:
        node = DAGNode(
            id=node_data['id'],
            type=node_data['type'],
            config=node_data.get('config', {}),
            inputs=node_data.get('inputs', []),
            outputs=node_data.get('outputs', [])
        )
        dag.add_node(node)
    
    for edge_data in edges:
        edge = DAGEdge(
            id=edge_data['id'],
            source=edge_data['source'],
            target=edge_data['target'],
            condition=edge_data.get('condition'),
            label=edge_data.get('label'),
            data_mapping=edge_data.get('data_mapping', {})
        )
        dag.add_edge(edge)
    
    return dag
