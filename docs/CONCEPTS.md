# Concepts (Python, in this repo's code)

Every Python feature `plugin_audit.py`, `main.py` and the tests use, with
where it appears, a small example and the gotcha.

| Concept | Where | Example | Gotcha |
| --- | --- | --- | --- |
| **dataclass** | `Finding` | `@dataclass(frozen=True) class Finding: level: str` | `frozen=True` makes instances immutable *and* hashable; assigning a field raises `FrozenInstanceError` |
| **type hints** | everywhere | `def inside(root: Path, rel: str) -> Path \| None` | hints aren't checked at run time; `X \| None` needs Python 3.10+ |
| **pathlib** | `inside`, `audit` | `(root / rel).resolve()` | `/` joins paths; `resolve()` follows symlinks and `..`, which is exactly what a containment check needs |
| **`is_relative_to`** | `inside` | `target.is_relative_to(root)` | compares path parts, not strings; `startswith("C:/a")` would wrongly accept `C:/ab` |
| **`isinstance` guards** | `hook_findings`, `server_findings` | `if not isinstance(hooks, dict): ...` | JSON from strangers can be any shape; check before calling `.get` or `.items()` |
| **conditional expression in a loop** | `hook_findings` | `for g in groups if isinstance(groups, list) else []` | readable once you see it; don't nest two of them |
| **exceptions as data** | `audit` | `except (ValueError, OSError) as e: out.append(Finding("warning", ...))` | catch the specific errors you expect; a bare `except:` would hide bugs |
| **`json.loads` with `utf-8-sig`** | `read_json` | `path.read_text(encoding="utf-8-sig")` | strips a BOM some Windows editors add; plain `utf-8` would fail to parse it |
| **generator expression** | `report` | `sum(f.level == "runs-code" for f in findings)` | `True` counts as 1 because `bool` is a subclass of `int` |
| **`sorted` with a key** | `report` | `sorted(findings, key=lambda f: (order[f.level], f.kind))` | a tuple key sorts by the first item, then the second |
| **nested function (closure)** | `rel()` inside `audit` | uses `root` from the outer function | the closure captures the variable, not its value at definition time |
| **`subprocess.run` with a list** | `main.run` | `subprocess.run(["ruff", "check", "."])` | a list means no shell, so no injection; `shell=True` with a string would be risky |
| **`shutil.which`** | `main.check` | `shutil.which("claude")` | returns `None` when the tool isn't on `PATH` |
| **`sys.exit(main(...))`** | `main.py` | the return value becomes the exit code | the gate and gitship depend on that code |
| **`tempfile.TemporaryDirectory`** | tests | `setUp` creates it, `tearDown` cleans up | always clean up in `tearDown`, even when a test fails |
| **`sys.path.insert`** | tests | lets tests import `plugin_audit` from the repo root | fine for a flat project; a package would use an install instead |

## Exercises

1. Make `audit()` also list `output-styles/*.md`. Add a test.
2. Change `inside()` to use `str(target).startswith(str(root))`. Write a test that proves it's now wrong (hint: a sibling folder whose name starts with the plugin's name).
3. Add a `--json` option to `main.py audit` that prints the findings with `dataclasses.asdict`.

**Self-check:** why does `audit()` return a list instead of printing?

## References

### Official

- [dataclasses](https://docs.python.org/3/library/dataclasses.html) ✔ (`frozen`), [pathlib](https://docs.python.org/3/library/pathlib.html) ✔ (`is_relative_to`, `resolve`), [json](https://docs.python.org/3/library/json.html), [codecs: utf-8-sig](https://docs.python.org/3/library/codecs.html#module-encodings.utf_8_sig) ✔, [subprocess](https://docs.python.org/3/library/subprocess.html), [shutil.which](https://docs.python.org/3/library/shutil.html#shutil.which), [unittest](https://docs.python.org/3/library/unittest.html), [tempfile](https://docs.python.org/3/library/tempfile.html)
- [PEP 604: `X | Y` union types](https://peps.python.org/pep-0604/)

### Other

- Real Python: [Data classes](https://realpython.com/python-data-classes/), [pathlib](https://realpython.com/python-pathlib/)

### Further learning

- [Exercism Python track](https://exercism.org/tracks/python)
