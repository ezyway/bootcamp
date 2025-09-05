## 📄 `cli.py` Explanation

```python
import typer
from typing_extensions import Annotated
from dotenv import load_dotenv

from main import run
```

* **Imports**:

  * `typer`: A library to build CLI applications easily.
  * `Annotated` from `typing_extensions`: Used to provide extra metadata for function arguments (like help text).
  * `load_dotenv`: Loads environment variables from a `.env` file.
  * `run` from `main`: The main function to execute the DAG pipeline.

```python
load_dotenv()
app = typer.Typer(help="Run a DAG-based line processing pipeline.")
```

* `load_dotenv()` loads environment variables so your pipeline can use them if needed.
* `app = typer.Typer(...)` initializes the CLI application with a description.

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

  * `input`: Required positional argument, the path to input text file.
  * `config`: Optional YAML config file path (defaults to `pipeline.yaml`).
  * `output`: Optional output file; if not provided, prints to console.
* Calls the `run` function to process the input through the DAG.

```python
if __name__ == "__main__":
    app()
```

* Standard Python entry point. If the file is run directly, it starts the Typer CLI.

**Summary:** `cli.py` is the entry point for the command-line interface. It reads input and config paths, optionally an output path, and runs the DAG-based processing pipeline.

---
---

## 📄 `core.py` Explanation

```python
from typing import Iterator, Tuple, List
from typez import ProcessorFn
```

* **Imports**:

  * `Iterator`, `Tuple`, `List` from `typing`: Used for type hints.
  * `ProcessorFn` from `typez`: This is a callable type alias for processors, which take an iterator of strings and return an iterator of `(tags, line)` tuples.

```python
def to_uppercase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    for line in lines:
        yield (["uppercase"], line.upper())
```

* **`to_uppercase` function**:

  * Takes an iterator of strings.
  * Converts each line to uppercase.
  * Yields a tuple: tags `['uppercase']` and the uppercase line.

```python
def to_snakecase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    for line in lines:
        yield (["snake"], line.replace(" ", "_").lower())
```

* **`to_snakecase` function**:

  * Replaces spaces with underscores and converts text to lowercase.
  * Tags the line as `['snake']`.

```python
def trim(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    for line in lines:
        yield (["trimmed"], line.strip())
```

* **`trim` function**:

  * Removes leading and trailing whitespace.
  * Tags the line as `['trimmed']`.

**Summary:**

* `core.py` provides basic line processing functions.
* Each function returns `(tags, processed_line)` tuples, which can be routed in the DAG pipeline based on tags.

---

---

## 📄 `main.py` Explanation

```python
import os
from typing import Iterator, Optional
from pipeline import build_dag, run_dag
```

* **Imports**:

  * `os`: For file path operations.
  * `Iterator`, `Optional`: Type hints.
  * `build_dag` and `run_dag` from `pipeline`: Used to build the DAG from config and execute it.

```python
def read_lines(path: str) -> Iterator[str]:
    with open(path, "r") as file:
        for line in file:
            yield line.rstrip("\n")
```

* **`read_lines` function**:

  * Reads lines from a text file.
  * Strips the newline character.
  * Yields one line at a time.

```python
def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
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

  * Writes processed lines to a file or prints to console if `output_file` is `None`.
  * Ensures directories exist using `os.makedirs`.

```python
def run(input_path: str, config_path: str, output_path: Optional[str]) -> None:
    lines = read_lines(input_path)
    nodes = build_dag(config_path)

    import yaml
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    start_node_name = cfg.get("start") or list(nodes.keys())[0]
    start_node = nodes[start_node_name]
    
    output_lines = run_dag(start_node, lines)
    write_output(output_lines, output_path)
```

* **`run` function**:

  * Reads input lines using `read_lines`.
  * Builds the DAG nodes using `build_dag`.
  * Reads the YAML config to determine the starting node (`start` field or first node by default).
  * Runs the DAG with `run_dag`.
  * Writes or prints output using `write_output`.

**Summary:**

* `main.py` orchestrates reading the input file, building and running the DAG, and writing the output.
* It’s the core glue that connects the CLI, pipeline, and processors.

---

---

## 📄 `typez.py` Explanation

```python
from typing import Iterator, Tuple, List, Callable

ProcessorFn = Callable[[Iterator[str]], Iterator[Tuple[List[str], str]]]
```

* **Imports**:

  * `Iterator`, `Tuple`, `List`, `Callable` from `typing` for type annotations.

* **`ProcessorFn` type alias**:

  * Represents any processor function or callable object.
  * Takes an iterator of strings as input.
  * Returns an iterator of `(tags, line)` tuples:

    * `tags` is a list of strings (used for routing in the DAG).
    * `line` is the processed line string.

**Summary:**

* `typez.py` defines the standard type for all processors in the pipeline.
* It ensures consistency and type safety across the project.

---

---

## 📄 `processors/taggers.py` Explanation

```python
from typing import Iterator, Tuple, List
from typez import ProcessorFn
```

* **Imports**:

  * `Iterator`, `Tuple`, `List` from `typing` for type hints.
  * `ProcessorFn` from `typez` for consistent processor typing.

```python
class TagError:
    """
    Tags lines containing the word 'ERROR' with ['error'].
    Otherwise tags with ['general'].
    """
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "ERROR" in line:
                yield (["error"], line)
            else:
                yield (["general"], line)
```

* **`TagError` class**:

  * Callable class (implements `__call__`).
  * Tags lines containing "ERROR" with `['error']`.
  * All other lines get `['general']`.
  * Allows the DAG to route error lines differently.

```python
class TagWarn:
    """
    Tags lines containing the word 'WARN' with ['warn'].
    Otherwise tags with ['general'].
    """
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "WARN" in line:
                yield (["warn"], line)
            else:
                yield (["general"], line)
```

* **`TagWarn` class**:

  * Callable class.
  * Tags lines containing "WARN" with `['warn']`.
  * All other lines get `['general']`.

**Summary:**

* `processors/taggers.py` defines processors that tag lines for routing in the DAG.
* These taggers allow different handling of errors, warnings, or general lines.
* They integrate seamlessly with the DAG pipeline logic.

---

---

## 📄 `pipeline.yaml` Explanation

```yaml
start: trim
nodes:
  - name: trim
    type: core.trim
    routes:
      trimmed: classify
```

* **Start Node:** `trim`.
* **Node `trim`**:

  * Processor: `core.trim` (removes whitespace, tags with `['trimmed']`).
  * Routes `trimmed` lines to `classify` node.

```yaml
  - name: classify
    type: processors.taggers.TagError
    routes:
      error: handle_error
      general: check_warn
```

* **Node `classify`**:

  * Processor: `TagError`.
  * Lines tagged `error` go to `handle_error`.
  * Lines tagged `general` go to `check_warn`.

```yaml
  - name: check_warn
    type: processors.taggers.TagWarn
    routes:
      warn: handle_warning
      general: handle_general
```

* **Node `check_warn`**:

  * Processor: `TagWarn`.
  * Lines tagged `warn` go to `handle_warning`.
  * Lines tagged `general` go to `handle_general`.

```yaml
  - name: handle_error
    type: core.to_uppercase
    routes: {}

  - name: handle_warning
    type: core.to_snakecase
    routes: {}

  - name: handle_general
    type: core.to_uppercase
    routes: {}
```

* **End Nodes:**

  * `handle_error`: Converts to uppercase.
  * `handle_warning`: Converts to snake\_case.
  * `handle_general`: Converts to uppercase.
* These nodes have no further routes (`routes: {}`), so processed lines are output.

**Summary:**

* `pipeline.yaml` defines the DAG structure.
* Each node has a processor and routing rules based on tags.
* Tags control which node a line goes to next.
* The DAG flows from `trim` → `classify` → `check_warn` → respective handlers.

---

---

## 📄 `sample_input.txt`

```text
  Hello World  
This is a WARN level log
Everything looks fine
ERROR: Something went wrong
Another line
 WARN: Disk space low
```

* This is a simple text file with several lines.
* Some lines contain `WARN` or `ERROR` keywords.
* Some lines have leading/trailing spaces.

---

## 📄 Expected Output

```text
HELLO WORLD
this_is_a_warn_level_log
EVERYTHING LOOKS FINE
ERROR: SOMETHING WENT WRONG
ANOTHER LINE
warn:_disk_space_low
```

* **Processing Steps:**

  1. Lines are trimmed of spaces.
  2. Lines with `ERROR` are converted to uppercase.
  3. Lines with `WARN` are converted to snake\_case.
  4. Other lines are converted to uppercase.
* This matches the routing logic defined in `pipeline.yaml`.

**Summary:**

* The sample input demonstrates different cases: general lines, warnings, and errors.
* The output shows how the DAG pipeline correctly processes lines according to tags and routing rules.

---
