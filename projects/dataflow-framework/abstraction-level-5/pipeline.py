import yaml
import importlib
from typing import Any, Iterator, Callable, Iterable, Tuple, List
from typez import ProcessorFn

def load_function(import_path: str) -> ProcessorFn:
    module_path, name = import_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    obj = getattr(module, name)

    if isinstance(obj, type):
        obj = obj()
    if not callable(obj):
        raise TypeError(f"Processor '{import_path}' is not callable")
    
    return obj

class DAGNode:
    def __init__(self, name: str, processor: ProcessorFn, routes: dict[str, str]):
        self.name = name
        self.processor = processor
        self.routes = routes  # tag -> downstream node name
        self.output_nodes: list[DAGNode] = []

def build_dag(config_path: str) -> dict[str, DAGNode]:
    with open(config_path, "r") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    nodes: dict[str, DAGNode] = {}
    for node_cfg in config.get("nodes", []):
        name = node_cfg["name"]
        processor = load_function(node_cfg["type"])
        routes = node_cfg.get("routes", {})
        nodes[name] = DAGNode(name, processor, routes)

    # Connect nodes
    for node in nodes.values():
        node.output_nodes = [nodes[tgt] for tgt in node.routes.values() if tgt in nodes]

    return nodes

def run_dag(start_node: DAGNode, lines: Iterable[str]) -> Iterator[str]:
    # Each element: (tags, line, node)
    pending: list[Tuple[List[str], str, DAGNode]] = [( ["start"], line, start_node) for line in lines ]

    while pending:
        tags, line, node = pending.pop(0)
        for out_tags, out_line in node.processor(iter([line])):
            next_nodes = set()
            for tag in out_tags:
                if tag in node.routes:
                    next_nodes.add(node.routes[tag])
            if next_nodes:
                for next_node_name in next_nodes:
                    next_node = next((n for n in node.output_nodes if n.name == next_node_name), None)
                    if next_node:
                        # forward emitted tags
                        pending.append((out_tags, out_line, next_node))
            else:
                # No matching route -> output
                yield out_line
