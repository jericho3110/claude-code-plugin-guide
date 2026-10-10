# Security

Two subjects: **plugins you install** (the real risk) and **this repo's own
code** (`plugin_audit.py`, which reads untrusted plugin files).

## Contents

1. [Threat model: what a plugin can do to you](#1-threat-model-what-a-plugin-can-do-to-you)
2. [Checklist before installing a plugin](#2-checklist-before-installing-a-plugin)
3. [RCE: every way code can run](#3-rce-every-way-code-can-run)
4. [This repo's auditor: defenses](#4-this-repos-auditor-defenses)
5. [Review table](#5-review-table)
6. [Accepted risks](#6-accepted-risks)
7. [References](#references)

---

## 1. Threat model: what a plugin can do to you

The official docs put it plainly: *"A Claude Code plugin you install can
execute arbitrary code on your machine with your user privileges."*

| Asset | Threat | Through |
| --- | --- | --- |
| your files, SSH keys, browser cookies | read and sent away | a hook or MCP server: plain code with your rights |
| your machine | malware installed | hooks, monitors, `bin/`, `.mcpb` bundles |
| your repos | malicious commits | instructions in a skill or agent that steer Claude |
| what you reviewed | silently replaced | auto-update to a new version |
| trust in the catalog name | impersonation | a marketplace pretending to be official (Claude Code blocks reserved names) |

## 2. Checklist before installing a plugin

1. **Who publishes it?** `claude plugin marketplace list` shows each source. Is it a person or organization you can check?
2. **What runs code?** `python main.py audit <plugin folder>` (or `claude plugin details`). Every `runs-code` line deserves reading.
3. **Read the hook, server and `bin/` files.** Look for network calls, shell strings, writes outside its own folders, obfuscated code, and downloads at run time.
4. **Prefer pinned versions.** `installed_plugins.json` records the git commit. Leave auto-update **off** for third-party marketplaces (the default), so the files you read stay the files you run.
5. **Smallest scope.** Use `--scope local` to try a plugin in one repo first.
6. **Remove what you don't use** (`claude plugin uninstall`): less code, less context.

To review a plugin *before* installing it, clone its repo and run either:

```bash
python main.py audit path/to/clone/plugin-folder
claude --plugin-dir path/to/clone/plugin-folder plugin details <name>
```

## 3. RCE: every way code can run

| Path | Runs when | Inside permission rules / sandbox? | How to see it |
| --- | --- | --- | --- |
| hooks (`hooks/hooks.json`, manifest `hooks`) | lifecycle events, automatically | **no** | audit: `hook` |
| monitors | session start or first use of a skill | **no** | audit: `monitor` |
| MCP stdio servers (`.mcp.json`, `mcpServers`) | session start | the process, **no**; calls to its tools, yes | audit: `mcp` |
| `.mcpb` / `.dxt` bundles | session start | **no**; contents not readable as text | audit: `bundle` |
| LSP servers | when files of that language open | **no** | audit: `lsp` |
| `headersHelper` | each request to a remote MCP server | **no** | audit: `headersHelper` |
| `bin/` executables | when Claude runs them via Bash | yes (a tool call) | audit: `bin` |
| skills, agents, commands | when Claude loads them | yes: they only steer Claude's tool calls | audit: `skill` / `agent` / `command` |
| `command` plugin source | at **install** time | asks you first (or `-y`) | read `marketplace.json` |

**This repo's own code runs nothing from a plugin.** `plugin_audit.py`
parses JSON and lists files. It never imports, executes or downloads
plugin content.

## 4. This repo's auditor: defenses

`plugin_audit.py` reads files from plugins you haven't trusted yet, so it
treats them as hostile input:

| Defense | Where | Test |
| --- | --- | --- |
| JSON files over 1 MB refused | `read_json`, `MAX_JSON_BYTES` | `test_refuses_oversized_json` |
| manifest paths that escape the plugin root are flagged and **not read** | `inside()` | `test_flags_path_traversal_in_manifest` |
| symlinks pointing outside the plugin flagged | the walk in `audit()` | manual check (Windows symlinks need admin rights) |
| walk stops after 20,000 files | `MAX_FILES` | by code review |
| malformed JSON → warning, not a crash | every `read_json` call is wrapped | `test_malformed_json_is_a_warning_not_a_crash` |
| unencrypted remote `http://` / `ws://` flagged (loopback allowed) | `url_finding` | `test_flags_unencrypted_remote_url_but_not_loopback` |
| no `eval`, `exec`, `shell=True` or `pickle` anywhere | whole repo | `devtools scan` in the gate |

The check gate (`python main.py check`) runs the tests, ruff,
`claude plugin validate --strict` on the example, the `devtools` security
scan (secrets, personal data, dangerous patterns) and the link check.

## 5. Review table

| # | Finding | Fix | Test |
| --- | --- | --- | --- |
| 1 | an auditor that followed a `../` hooks path would read files outside the plugin | resolve and check containment first; flag, don't read | `test_flags_path_traversal_in_manifest` |
| 2 | a huge JSON file could exhaust memory | 1 MB limit before parsing | `test_refuses_oversized_json` |
| 3 | the report heading showed the version folder (`5.1.0`), not the plugin name | read `name` from the manifest | `test_example_plugin_runs_no_code` (checks the report) |

## 6. Accepted risks

| Limit | Why accepted |
| --- | --- |
| the auditor lists code; it doesn't judge whether code is malicious | that needs a human reading it; the tool shows *where* to read |
| `.mcpb` bundles and npm/`command` sources aren't unpacked | unpacking untrusted archives is its own risk; the report says "code you can't read here" |
| auditing a marketplace *entry* with inline components isn't covered | the common case is a plugin folder; validate the marketplace with `claude plugin validate` |

## References

### Official

- Claude Code: [Plugin security and trust](https://code.claude.com/docs/en/plugins/security) ✔, [Security](https://code.claude.com/docs/en/security), [Manage plugins for your organization](https://code.claude.com/docs/en/plugins/org)
- Python: [`pathlib.Path.resolve` and `is_relative_to`](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to) ✔

### Other

- [OWASP: Path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [OWASP Top 10 for LLM applications](https://genai.owasp.org/llm-top-10/) (prompt injection, supply chain)
- [SLSA: supply-chain levels](https://slsa.dev/) (why pinning versions matters)

### Further learning

- [GitHub: About supply chain security](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-supply-chain-security)
