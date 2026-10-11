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
| context window | everything the model sees in one request, and the limit on its size | [CONTEXT §1](CONTEXT_MEMORY_CACHE.md#1-the-context-window) |
| compaction | replacing older conversation with a summary to free context | [CONTEXT §1](CONTEXT_MEMORY_CACHE.md#1-the-context-window) |
| auto memory | notes Claude writes in `~/.claude/projects/<project>/memory/`, loaded each session | [CONTEXT §2](CONTEXT_MEMORY_CACHE.md#2-memory) |
| prompt cache | server-side reuse of an identical prompt prefix: cheaper and faster, same output | [CONTEXT §3](CONTEXT_MEMORY_CACHE.md#3-the-prompt-cache) |
| monitor | a background command started with the session | [SECURITY §3](SECURITY.md#3-rce-every-way-code-can-run) |
| scope | who gets a plugin: user, project, local or managed | [HOW §6](HOW_PLUGINS_WORK.md#6-scopes-who-gets-the-plugin) |
| `${CLAUDE_PLUGIN_ROOT}` | the installed plugin's folder, for finding its own files | [HOW §4](HOW_PLUGINS_WORK.md#4-what-a-plugin-can-contain) |
| always-on cost | tokens a plugin adds to every session | [HOW §10](HOW_PLUGINS_WORK.md#10-what-a-plugin-costs-tokens) |
| RCE | remote code execution: code you didn't choose running on your machine | [SECURITY §3](SECURITY.md#3-rce-every-way-code-can-run) |
| path traversal | a `../` path that escapes the folder it should stay in | [SECURITY §4](SECURITY.md#4-this-repos-auditor-defenses) |
| declared / fetched / loaded | the three stages of a plugin: in settings, on disk, in the running session | [INSTALL §2](INSTALL_PROCESS.md#2-the-mental-model-declared-fetched-loaded) |
| content addressing | naming data by a hash of its content (a git commit SHA) | [INSTALL §4.3](INSTALL_PROCESS.md#43-compute-the-version-pinning-and-content-addressing) |
| inversion of control | the framework calls your code when an event happens | [INSTALL §6](INSTALL_PROCESS.md#6-step-4-run-events-call-the-plugin) |
| plugin architecture (microkernel) | a small core with extension points others fill | [INSTALL §1](INSTALL_PROCESS.md#1-why-plugins-exist-the-plugin-architecture) |
| functional core, imperative shell | pure logic returns data; a thin outer layer does I/O | [ARCHITECTURE](ARCHITECTURE.md#design-choices) |

## References

### Official

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)

### Further learning

- [Model Context Protocol](https://modelcontextprotocol.io/introduction)
