# dataflow-framework

A lightweight CLI utility for transforming text files with different processing modes (e.g., **uppercase**, **snake\_case**). Built with [Typer](https://typer.tiangolo.com/) for simple CLI interactions and designed to be easily extensible with custom processors.

---

## 🚀 Installation

Once published, you can install directly from PyPI:

```bash
pip install dataflow-framework
```

Or install locally (from the repo):

```bash
pip install .
```

---

## 📌 Usage

Transform a text file by specifying the input file, processing mode, and optionally an output file.

```bash
python -m dataflow_framework.cli input.txt --mode uppercase --output output.txt
```

### Examples

Convert to uppercase:

```bash
python -m dataflow_framework.cli input.txt --mode uppercase
```

Convert to snake\_case:

```bash
python -m dataflow_framework.cli input.txt --mode snakecase --output result.txt
```

If no `--output` is provided, results are printed to the console.

---

## ⚙️ Configuration with `.env`

You can define a default mode in a `.env` file:

```env
DEFAULT_MODE=uppercase
```

This way, you can omit `--mode` when running the command.

---

## 🛠️ Extending the Framework

You can easily add new processors:

1. Define a processor in `core.py`:

   ```python
   def to_titlecase(line: str) -> str:
       return line.title()
   ```

2. Add it to the pipeline in `pipeline.py`:

   ```python
   elif mode == "titlecase":
       return [to_titlecase]
   ```

Now you can run:

```bash
python -m dataflow_framework.cli input.txt --mode titlecase
```

---

## ✅ Requirements

* Python 3.13+
* [typer](https://pypi.org/project/typer/)
* [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## 📖 Roadmap

* [ ] Add more built-in processors (e.g., kebab-case, Title Case)
* [ ] Support for streaming large files
* [ ] Option to chain multiple processors

---

## 🧾 Example Workflow

```bash
# Input: input.txt
Hello World
Python Rocks

# Run transformation
python -m dataflow_framework.cli input.txt --mode snakecase --output output.txt

# Output: output.txt
hello_world
python_rocks
```
