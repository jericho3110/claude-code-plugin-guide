# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions: [SemVer](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-10

### Added
- `docs/INSTALL_PROCESS.md`: the install process in theory and practice, following the real ponytail install through catalog, resolution, versioning, cache, records, loading, events and updates, naming the concept behind each step, and comparing with pip, npm and VS Code.

### Fixed
- HOW_PLUGINS_WORK §5 left out that `marketplace add` also writes `extraKnownMarketplaces` to settings.

## [0.1.0] - 2026-10-10

### Added
- Guide: how plugins work (marketplaces, manifests, components, disk layout, scopes, commands, updates, token cost), case studies (ponytail, graphify) and security (threat model, checklist, RCE paths).
- `plugin_audit.py` + `python main.py audit <dir>`: a read-only list of everything in a plugin that runs code. 6 tests.
- `examples/marketplace`: a one-plugin marketplace (`study-notes`, one skill) that passes `claude plugin validate --strict`.
- `python main.py check`: tests, ruff, validate, devtools scan and links.

### Found live
- `/plugin` doesn't work in the VS Code chat box; VS Code's command is `/plugins`, and `claude plugin ...` works in any shell.
- graphify isn't a Claude Code plugin: it's a skill plus a CLI with its own installer, so `claude plugin list` doesn't show it.
