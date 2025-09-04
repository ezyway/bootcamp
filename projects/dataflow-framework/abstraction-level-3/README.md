# dataflow-framework

A lightweight, **config-driven** CLI utility for transforming text files. Instead of hardcoding modes, users now define their desired processing pipeline in a YAML configuration file. Built with [Typer](https://typer.tiangolo.com/) for simple CLI interactions and designed for extensibility with custom processors.

---

## 🚀 Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv pip install -e .
```

Or install with pip:

```bash
pip install .
```

---

## 📌 Usage

Transform a text file by specifying the input file, a pipeline configuration file, and optionally an output file.

```bash
uv run cli.py input.txt --config pipeline.yaml --output output.txt
```

### Example

Given the following `pipeline.yaml`:

```yaml
pipeline:
  - type: processors.snake.to_snakecase
  - type: processors.upper.to_uppercase
```

Run:

```bash
uv run cli.py input.txt --config pipeline.yaml
```

This will first convert lines to `snake_case`, then transform them to `UPPERCASE`.

If no `--output` is provided, results are printed to the console.

---

## ⚙️ Default Config

If you don’t provide `--config`, the tool will use a default `pipeline.yaml` in the project root.

```bash
uv run cli.py input.txt
```

---

## 🛠️ Extending the Framework

You can add your own processors without touching the core code:

1. Create a new file in the `processors/` directory, e.g. `title.py`:

   ```python
   def to_titlecase(line: str) -> str:
       return line.title()
   ```

2. Update your `pipeline.yaml`:

   ```yaml
   pipeline:
     - type: processors.title.to_titlecase
   ```

3. Run:

   ```bash
   uv run cli.py input.txt --config pipeline.yaml
   ```

Now your custom processor is part of the pipeline!

---

## ✅ Requirements

* Python 3.13+
* [typer](https://pypi.org/project/typer/)
* [python-dotenv](https://pypi.org/project/python-dotenv/)
* [pyyaml](https://pypi.org/project/PyYAML/)

---

## 📖 Roadmap

* [ ] Add more built-in processors (e.g., kebab-case, Title Case)
* [ ] Validation & logging for configs
* [ ] Support for streaming & fan-out pipelines

---

## 🧾 Example Workflow

```bash
# Input: input.txt
Hello World
Python Rocks

# Run transformation with pipeline.yaml (snake → upper)
uv run cli.py input.txt --config pipeline.yaml --output output.txt

# Output: output.txt
HELLO_WORLD
PYTHON_ROCKS
```
