# Architecture

This repo is mostly documentation, plus one small tool and one example.

## Layout

```text
Claude_Code_Plugin_Guide/
├── main.py                 front door: `audit <dir>` | `check`  (imperative shell)
├── plugin_audit.py         pure-ish core: read files → list of Finding
├── tests/                  unittest, builds fake plugins in temp folders
├── examples/marketplace/   a valid one-plugin marketplace (study-notes)
└── docs/                   the guide
```

## How `python main.py audit <dir>` flows

```text
main.main(["audit", dir])
  └─ plugin_audit.report(dir)
       └─ audit(dir)
            ├─ read .claude-plugin/plugin.json      (size-limited, may be absent)
            ├─ flag manifest paths that escape root (never read them)
            ├─ hooks:   hooks/hooks.json + manifest "hooks" (files or inline)
            ├─ servers: .mcp.json / .lsp.json + manifest mcpServers / lspServers
            ├─ monitors, bin/, symlinks           (one walk, capped)
            └─ skills / agents / commands         (names only)
       → sorted text: runs-code first, then warnings, then info
```

## Design choices

| Choice | Alternatives | Why |
| --- | --- | --- |
| **functional core, imperative shell**: `audit()` returns data, `main.py` prints | print while scanning | the core is testable without capturing output |
| `@dataclass(frozen=True)` `Finding` | dicts, tuples | named fields, immutable, readable in tests |
| standard library only | `jsonschema`, `pydantic` | no dependency to vet; we list things, not validate them (`claude plugin validate` does that) |
| `unittest` | pytest | in the standard library; matches the other side projects |
| tools in `check` are skipped if absent | fail when missing | the tests still run on a machine without `claude` or `devtools` |
| one example plugin, skill-only | a full plugin with hooks | an example that runs no code is safe to copy and install |

## Principles used

- **YAGNI**: no plugin installer, no scoring of "how dangerous"; just the list a human needs.
- **Fail closed on hostile input**: anything unreadable becomes a warning, never silently skipped.
- **Single responsibility**: `hook_findings`, `server_findings` and `url_finding` each handle one kind of thing.

## Known limits

See [SECURITY.md §6](SECURITY.md#6-accepted-risks).

## References

### Official

- Python: [dataclasses](https://docs.python.org/3/library/dataclasses.html), [pathlib](https://docs.python.org/3/library/pathlib.html), [unittest](https://docs.python.org/3/library/unittest.html)

### Other

- Gary Bernhardt, [Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)
- Martin Fowler, [Yagni](https://martinfowler.com/bliki/Yagni.html)

### Further learning

- [Exercism Python track](https://exercism.org/tracks/python)
