# Libraries and built-ins

No external Python dependencies. Everything is the standard library.

| Module / built-in | Where | What for | Why this, not an alternative |
| --- | --- | --- | --- |
| `json` | `plugin_audit.read_json`, tests | parse manifests, write test fixtures | standard; `jsonschema` would validate shape, but `claude plugin validate` already does that |
| `dataclasses.dataclass` | `Finding` | an immutable record with named fields | lighter than a class with `__init__`; clearer than a tuple |
| `pathlib.Path` | everywhere | joins, `resolve`, `is_relative_to`, `rglob`, `glob` | object paths beat `os.path` string juggling |
| `urllib.parse.urlparse` | `url_finding` | read the host from an MCP URL | correct parsing beats a regex |
| `subprocess` | `main.run` | run the check tools | list arguments, no shell |
| `shutil.which` | `main.check` | skip tools that aren't installed | standard and cross-platform |
| `sys` | `main.py`, tests | argv, exit code, `sys.executable`, `sys.path` | — |
| `unittest` | tests | test runner | standard; same as the other side projects |
| `tempfile` | tests | throwaway plugin folders | cleaned up automatically |
| `isinstance`, `sorted`, `sum`, `map`, `str.join` | core | shape checks, ordering, counting | built-ins |
| `__name__ == "__main__"` | `main.py` | run only when executed, not on import | standard idiom |
| `__file__` | `main.py`, tests | find the repo root | — |

**Tools used by the gate (not imported):** `ruff`, `claude plugin validate`,
`devtools` (from [mr-factory-workspace](https://github.com/jericho3110/mr-factory-workspace/tree/main/packages/devtools)).

## References

### Official

- [The Python Standard Library](https://docs.python.org/3/library/index.html)
- [`__main__`](https://docs.python.org/3/library/__main__.html)

### Further learning

- [Python Module of the Week](https://pymotw.com/3/)
