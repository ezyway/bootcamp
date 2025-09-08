## 📄 `cli.py` Explanation

```python
import typer
from typing_extensions import Annotated
from dotenv import load_dotenv

from main import run
```

* **Imports**:

  * `typer`: A modern library for creating CLI applications.
  * `Annotated` from `typing_extensions`: Used for enriching function arguments with metadata.
  * `load_dotenv`: Loads environment variables from a `.env` file.
  * `run` from `main`: The main function that executes the DAG pipeline.

```python
load_dotenv()
app = typer.Typer(help="Run a DAG-based line processing pipeline.")
```

* `load_dotenv()` ensures environment variables in `.env` are available.
* `app = typer.Typer(...)` creates the CLI app with a helpful description.

```python
@app.command()
def main(
    input: Annotated[str, typer.Argument()],
    config: Annotated[
        str,
        typer.Option(help="Path to DAG pipeline config file (YAML). Defaults to pipeline.yaml."),
    ] = "pipeline.yaml",
    output: Annotated[
        str | None,
        typer.Option(help="Specify output file. If not specified, prints to console."),
    ] = None,
):
    """
    Run a DAG pipeline on input lines. Each processor can yield tagged lines, which
    are routed according to the DAG config.
    """
    run(input, config, output)
```

* **Defines CLI command `main`**:

  * `input`: Positional argument → path to input file.
  * `config`: Optional argument → path to YAML config (default: `pipeline.yaml`).
  * `output`: Optional argument → output file path (if omitted, prints to console).
* Inside the function, it calls `run(input, config, output)` to execute the pipeline.

```python
if __name__ == "__main__":
    app()
```

* Standard Python entry point. If the script is run directly, the Typer CLI launches.

**Summary:**

* The new `cli.py` acts as a clean command-line interface to run the DAG pipeline.
* It keeps argument handling minimal and delegates all processing to `main.run`.

---
---

## 📄 `core.py` Explanation 

```python
from typing import Iterator, Tuple, List
from typez import ProcessorFn
```

* **Imports**:

  * `Iterator`, `Tuple`, `List` from `typing`: For type annotations.
  * `ProcessorFn` from `typez`: Standard type alias for processor functions.

```python
def to_uppercase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    """
    Convert lines to uppercase and emit them with 'end' tag.
    """
    for line in lines:
        yield (["end"], line.upper())
```

* **`to_uppercase` function**:

  * Converts each input line to uppercase.
  * Yields a tuple: `tags = ['end']` and the processed line.
  * **Change vs old version:** The tag is now `'end'` instead of `'uppercase'`.

```python
def to_snakecase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    """
    Convert lines to snake_case and emit them with 'end' tag.
    """
    for line in lines:
        yield (["end"], line.replace(" ", "_").lower())
```

* **`to_snakecase` function**:

  * Replaces spaces with underscores and converts text to lowercase.
  * Yields with tag `'end'`.
  * **Change:** Tag updated from `'snake'` to `'end'`.

```python
def trim(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    """Trim whitespace and emit lines with 'trimmed' tag."""
    for line in lines:
        yield (["trimmed"], line.strip())
```

* **`trim` function**:

  * Removes leading/trailing whitespace.
  * Tags lines with `'trimmed'` (unchanged from old version).

**Summary:**

* `core.py` provides basic text processing functions.
* Lines are emitted with specific tags used for DAG routing:

  * `trim` → `'trimmed'`
  * `to_uppercase` → `'end'`
  * `to_snakecase` → `'end'`
* The tag changes indicate that both uppercase and snake\_case outputs now share a common end tag for routing.

---
---

## 📄 `main.py` Explanation

```python
import os
from typing import Iterator, Optional
from pipeline import build_routing, run_router
```

* **Imports**:

  * `os`: For file path and directory operations.
  * `Iterator`, `Optional` from `typing`: For type hints.
  * `build_routing`, `run_router` from `pipeline`: New routing functions replacing the DAG approach.

```python
def read_lines(path: str) -> Iterator[str]:
    """Read lines from a file, stripping newlines."""
    with open(path, "r") as file:
        for line in file:
            yield line.rstrip("\n")
```

* **`read_lines` function**:

  * Reads lines from a file one by one.
  * Removes trailing newline characters.

```python
def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
    """Write lines to a file or print to console if output_file is None."""
    if output_file is None:
        for line in lines:
            print(line)
    else:
        output_file = os.path.abspath(os.path.expanduser(output_file))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as file:
            for line in lines:
                file.write(line + "\n")
```

* **`write_output` function**:

  * Writes processed lines to a file if `output_file` is provided.
  * Prints lines to console if no output file is given.
  * Ensures directories exist before writing.

```python
def run(input_path: str, config_path: str, output_path: Optional[str]) -> None:
    """Run the tag-based routing engine on input lines."""
    lines = read_lines(input_path)
    nodes = build_routing(config_path)

    import yaml
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    start_tag = cfg.get("start", "start")

    output_lines = run_router(start_tag, lines, nodes)
    write_output(output_lines, output_path)
```

* **`run` function**:

  * Reads input lines using `read_lines`.
  * Builds a routing map using `build_routing(config_path)`.
  * Loads YAML configuration to get the `start` tag (default is `'start'`).
  * Passes lines, start tag, and nodes to `run_router` for processing.
  * Writes or prints output via `write_output`.

**Summary:**

* `main.py` now orchestrates a tag-based routing system instead of a node-based DAG.
* It serves as the entry point to process input files according to routing rules defined in the YAML configuration.

---
---

## 📄 `pipeline.py` Explanation

```python
import yaml
import importlib
from typing import Any, Iterator, Tuple, List, Dict
from typez import ProcessorFn
```

* **Imports**:

  * `yaml`: Parse YAML configuration files.
  * `importlib`: Dynamically import modules and functions.
  * `Any`, `Iterator`, `Dict` from `typing`: For type hints.
  * `ProcessorFn` from `typez`: Type alias for processor functions.

```python
class ProcessorNode:
    """
    Represents a processor state. Processes lines and emits (tag, line) pairs.
    """
    def __init__(self, tag: str, processor: ProcessorFn):
        self.tag = tag
        self.processor = processor
```

* **`ProcessorNode` class**:

  * Holds a `tag` and a `processor` callable.
  * Acts as a wrapper for routing operations.

```python
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
```

* **`load_function`**:

  * Dynamically loads a function or class by import path (e.g., `core.trim`).
  * If it’s a class, instantiates it.
  * Ensures the object is callable.

```python
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
```

* **`build_routing`**:

  * Reads YAML configuration.
  * Creates `ProcessorNode` objects for each node, keyed by their `tag`.
  * Returns a mapping: `tag -> ProcessorNode`.

```python
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
```

* **`run_router` function**:

  * Uses a queue (`deque`) to manage lines with tags.
  * Processes each line through the node corresponding to its current tag.
  * Lines tagged `'end'` are yielded directly.
  * Allows multiple output tags for fan-out processing.
  * Continues routing until all lines reach `'end'`.

**Summary:**

* `pipeline.py` replaces the old DAG system with a flexible tag-based router.
* Each processor can emit lines with one or more tags, and routing continues dynamically.
* This structure supports fan-out and flexible processing pipelines, simplifying routing logic.


---
---

## 📄 `typez.py` Explanation

```python
from typing import Iterator, Tuple, List, Callable
```

* **Imports**:

  * `Iterator`, `Tuple`, `List`, `Callable` from `typing` for type annotations.

```python
# Each processor takes an iterator of lines and yields (tags, line) pairs
ProcessorFn = Callable[[Iterator[str]], Iterator[Tuple[List[str], str]]]
```

* **`ProcessorFn` type alias**:

  * Represents a processor function or callable object.
  * Accepts an iterator of strings as input.
  * Returns an iterator of `(tags, line)` tuples, where:

    * `tags` is a list of strings used for routing.
    * `line` is the processed text string.

**Summary:**

* `typez.py` defines the standard processor type for the project.
* Ensures consistent typing and facilitates dynamic routing with tags.


---
---

## 📄 `processors/base.py` Explanation

```python
from typing import Iterator, Callable, Tuple, List

ProcessorFn = Callable[[Iterator[str]], Iterator[Tuple[List[str], str]]]
```

* **Imports**:

  * `Iterator`, `Tuple`, `List`, `Callable` from `typing` for type annotations.
* **ProcessorFn type alias** ensures consistent processor signatures.

```python
def streamify(fn: Callable[[str], str], tag: str = "default") -> ProcessorFn:
    def wrapper(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield [tag], fn(line)
    return wrapper
```

* **`streamify` function**:

  * Converts a standard string function (`fn`) into a processor.
  * Wraps each line in a tuple `(tags, processed_line)`.
  * `tag` argument determines the emitted tag for routing.

```python
class LineCounter:
    def __init__(self, tag: str = "default"):
        self.count = 0
        self.tag = tag

    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            self.count += 1
            yield [self.tag], f"{self.count}: {line}"
```

* **`LineCounter` class**:

  * Callable processor that numbers each input line.
  * Maintains internal count across calls.
  * Emits `(tags, line)` tuples with `tag` for routing.

**Summary:**

* `processors/base.py` provides utilities for building processors.
* `streamify` allows wrapping simple functions as processors.
* `LineCounter` is a stateful processor that counts lines, demonstrating a persistent internal state in a processor.

---
---

## 📄 `processors/tagger.py` Explanation

```python
from typing import Iterator, Tuple, List
from typez import ProcessorFn
```

* **Imports**:

  * `Iterator`, `Tuple`, `List` from `typing` for type hints.
  * `ProcessorFn` from `typez` for consistent processor typing.

```python
class Tagger:
    """
    Tags lines containing 'ERROR' with ['error'].
    Other lines are tagged ['general'] for further processing.
    """
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "ERROR" in line:
                yield (["error"], line)
            elif "WARN" in line:
                yield (["warn"], line)
            else:
                yield (["general"], line)
```

* **`Tagger` class**:

  * Callable processor that tags lines based on content.
  * Lines with `ERROR` → tag `['error']`
  * Lines with `WARN` → tag `['warn']`
  * All other lines → tag `['general']`
  * Enables the routing engine to send lines to different processors depending on tags.

**Summary:**

* `processors/tagger.py` consolidates error and warning tagging into a single processor.
* Provides clear tagging logic for the tag-based routing system.

---
---

## 📄 `processors/output.py` Explanation

```python
from typing import Iterator, Tuple, List
from typez import ProcessorFn
```

* **Imports**:

  * `Iterator`, `Tuple`, `List` from `typing` for type hints.
  * `ProcessorFn` from `typez` for consistent processor typing.

```python
class terminal:
    """Terminal processor that emits 'end' for all lines."""
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield (["end"], line)
```

* **`terminal` class**:

  * Callable processor for final output.
  * Every line processed is emitted with the tag `['end']`.
  * Integrates with the routing engine to signal processing completion.

**Summary:**

* `processors/output.py` defines the final step in the tag-based routing pipeline.
* Ensures all lines reach the `'end'` tag for output, either to file or console.

