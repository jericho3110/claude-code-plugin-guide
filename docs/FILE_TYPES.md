# File types

| File | Why it exists |
| --- | --- |
| `*.py` | the auditor, the front door and the tests |
| `*.md` | the docs; `SKILL.md` is also a skill (Markdown with a YAML header between `---` lines) |
| `.claude-plugin/marketplace.json` | the example catalog: name, owner, plugin entries |
| `.claude-plugin/plugin.json` | the example plugin's manifest |
| `.gitignore` | keeps caches, virtual environments and `graphify-out/` out of git |
| `.gitattributes` | normalizes line endings so diffs don't show every line as changed on Windows |
| `.gitship.json` | tells [gitship](https://github.com/jericho3110/mr-factory-workspace/tree/main/packages/gitship) which check to run before committing |
| `LICENSE` | MIT: anyone may reuse this, with the notice |
| `CHANGELOG.md` | what changed in each version |

Files a plugin install creates on *your* machine (not in this repo) are
listed in [HOW_PLUGINS_WORK.md §5](HOW_PLUGINS_WORK.md#5-installing-what-happens-on-disk).

## References

### Official

- [YAML front matter in skills](https://code.claude.com/docs/en/skills), [gitattributes](https://git-scm.com/docs/gitattributes), [gitignore](https://git-scm.com/docs/gitignore)

### Further learning

- [choosealicense.com](https://choosealicense.com/)
