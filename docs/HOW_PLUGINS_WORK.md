# How Claude Code plugins work

What happens, step by step, when you "download a plugin" for Claude Code:
where it comes from, what lands on your disk, what it can do, and how to
check it first. Checked against the official docs and Claude Code 2.1.268
on Windows in October 2026.

## Contents

1. [The big picture](#1-the-big-picture)
2. [Marketplaces: the catalog](#2-marketplaces-the-catalog)
3. [Plugins: the package](#3-plugins-the-package)
4. [What a plugin can contain](#4-what-a-plugin-can-contain)
5. [Installing: what happens on disk](#5-installing-what-happens-on-disk)
6. [Scopes: who gets the plugin](#6-scopes-who-gets-the-plugin)
7. [Every command, explained](#7-every-command-explained)
8. [Where you type them: terminal, VS Code, desktop](#8-where-you-type-them-terminal-vs-code-desktop)
9. [Updates and removal](#9-updates-and-removal)
10. [What a plugin costs: tokens](#10-what-a-plugin-costs-tokens)
11. [Plugins vs skills vs CLAUDE.md](#11-plugins-vs-skills-vs-claudemd)
12. [Make your own (this repo's example)](#12-make-your-own-this-repos-example)
13. [Exercises](#13-exercises)
14. [References](#references)

---

## 1. The big picture

```text
 GitHub repo (or git URL, local folder, hosted JSON)
   └─ .claude-plugin/marketplace.json      ← the CATALOG: "here are my plugins and where to fetch each"
         │
         │  claude plugin marketplace add owner/repo        (once per catalog)
         ▼
 ~/.claude/plugins/marketplaces/<marketplace>/              ← a local copy of the catalog
         │
         │  claude plugin install <plugin>@<marketplace>    (once per plugin)
         ▼
 ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/  ← the PACKAGE: skills, hooks, servers...
         │
         │  recorded in settings.json → "enabledPlugins": { "<plugin>@<marketplace>": true }
         ▼
 next session start (or /reload-plugins): Claude Code loads its components
```

If you know Python packaging, the mapping is close:

| Python | Claude Code |
| --- | --- |
| PyPI (an index of packages) | a **marketplace** (`marketplace.json`) |
| a package on PyPI | a **plugin** |
| `pip install requests` | `claude plugin install name@marketplace` |
| `pyproject.toml` | `.claude-plugin/plugin.json` |
| `site-packages/` | `~/.claude/plugins/cache/` |
| `pip install --index-url ...` | `claude plugin marketplace add ...` |

One big difference: **there's no central index you must use.** Anyone can
publish a marketplace by putting one JSON file in a GitHub repo. That's
easy, and it's also why [SECURITY.md](SECURITY.md) matters.

## 2. Marketplaces: the catalog

A marketplace is a directory or repo with `.claude-plugin/marketplace.json`.
It needs a `name`, an `owner` and a `plugins` array. Each plugin entry needs a
`name` and a `source`. This repo's example
([examples/marketplace/.claude-plugin/marketplace.json](../examples/marketplace/.claude-plugin/marketplace.json)):

```json
{
  "name": "learning-examples",
  "owner": { "name": "jericho3110" },
  "plugins": [
    { "name": "study-notes", "source": "./plugins/study-notes", "description": "..." }
  ]
}
```

**Where a plugin's files come from** (`source`):

| Source | Meaning |
| --- | --- |
| `"./plugins/x"` | a folder inside the marketplace repo (relative to the folder holding `.claude-plugin/`) |
| `{"source": "github", "repo": "owner/repo"}` | its own GitHub repo |
| `{"source": "git-subdir", "url": ..., "path": ...}` | a folder inside another repo (monorepo) |
| `url`, `archive`, `npm`, `command` | any git URL, a zip over HTTPS, an npm package, or a folder made by running a command |

**Ways to add a marketplace:**

| You type | Meaning |
| --- | --- |
| `owner/repo` | a GitHub repo; add `#v1.2.0` to pin a tag or branch |
| `https://host/group/repo.git` | any git host (always include `https://`) |
| `./my-marketplace` | a local folder (start with `./` or `../`, or it's read as `owner/repo`) |
| `https://example.com/marketplace.json` | a hosted JSON file |

**Names are checked.** Names such as `claude-plugins-official` are reserved
for Anthropic. Claude Code accepts them only from repos under
`github.com/anthropics/`, so a stranger can't pretend to be the official
catalog.

The official marketplace, `claude-plugins-official`, is added automatically
the first time you open an interactive terminal session. On this machine it
was already in `~/.claude/plugins/known_marketplaces.json` next to `ponytail`.

## 3. Plugins: the package

A plugin is a folder. `.claude-plugin/plugin.json` (the **manifest**) is
optional; without it, Claude Code finds components in their default folders.
`name` is the only required field. Real ponytail manifest:

```json
{
  "name": "ponytail",
  "version": "5.1.0",
  "description": "Lazy senior dev mode. ...",
  "author": { "name": "Dietrich Gebert", "url": "https://github.com/DietrichGebert" },
  "hooks": "./hooks/claude-codex-hooks.json"
}
```

Rules worth knowing:
- **Everything is namespaced** under the plugin name: skill `explain-file` in plugin `study-notes` runs as `/study-notes:explain-file`. Two plugins can't clash.
- **Paths start with `./`** and must stay inside the plugin folder. A `..` path is refused (path traversal).
- **`version` pins users** to that version until you change it.
- **Unknown top-level fields are stripped** with a warning; `claude plugin validate --strict` turns warnings into failures for CI.
- Put only `plugin.json` inside `.claude-plugin/`; everything else goes at the plugin root.

## 4. What a plugin can contain

| Component | Default location | What it is | Runs code? |
| --- | --- | --- | --- |
| Skills | `skills/<name>/SKILL.md` | instructions Claude loads when relevant or when you type `/<plugin>:<skill>` | no, but it steers Claude |
| Commands | `commands/*.md` | older form of skills; prefer skills | no |
| Agents | `agents/*.md` | subagents with their own prompt | no, but they steer Claude |
| Hooks | `hooks/hooks.json` | shell commands run at lifecycle events (`SessionStart`, `PreToolUse`, `UserPromptSubmit`, ...) | **yes, with your user rights** |
| MCP servers | `.mcp.json` | extra tools for Claude: a local process or a remote URL | **yes** (local) |
| LSP servers | `.lsp.json` | language servers for code intelligence | **yes** |
| Monitors | `monitors/monitors.json` | background commands started with the session | **yes** |
| Executables | `bin/` | added to the Bash tool's `PATH` | **yes** |
| Output styles, themes, settings | `output-styles/`, `themes/`, `settings.json` | look and defaults | no |

The "runs code" column is the one to care about. Hooks, monitors and server
processes run **outside** Claude Code's sandbox and permission rules. Your
permission rules apply only to the *tool calls Claude makes*.

**`${CLAUDE_PLUGIN_ROOT}`** is how a plugin finds its own files: it expands
to the installed version's folder. `${CLAUDE_PLUGIN_DATA}`
(`~/.claude/plugins/data/<id>/`) is for state that should survive updates.

**`userConfig`** lets a plugin ask you for settings (an API token, say).
Values marked `sensitive` go to the system's credential store, not to
`settings.json`.

## 5. Installing: what happens on disk

Real files from this machine after `claude plugin install ponytail@ponytail`:

```text
~/.claude/
├── settings.json                         "extraKnownMarketplaces": { "ponytail": {...} }, "enabledPlugins": { "ponytail@ponytail": true }
└── plugins/
    ├── known_marketplaces.json           each marketplace: its source repo + local folder
    ├── installed_plugins.json            each plugin: scope, version, installPath, gitCommitSha
    ├── marketplaces/
    │   ├── claude-plugins-official/      the catalog clone
    │   └── ponytail/
    ├── cache/ponytail/ponytail/5.1.0/    the plugin's files (what actually loads)
    └── data/ponytail-ponytail/           ${CLAUDE_PLUGIN_DATA}
```

(An earlier version of this tree left out `extraKnownMarketplaces`: `marketplace add` records the
marketplace in your settings as well as in `known_marketplaces.json`.)

`installed_plugins.json` records the exact **git commit** that was installed.
That's how you can tell later precisely which code you're running.

Step by step, with the theory behind each step (indexes, content addressing,
immutable caches, reconciliation, inversion of control): [INSTALL_PROCESS.md](INSTALL_PROCESS.md).

## 6. Scopes: who gets the plugin

| Scope | Written to | Who gets it |
| --- | --- | --- |
| `user` (default) | `~/.claude/settings.json` | you, in every project on this machine |
| `project` | `.claude/settings.json` (committed) | everyone working in this repo; each still runs `install --scope project` once |
| `local` | `.claude/settings.local.json` | you, in this repo only |
| `managed` | your organization's managed settings | everyone; you can't remove it |

When scopes disagree, **local beats project beats user**. The terminal, the
desktop app and VS Code on one computer read the same files, so a user-scope
install shows up in all three.

## 7. Every command, explained

Run these in your normal shell (PowerShell, bash). Each has a `/plugin ...`
form inside a session.

| Command | What it does |
| --- | --- |
| `claude plugin marketplace add <source>` | register a catalog (sources in §2) |
| `claude plugin marketplace list` | show each catalog **and where it came from**: step 1 of a security review |
| `claude plugin marketplace update [name]` | refresh catalog listings (doesn't update installed plugins) |
| `claude plugin marketplace remove <name>` | remove a catalog **and uninstall every plugin from it** |
| `claude plugin install <plugin>@<marketplace>` | install (+ enable). `-s/--scope user\|project\|local`; `-y` accepts a `command` source without a prompt (scripts only); `--config key=value` sets a `userConfig` option |
| `claude plugin list` | installed plugins with version, scope and status |
| `claude plugin details <name>` | **what it contains** (skills, agents, hooks, servers) and its token cost |
| `claude plugin enable` / `disable <plugin>` | turn on/off without uninstalling |
| `claude plugin update <plugin>@<marketplace>` | update now (restart or `/reload-plugins` to apply) |
| `claude plugin uninstall <plugin>` | remove; `--scope` to pick which scope |
| `claude plugin prune` | remove dependencies that were auto-installed and are no longer needed |
| `claude plugin validate [--strict] <path>` | check a plugin or marketplace you're writing |
| `claude plugin init <name>` | scaffold a new plugin in `~/.claude/skills/<name>/` |
| `claude --plugin-dir <dir>` | load a plugin from disk **for one session**, without installing it |

Two real commands from setting up this machine:

```bash
claude plugin marketplace add DietrichGebert/ponytail   # GitHub shorthand: owner/repo
claude plugin install ponytail@ponytail                 # plugin "ponytail" from marketplace "ponytail"
```

## 8. Where you type them: terminal, VS Code, desktop

| Where | How |
| --- | --- |
| Terminal session | `/plugin` opens a panel with **Discover**, **Installed**, **Marketplaces** and **Errors** tabs |
| VS Code extension | `/plugins` (plural) opens **Manage plugins** |
| Desktop app | **+ → Plugins → Add plugin** |
| `claude -p`, scripts, any shell | `claude plugin ...` commands (§7) |
| Cloud sessions (claude.ai/code) | no plugin browser; your local plugins don't load there |

**Found live:** typing `/plugin marketplace add DietrichGebert/ponytail` into
the VS Code chat box didn't work, because that slash command belongs to the
terminal UI. The fix was to run `claude plugin marketplace add ...` in a
shell, which writes the same settings. (VS Code's own entry point is
`/plugins`.)

## 9. Updates and removal

- **Auto-update** is on by default only for Anthropic's official marketplaces. Third-party ones such as ponytail are **off**: you update them yourself with `claude plugin update`. That's safer, because an auto-update replaces the files you reviewed.
- A running session keeps the version it loaded. `/reload-plugins` or a new session picks up changes.
- **Uninstall** deletes the plugin's data folder if no other scope uses it. The cached files stay for 14 days, then a background sweep removes them; delete `~/.claude/plugins/cache/<marketplace>/<plugin>/` yourself to remove them now.

## 10. What a plugin costs: tokens

Every enabled plugin adds some text to **every** session, for example each
skill's one-line description, so Claude knows the skill exists. The full
skill text loads only when it's used. `claude plugin details` shows both
numbers. Real output for ponytail:

```text
Projected token cost
  Always-on:   ~639 tok   added to every session
  component        always-on  on-invoke
  ponytail              ~140      ~1.1k
  ponytail-audit        ~140      ~1.8k
```

And for this repo's tiny example: `Always-on: ~54 tok`. That's the reason to
uninstall plugins you don't use: they cost context in every session, even
when you never call them.

## 11. Plugins vs skills vs CLAUDE.md

Not every "plugin" is a Claude Code plugin. On this machine:

| | ponytail | graphify |
| --- | --- | --- |
| Installed with | `claude plugin install` | its own installer: `uv tool install graphifyy`, then `graphify install` |
| Is a Claude Code plugin? | **yes** (marketplace + manifest) | **no**: a standalone **skill** plus a Python CLI |
| Lands in | `~/.claude/plugins/cache/...` | `~/.claude/skills/graphify/SKILL.md`, plus 4 lines appended to `~/.claude/CLAUDE.md` |
| Runs code via | 3 hooks (Node scripts) | the `graphify` program that the skill tells Claude to run |
| Listed by `claude plugin list`? | yes | no |
| Removed with | `claude plugin uninstall` | delete the skill folder, remove the CLAUDE.md block, `uv tool uninstall graphifyy` |

More detail in [CASE_STUDIES.md](CASE_STUDIES.md). The lighter options, from
least to most:

1. **`CLAUDE.md`**: plain instructions loaded every session. No packaging.
2. **A skill** in `~/.claude/skills/<name>/SKILL.md`: loaded when relevant.
3. **A plugin**: skills plus hooks, agents and servers, versioned and shareable through a marketplace.

## 12. Make your own (this repo's example)

```bash
claude plugin validate --strict examples/marketplace                 # the catalog
claude plugin validate --strict examples/marketplace/plugins/study-notes
claude --plugin-dir examples/marketplace/plugins/study-notes plugin details study-notes
claude plugin marketplace add ./examples/marketplace                 # try it for real...
claude plugin install study-notes@learning-examples
claude plugin marketplace remove learning-examples                   # ...and remove it again
```

Real `details` output:

```text
study-notes 0.1.0
Component inventory
  Skills (1)  explain-file
  Agents (0)
  Hooks (0)
  MCP servers (0)
  LSP servers (0)
```

## 13. Exercises

1. Run `claude plugin marketplace list`. For each one, what's the source, and who controls it?
2. Run `python main.py audit` on each folder under `~/.claude/plugins/cache/`. What runs code?
3. Add a second skill to `study-notes`, then validate it and check `details`. How did the always-on cost change?
4. Add `"hooks": "../outside.json"` to the example manifest and run `validate`. What error do you get, and why does it matter?
5. Load the example with `--plugin-dir` and run `/study-notes:explain-file plugin_audit.py`.

**Self-check:** why do Claude Code's permission rules not protect you from a plugin's hooks?

## References

**§1–4 Marketplaces, plugins, components (official)**
- [Install and manage plugins](https://code.claude.com/docs/en/discover-plugins) ✔ (scopes, add-marketplace sources, VS Code `/plugins`, auto-update defaults)
- [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces) ✔ (required fields, source types, relative-path rules)
- [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference) ✔ (fields, path rules, standard layout, `${CLAUDE_PLUGIN_ROOT}`)
- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Hooks reference](https://code.claude.com/docs/en/hooks), [MCP](https://code.claude.com/docs/en/mcp), [Skills](https://code.claude.com/docs/en/skills)

**§5–10 Disk, scopes, commands, updates**
- [Settings](https://code.claude.com/docs/en/settings) (settings files and precedence)
- [Plugin security and trust](https://code.claude.com/docs/en/plugins/security) ✔ (cache path, 14-day cleanup, reserved names)
- `claude plugin --help`, `claude plugin install --help`, `claude plugin validate --help` (run locally, v2.1.268) ✔

**§11 Case studies**
- [ponytail](https://github.com/DietrichGebert/ponytail), [graphify](https://github.com/Graphify-Labs/graphify)

**Other explanations**
- [Anthropic's official plugin marketplace on GitHub](https://github.com/anthropics/claude-plugins-official) (real plugins to read)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/) (for the pip comparison in §1)

### Further learning
- [Model Context Protocol: introduction](https://modelcontextprotocol.io/introduction) (what MCP servers are)
- Read `plugins/example-plugin` in the official marketplace: one of every component type
- [Language Server Protocol overview](https://microsoft.github.io/language-server-protocol/)
