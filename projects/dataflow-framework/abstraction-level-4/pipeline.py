import yaml
import importlib
from typing import Any, Iterator
from processors.base import ProcessorFn

def load_function(import_path: str) -> ProcessorFn:
    """
    Dynamically import a processor from a dotted path like:
    - 'processors.upper.upper_processor' (streamified function)
    - 'processors.base.LineCounter' (stateful class)
    """
    try:
        module_path, name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        obj = getattr(module, name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ImportError(f"Could not import processor '{import_path}': {e}") from e

    # If it's a class, instantiate it
    if isinstance(obj, type):
        obj = obj()
    # Ensure it's callable
    if not callable(obj):
        raise TypeError(f"Processor '{import_path}' is not callable")
    return obj

def get_pipeline(config_path: str) -> list[ProcessorFn]:
    """
    Load a list of processors from a YAML config file. Each processor must be callable: Iterator[str] -> Iterator[str]
    """
    with open(config_path, "r") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    steps = config.get("pipeline", [])
    if not isinstance(steps, list):
        raise ValueError("Config must define a list under 'pipeline'")

    processors: list[ProcessorFn] = []
    for step in steps:
        if not isinstance(step, dict) or "type" not in step:
            raise ValueError(f"Invalid pipeline step: {step}")
        processors.append(load_function(step["type"]))

    return processors
