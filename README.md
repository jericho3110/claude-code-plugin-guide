# Claude Code Plugin Guide

How "downloading a plugin" for [Claude Code](https://code.claude.com/docs/en/overview)
actually works: marketplaces, manifests, what lands on your disk, what can run
code, and how to check a plugin **before** you trust it. It includes a small
read-only auditor and a valid example plugin.

> Unofficial learning notes, checked against the official docs and Claude
> Code 2.1.268 (October 2026). Not affiliated with Anthropic.

## Contents
- [Quick start](#quick-start)
- [Layout](#layout)
- [Checks](#checks)
- [Documentation](#documentation)
- [References](#references)

## Quick start

```bash
python main.py audit ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>   # what in it runs code?
python main.py check                                                           # tests + validate + security + links
```

Real output for the `ponytail` plugin (shortened):

```text
Plugin: ponytail
  [runs-code] hook  hooks/claude-codex-hooks.json: SessionStart [startup|resume|clear|compact] command: node -e "..."
  [runs-code] hook  hooks/claude-codex-hooks.json: SubagentStart [*] command: node -e "..."
  [runs-code] hook  hooks/claude-codex-hooks.json: UserPromptSubmit [*] command: node -e "..."
  [info     ] skill skills/: instructions for Claude: ponytail, ponytail-audit, ...
3 thing(s) that run code, 0 warning(s). Read each one before installing.
```

Python 3.10+ only; no packages to install.

## Layout

```text
main.py                  front door: audit | check
plugin_audit.py          the read-only auditor (never runs plugin code)
tests/                   6 unittest tests with fake plugins
examples/marketplace/    a valid one-plugin marketplace: study-notes (one skill)
docs/                    the guide
```

## Checks

`python main.py check` runs: unittest, `ruff check`, `claude plugin validate --strict`
on the example marketplace and plugin, `devtools scan` (secrets, personal data,
dangerous patterns) and `devtools links --offline`. Tools that aren't
installed are skipped with a note.

## Documentation

| Doc | What's in it |
| --- | --- |
| [docs/HOW_PLUGINS_WORK.md](docs/HOW_PLUGINS_WORK.md) | **start here**: marketplaces, plugins, components, files on disk, scopes, every command, updates, token cost |
| [docs/INSTALL_PROCESS.md](docs/INSTALL_PROCESS.md) | **the install process in theory and practice**: one real install followed step by step (catalog → resolve → version → cache → record → load → run → update), with the computer-science concept behind each step |
| [docs/CONTEXT_MEMORY_CACHE.md](docs/CONTEXT_MEMORY_CACHE.md) | **context window vs memory vs prompt cache**: what each is, how memory is loaded, cache prices and lifetime, one turn end to end, Python analogies |
| [docs/CASE_STUDIES.md](docs/CASE_STUDIES.md) | two real installs: ponytail (a plugin with hooks) and graphify (a skill with its own installer) |
| [docs/SECURITY.md](docs/SECURITY.md) | threat model, checklist before installing, every RCE path, the auditor's defenses |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | how the auditor is built and why |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | every Python feature the code uses, with gotchas and exercises |
| [docs/LEARNING_PATH.md](docs/LEARNING_PATH.md) | a reading order in six stages |
| [docs/LIBRARIES_AND_BUILTINS.md](docs/LIBRARIES_AND_BUILTINS.md) | each module and built-in, and why |
| [docs/CONVENTIONS.md](docs/CONVENTIONS.md), [docs/GLOSSARY.md](docs/GLOSSARY.md), [docs/FILE_TYPES.md](docs/FILE_TYPES.md) | rules, terms, file types |
| [CHANGELOG.md](CHANGELOG.md) | versions |

## References

### Official

- [Claude Code: plugins](https://code.claude.com/docs/en/plugins), [Install and manage plugins](https://code.claude.com/docs/en/discover-plugins), [Plugin security](https://code.claude.com/docs/en/plugins/security)

### Further learning

- [Anthropic's official plugin marketplace](https://github.com/anthropics/claude-plugins-official)

## License

[MIT](LICENSE)
