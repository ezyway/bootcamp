import yaml
import importlib
from typing import Any
from typez import ProcessorFn

def load_function(import_path: str) -> ProcessorFn:
    """Dynamically import a function from a dotted path like 'processors.upper.to_uppercase'."""
    try:
        module_path, func_name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        fn = getattr(module, func_name)
    except (ValueError, ImportError, AttributeError) as e:
        raise ImportError(f"Could not import processor '{import_path}': {e}") from e

    if not callable(fn):
        raise TypeError(f"Processor '{import_path}' is not callable")
    return fn

def get_pipeline(config_path: str) -> list[ProcessorFn]:
    """Load pipeline steps from YAML config file."""
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
