# Learning path

| Stage | Read | Concepts | Exercise | Self-check |
| --- | --- | --- | --- | --- |
| 1 | [HOW_PLUGINS_WORK.md](HOW_PLUGINS_WORK.md) §1–3 | marketplace vs plugin, manifest, namespacing | run `claude plugin marketplace list` and explain each source | what's the difference between `ponytail` and `ponytail@ponytail`? |
| 2 | §4–6 | components, what runs code, files on disk, scopes | find your `installed_plugins.json` and read one entry | which scope wins when user and project disagree? |
| 3 | §7–10 | the CLI, updates, token cost | `claude plugin details` on each plugin you have | why does an unused plugin still cost tokens? |
| 4 | [CASE_STUDIES.md](CASE_STUDIES.md) | plugin vs skill vs CLAUDE.md, hooks in practice | find where graphify's skill lives | why do graphify's commands go through permission rules but ponytail's hooks don't? |
| 5 | [SECURITY.md](SECURITY.md), `plugin_audit.py`, [CONCEPTS.md](CONCEPTS.md) | threat model, RCE paths, hostile input | `python main.py audit` on a plugin from the official marketplace folder | why is `is_relative_to` safer than `startswith`? |
| 6 | `examples/marketplace/`, HOW_PLUGINS_WORK §12 | building and validating your own | add a second skill, validate, install, remove | what does `validate --strict` catch that the runtime tolerates? |

## References

### Official

- [Claude Code plugins documentation](https://code.claude.com/docs/en/plugins)

### Further learning

- [Anthropic's official plugin marketplace](https://github.com/anthropics/claude-plugins-official): read real plugins
