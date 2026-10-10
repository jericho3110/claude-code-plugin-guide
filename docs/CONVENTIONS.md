# Conventions

| Topic | Rule |
| --- | --- |
| Code | Python 3.10+, standard library only, `ruff check` clean |
| Names | `snake_case` functions, `CapWords` classes, `UPPER_CASE` limits (`MAX_JSON_BYTES`) |
| Plugin names | kebab-case; never start with `claude-` or `anthropic-` (reserved; `validate` rejects them) |
| Examples | must pass `claude plugin validate --strict`; no hooks, servers or `bin/` (safe to copy) |
| Data in docs | no real user paths, IDs or IPs: use `~`, made-up names, RFC 5737 addresses (`203.0.113.10`) |
| Docs | every claim checked against the docs or real output; each doc ends with References and Further learning |
| Commits | imperative summary ≤ 72 chars, a body saying why, how it was verified; made with [gitship](https://github.com/jericho3110/mr-factory-workspace/tree/main/packages/gitship), which runs `python main.py check` first |
| Versions | SemVer, recorded in [CHANGELOG.md](../CHANGELOG.md) |

## References

### Official

- [PEP 8](https://peps.python.org/pep-0008/), [Ruff](https://docs.astral.sh/ruff/), [RFC 5737](https://www.rfc-editor.org/rfc/rfc5737), [Semantic Versioning](https://semver.org/)

### Further learning

- [How to Write a Git Commit Message](https://cbea.ms/git-commit/)
