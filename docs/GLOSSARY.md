# Glossary

| Term | Meaning | Explained in |
| --- | --- | --- |
| marketplace | a catalog (`marketplace.json`) listing plugins and where to fetch each | [HOW §2](HOW_PLUGINS_WORK.md#2-marketplaces-the-catalog) |
| plugin | a folder of skills, agents, hooks and servers, installed as one unit | [HOW §3](HOW_PLUGINS_WORK.md#3-plugins-the-package) |
| manifest | `.claude-plugin/plugin.json`: the plugin's name, version and component paths | [HOW §3](HOW_PLUGINS_WORK.md#3-plugins-the-package) |
| `plugin@marketplace` | the install id: plugin name, then the catalog it comes from | [HOW §7](HOW_PLUGINS_WORK.md#7-every-command-explained) |
| skill | a `SKILL.md` with instructions Claude loads when relevant | [HOW §4](HOW_PLUGINS_WORK.md#4-what-a-plugin-can-contain) |
| hook | a command run automatically at a lifecycle event | [HOW §4](HOW_PLUGINS_WORK.md#4-what-a-plugin-can-contain), [SECURITY §3](SECURITY.md#3-rce-every-way-code-can-run) |
| MCP server | a program or URL that gives Claude extra tools (Model Context Protocol) | [HOW §4](HOW_PLUGINS_WORK.md#4-what-a-plugin-can-contain) |
| LSP server | a language server: code intelligence (Language Server Protocol) | [HOW §4](HOW_PLUGINS_WORK.md#4-what-a-plugin-can-contain) |
| monitor | a background command started with the session | [SECURITY §3](SECURITY.md#3-rce-every-way-code-can-run) |
| scope | who gets a plugin: user, project, local or managed | [HOW §6](HOW_PLUGINS_WORK.md#6-scopes-who-gets-the-plugin) |
| `${CLAUDE_PLUGIN_ROOT}` | the installed plugin's folder, for finding its own files | [HOW §4](HOW_PLUGINS_WORK.md#4-what-a-plugin-can-contain) |
| always-on cost | tokens a plugin adds to every session | [HOW §10](HOW_PLUGINS_WORK.md#10-what-a-plugin-costs-tokens) |
| RCE | remote code execution: code you didn't choose running on your machine | [SECURITY §3](SECURITY.md#3-rce-every-way-code-can-run) |
| path traversal | a `../` path that escapes the folder it should stay in | [SECURITY §4](SECURITY.md#4-this-repos-auditor-defenses) |
| functional core, imperative shell | pure logic returns data; a thin outer layer does I/O | [ARCHITECTURE](ARCHITECTURE.md#design-choices) |

## References

### Official

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)

### Further learning

- [Model Context Protocol](https://modelcontextprotocol.io/introduction)
