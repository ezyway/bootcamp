# pipeline.py
import yaml
import importlib
from typing import Any, Iterator, Tuple, List, Dict
from typez import ProcessorFn

import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class ProcessorNode:
    def __init__(self, tag: str, processor: ProcessorFn):
        self.tag = tag
        self.processor = processor
        self.graph: nx.DiGraph | None = None  # optional graph reference

def load_function(import_path: str) -> ProcessorFn:
    module_path, name = import_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    obj = getattr(module, name)
    if isinstance(obj, type):
        obj = obj()
    if not callable(obj):
        raise TypeError(f"Processor '{import_path}' is not callable")
    return obj

def build_routing(config_path: str) -> Dict[str, ProcessorNode]:
    with open(config_path, "r") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    nodes: Dict[str, ProcessorNode] = {}
    for node_cfg in config.get("nodes", []):
        tag = node_cfg["tag"]
        processor = load_function(node_cfg["type"])
        nodes[tag] = ProcessorNode(tag, processor)
    
    if "start" not in nodes:
        raise ValueError("Config must include a 'start' node")
    if "end" not in nodes:
        raise ValueError("Config must include an 'end' node")

    graph = nx.DiGraph()
    for tag in nodes:
        graph.add_node(tag)

    for node_cfg in config.get("nodes", []):
        tag = node_cfg["tag"]
        for out_tag in node_cfg.get("routes", []):
            if out_tag not in nodes and out_tag != "end":
                raise KeyError(f"Node '{tag}' declares route to unknown tag '{out_tag}'")
            graph.add_edge(tag, out_tag)

    unreachable = set(nodes) - set(nx.descendants(graph, "start")) - {"start"}
    if unreachable:
        print(f"Warning: unreachable nodes from 'start': {unreachable}")

    try:
        cycles = list(nx.find_cycle(graph, orientation="original"))
        if cycles:
            print(f"Warning: detected cycles in routing graph: {cycles}")
    except nx.exception.NetworkXNoCycle:
        pass

    for node in nodes.values():
        node.graph = graph

    return nodes

def visualize_routing(nodes: Dict[str, ProcessorNode], title: str = "Routing Graph", output_file: str | None = None) -> None:
    """
    Visualize the routing graph using networkx and matplotlib.
    If output_file is provided, saves the figure instead of showing it.
    """
    any_node = next(iter(nodes.values()))
    graph = any_node.graph
    if graph is None:
        print("No graph available for visualization.")
        return

    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_color="skyblue", node_size=2000, edge_color="gray", arrowsize=20)
    plt.title(title)

    if output_file:
        plt.savefig(output_file)
        print(f"Graph saved to {output_file}")
    else:
        plt.show()


def run_router(start_tag: str, lines: Iterator[str], nodes: Dict[str, ProcessorNode], max_hops: int = 1000) -> Iterator[str]:
    from collections import deque

    pending = deque([(start_tag, line, 0) for line in lines])
    while pending:
        tag, line, hops = pending.popleft()
        if tag == "end":
            yield line
            continue

        if hops > max_hops:
            raise RuntimeError(f"Line exceeded max hops ({max_hops}) for tag '{tag}'. Possible infinite loop.")

        if tag not in nodes:
            raise KeyError(f"Line routed to unknown tag '{tag}'. Please check processor output or config.")

        processor_node = nodes[tag]
        for out_tags, out_line in processor_node.processor(iter([line])):
            # Validate processor output
            if not isinstance(out_tags, list):
                raise TypeError(f"Processor '{tag}' must yield a list of tags, got {type(out_tags).__name__}")
            if not out_tags:
                raise ValueError(f"Processor '{tag}' yielded an empty list of tags. Each line must have at least one tag.")

            for out_tag in out_tags:
                if out_tag not in nodes and out_tag != "end":
                    raise KeyError(f"Processor '{tag}' emitted unknown tag '{out_tag}'. Add it to config.")
                pending.append((out_tag, out_line, hops + 1))
