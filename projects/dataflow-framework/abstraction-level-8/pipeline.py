# pipeline.py
import yaml
import importlib
from typing import Any, Iterator, Tuple, List, Dict
from typez import ProcessorFn
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from metrics import MetricsStore

class ProcessorNode:
    def __init__(self, tag: str, processor: ProcessorFn):
        self.tag = tag
        self.processor = processor
        self.graph: nx.DiGraph | None = None  # optional graph reference
        
        # Set processor tag for metrics if it's a BaseProcessor instance
        if hasattr(processor, 'set_processor_tag'):
            processor.set_processor_tag(tag)

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
    metrics_store = MetricsStore.get_instance()
    
    for node_cfg in config.get("nodes", []):
        tag = node_cfg["tag"]
        processor = load_function(node_cfg["type"])
        
        # Create processor node and set tag for metrics
        nodes[tag] = ProcessorNode(tag, processor)
        
        # Initialize processor metrics
        metrics_store.record_processor_metrics(tag, 0.0, True)
    
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
    import time
    
    metrics_store = MetricsStore.get_instance()
    
    # Track routing-level metrics
    routing_start_time = time.time()
    total_lines_processed = 0
    
    pending = deque([(start_tag, line, 0, "") for line in lines])
    
    while pending:
        tag, line, hops, line_id = pending.popleft()
        
        if tag == "end":
            # Complete the trace if we have a line_id - FIXED VERSION
            if line_id and metrics_store.trace_enabled:
                # Provide all required parameters for enhanced add_trace_step
                metrics_store.add_trace_step(
                    line_id=line_id,
                    processor_tag="end",
                    input_content=line,
                    output_content=line,
                    output_tags=["end"],
                    processing_time=0.0
                )
                metrics_store.complete_trace(line_id, line)
            
            total_lines_processed += 1
            yield line
            continue
        
        if hops > max_hops:
            error_msg = f"Line exceeded max hops ({max_hops}) for tag '{tag}'. Possible infinite loop."
            metrics_store.record_error("router", Exception(error_msg), line)
            raise RuntimeError(error_msg)
        
        if tag not in nodes:
            error_msg = f"Line routed to unknown tag '{tag}'. Please check processor output or config."
            metrics_store.record_error("router", KeyError(error_msg), line)
            raise KeyError(error_msg)
        
        processor_node = nodes[tag]
        
        try:
            # Start trace for this line if not already started
            if not line_id and metrics_store.trace_enabled:
                line_id = metrics_store.start_trace(line)
            
            # Process the line through the current processor
            for out_tags, out_line in processor_node.processor(iter([line])):
                # Validate processor output
                if not isinstance(out_tags, list):
                    error_msg = f"Processor '{tag}' must yield a list of tags, got {type(out_tags).__name__}"
                    metrics_store.record_error(tag, TypeError(error_msg), line)
                    raise TypeError(error_msg)
                
                if not out_tags:
                    error_msg = f"Processor '{tag}' yielded an empty list of tags. Each line must have at least one tag."
                    metrics_store.record_error(tag, ValueError(error_msg), line)
                    raise ValueError(error_msg)
                
                for out_tag in out_tags:
                    if out_tag not in nodes and out_tag != "end":
                        error_msg = f"Processor '{tag}' emitted unknown tag '{out_tag}'. Add it to config."
                        metrics_store.record_error(tag, KeyError(error_msg), line)
                        raise KeyError(error_msg)
                    
                    # Add to pending with the same line_id for tracing continuity
                    pending.append((out_tag, out_line, hops + 1, line_id))
                    
        except Exception as e:
            # Error already recorded by BaseProcessor, just re-raise
            raise e
    
    # Record overall routing metrics
    total_routing_time = time.time() - routing_start_time
    print(f"Routing completed: {total_lines_processed} lines in {total_routing_time:.2f}s")
