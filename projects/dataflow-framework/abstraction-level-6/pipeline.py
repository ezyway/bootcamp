import yaml
import importlib
from typing import Any, Iterator, Tuple, List, Dict
from typez import ProcessorFn

class ProcessorNode:
    """
    Represents a processor state. Processes lines and emits (tag, line) pairs.
    """
    def __init__(self, tag: str, processor: ProcessorFn):
        self.tag = tag
        self.processor = processor

def load_function(import_path: str) -> ProcessorFn:
    """
    Dynamically load a processor function or callable class.
    """
    module_path, name = import_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    obj = getattr(module, name)
    if isinstance(obj, type):
        obj = obj()
    if not callable(obj):
        raise TypeError(f"Processor '{import_path}' is not callable")
    return obj

def build_routing(config_path: str) -> Dict[str, ProcessorNode]:
    """
    Build a tag-based routing map from YAML config.
    """
    with open(config_path, "r") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    nodes: Dict[str, ProcessorNode] = {}
    for node_cfg in config.get("nodes", []):
        tag = node_cfg["tag"]
        processor = load_function(node_cfg["type"])
        nodes[tag] = ProcessorNode(tag, processor)
    
    return nodes

def run_router(start_tag: str, lines: Iterator[str], nodes: Dict[str, ProcessorNode]) -> Iterator[str]:
    """
    Routes lines dynamically based on tags until 'end' is emitted.
    """
    from collections import deque

    # Each item: (current_tag, line)
    pending = deque([(start_tag, line) for line in lines])
    
    while pending:
        tag, line = pending.popleft()
        if tag == "end":
            yield line
            continue

        if tag not in nodes:
            raise KeyError(f"No processor registered for tag '{tag}'")
        
        processor_node = nodes[tag]
        for out_tags, out_line in processor_node.processor(iter([line])):
            # Fan-out: multiple output tags
            for out_tag in out_tags:
                pending.append((out_tag, out_line))
