# The install process, in theory and in practice

[HOW_PLUGINS_WORK.md](HOW_PLUGINS_WORK.md) says *what* the pieces are. This
doc follows **one install from the command you type to a hook running**, and
names the computer-science idea behind each step. The running example is the
real install of ponytail on this machine:

```bash
claude plugin marketplace add DietrichGebert/ponytail
claude plugin install ponytail@ponytail
```

## Contents

1. [Why plugins exist: the plugin architecture](#1-why-plugins-exist-the-plugin-architecture)
2. [The mental model: declared, fetched, loaded](#2-the-mental-model-declared-fetched-loaded)
3. [Step 1: add the marketplace (find the catalog)](#3-step-1-add-the-marketplace-find-the-catalog)
4. [Step 2: install (resolve, fetch, pin, cache, record)](#4-step-2-install-resolve-fetch-pin-cache-record)
5. [Step 3: load (at session start)](#5-step-3-load-at-session-start)
6. [Step 4: run (events call the plugin)](#6-step-4-run-events-call-the-plugin)
7. [Step 5: update and clean up](#7-step-5-update-and-clean-up)
8. [Where trust is checked along the way](#8-where-trust-is-checked-along-the-way)
9. [The concepts, collected](#9-the-concepts-collected)
10. [Compared with pip, npm and VS Code](#10-compared-with-pip-npm-and-vs-code)
11. [Exercises](#11-exercises)
12. [References](#references)

---

## 1. Why plugins exist: the plugin architecture

Claude Code has a small, fixed core (the agent loop, the tools, permissions)
and lets anyone add behaviour **without changing the core**. That's the
**plugin architecture**, also called the **microkernel pattern**:

```text
            ┌──────────── Claude Code core ────────────┐
            │  agent loop · tools · permissions · UI    │
            │                                           │
            │   extension points (the "sockets"):       │
            │   skills · agents · hooks · MCP · LSP ... │
            └───────▲────────▲─────────▲────────────────┘
                    │        │         │
               ponytail   graphify   your plugin       ← plug-ins fill the sockets
```

It follows the **open/closed principle**: the core is *closed* for
modification but *open* for extension. Python works the same way: `pytest`
finds plugins through *entry points*, without pytest being edited for each one.

The cost: every plugin is somebody else's code inside your tool. Hence §8.

## 2. The mental model: declared, fetched, loaded

The official docs describe three stages. Each has its own files:

```text
 DECLARED (what you want)          FETCHED (what's on disk)                 LOADED (what runs)
 settings.json                     ~/.claude/plugins/                        this session's memory
 ─────────────────────             ──────────────────────────                ───────────────────
 extraKnownMarketplaces  ──►       known_marketplaces.json + marketplaces/   
 enabledPlugins          ──►       installed_plugins.json  + cache/   ──►    skills, hooks, servers
                          fetch                                       load
                          (network)                                   (no network; at start
                                                                       or /reload-plugins)
```

This is **declarative configuration with reconciliation**. You declare the
*desired state* ("ponytail should be enabled"), and Claude Code brings the
*actual state* (files on disk, things loaded) in line with it. Package
managers, Kubernetes and Terraform all work this way. It explains two things
people find surprising:

- **Editing settings doesn't change a running session.** The loaded stage only updates on a new session or `/reload-plugins`.
- **Loading needs no network.** Plugins load from the cache, so a session starts fast and offline. Fetching happens in the background afterwards.

## 3. Step 1: add the marketplace (find the catalog)

`claude plugin marketplace add DietrichGebert/ponytail`

| # | What happens | Concept |
| --- | --- | --- |
| 1 | The source string is **parsed**: `owner/repo` means GitHub; `./x` means a folder; `https://…` means a URL. A bare `gitlab.com/x/y` is read as GitHub shorthand and rejected | **parsing with a grammar**; why "include `https://`" matters |
| 2 | The repo is **cloned**: over SSH if your SSH key works for github.com, otherwise HTTPS, using git credentials already on your machine; never a password prompt | **reusing an existing trust store** instead of inventing one |
| 3 | `.claude-plugin/marketplace.json` is read and checked: name, owner, plugin entries | **schema validation** at a trust boundary |
| 4 | The **name** is checked: official names (`claude-plugins-official`, …) are accepted only from `github.com/anthropics/` | a **namespace authority**, like domain names: only the owner can use a name |
| 5 | Two records are written: the *declaration* in `settings.json` and the *state* in `known_marketplaces.json` | **desired state vs actual state** (§2) |

Real records after this step:

```json
// ~/.claude/settings.json (declared)
"extraKnownMarketplaces": { "ponytail": { "source": { "source": "github", "repo": "DietrichGebert/ponytail" } } }

// ~/.claude/plugins/known_marketplaces.json (fetched)
"ponytail": { "source": {...}, "installLocation": "~/.claude/plugins/marketplaces/ponytail", "lastUpdated": "2026-10-09T10:22:48.867Z" }
```

**Nothing from the catalog runs at this step.** It's data: a list of plugins
and where they live.

## 4. Step 2: install (resolve, fetch, pin, cache, record)

`claude plugin install ponytail@ponytail`

### 4.1 Look it up: the catalog is an index

`ponytail@ponytail` means *plugin* `ponytail` from *marketplace* `ponytail`.
Naming the marketplace makes Claude Code **refresh** that catalog first (unless
it did so in the last 30 seconds), then look the plugin up in it.

**Concept: a package index.** PyPI is an index for pip; the marketplace is an
index for Claude Code. The `name@marketplace` form is **fully qualified**:
two marketplaces can both have a `formatter` without ambiguity, like
`module.function` in Python.

### 4.2 Resolve the source: one level of indirection

The catalog entry doesn't contain the plugin; it **points** to it:
`"source": "./"` (inside the catalog repo itself, for ponytail), or a GitHub
repo, a git subfolder, a zip URL, an npm package. That's **indirection**:
the catalog can move or re-point a plugin without users changing anything.

### 4.3 Compute the version: pinning and content addressing

Claude Code needs a version string to name the cache folder and to detect
updates. In order:

1. `version` in the plugin's own `plugin.json` (ponytail: `"5.1.0"`)
2. else `version` in the catalog entry
3. else derived from the content: the **git commit SHA** (12 characters), or the **SHA-256 digest** of a zip

**Concept: content addressing.** A commit SHA is a hash of the content, so
the same SHA always means exactly the same files. Pinning `"version": "5.1.0"`
is **semantic versioning**: a human promise. Leaving `version` out makes every
new commit a new version. On this machine, `installed_plugins.json` records
both: `"version": "5.1.0"` and `"gitCommitSha": "9cc65d03…"`, which is exactly
the commit the catalog clone is at (`9cc65d0`).

### 4.4 Copy into the cache: immutable versioned folders

The plugin is **copied** into `~/.claude/plugins/cache/ponytail/ponytail/5.1.0/`.
Files outside the plugin folder are not copied.

**Concept: immutability.** A version folder is never edited after it's
written; an update writes a *new* folder (§7). So a running session can't have
its files changed under it, and a rollback is just pointing at the old folder.
Python's `site-packages` doesn't work this way (pip overwrites in place),
which is one reason virtual environments exist.

(Plugins from a **local** marketplace folder are the exception: they load *in
place*, so your edits show up on the next reload. That's handy while writing a plugin.)

### 4.5 Install its packages, with the dangerous parts switched off

If the plugin folder has **both** a `package.json` and a lockfile
(`package-lock.json`, `npm-shrinkwrap.json` or `bun.lock`), Claude Code runs
npm or Bun to install its Node packages, with strict limits:

| Limit | Why |
| --- | --- |
| only registry packages, each **pinned to an exact version** by the lockfile ("frozen") | **reproducible builds**: everyone gets identical code |
| `--ignore-scripts`: no `preinstall`/`postinstall` scripts | install scripts are the classic **supply-chain attack**: code that runs just by installing |
| `https` downloads only | no tampering in transit |
| run in a separate folder holding only the dependency list | the plugin's own `.npmrc` or `.env` can't redirect the install |
| 60-second timeout | a hostile package can't hang the install |

**No code from the plugin or its packages runs during installation.**
ponytail has a `package.json` but **no lockfile**, so this step was skipped:
its hooks use only Node's built-in modules.

Plugins can also **depend on other plugins**. Those are installed and enabled
at the same scope, like pip installing `requests`' dependencies.

### 4.6 Record and enable

Two more records, again *state* and *declaration*:

```json
// ~/.claude/plugins/installed_plugins.json (state)
"ponytail@ponytail": [{ "scope": "user", "version": "5.1.0", "installPath": ".../cache/ponytail/ponytail/5.1.0",
                        "installedAt": "...", "lastUpdated": "...", "gitCommitSha": "9cc65d03..." }]

// ~/.claude/settings.json (declared; user scope, so the user file)
"enabledPlugins": { "ponytail@ponytail": true }
```

**Concept: separating install from enable.** Installed means "on disk";
enabled means "load it". You can disable without deleting, and a project can
enable a plugin that each person installs.

## 5. Step 3: load (at session start)

| # | What happens | Concept |
| --- | --- | --- |
| 1 | `enabledPlugins` is merged from **six sources**, lowest to highest: `--add-dir`, user, project, local, `--settings` flag, managed. For each plugin id, the highest source that mentions it wins | **layered configuration** (cascading), like CSS or Git's system → global → local config |
| 2 | If two enabled plugins share a manifest name, a fixed order decides: managed > `--plugin-dir` > marketplace > skills folder > synced from claude.ai | **deterministic conflict resolution**: same inputs, same result |
| 3 | Each plugin's `plugin.json` is read; every component path must stay inside the plugin folder | **path containment** (no `../` escapes) |
| 4 | Everything is **namespaced**: skill `ponytail-audit` becomes `/ponytail:ponytail-audit` | **namespaces** prevent name clashes, like Python modules |
| 5 | Skills: only each skill's **description** enters the context; the full text loads when used | **lazy loading / progressive disclosure**: why the always-on cost is ~639 tokens, not ~7,000 |
| 6 | Hooks are **registered** for their events; MCP and LSP servers are started; `bin/` joins the Bash tool's `PATH`; `${CLAUDE_PLUGIN_ROOT}` is replaced with the version folder | **registration** of callbacks; **dependency injection** of paths |

Project-scope plugins (from a repo's `.claude/settings.json`) load only after
you accept that folder's **workspace trust** dialog, because the repo, not
you, chose them.

## 6. Step 4: run (events call the plugin)

A plugin never "runs itself". Claude Code **calls it** when something
happens:

```text
session starts ──► SessionStart event ──► ponytail hook: node .../ponytail-activate.js
                                               │ prints the rules on stdout
                                               ▼
                                   Claude Code adds that text to the context
you send a message ──► UserPromptSubmit ──► ponytail-mode-tracker.js ("stop ponytail"?)
a subagent starts ──► SubagentStart ──► ponytail-subagent.js
```

**Concepts:**
- **Inversion of control** ("don't call us, we'll call you"): the framework decides *when*; the plugin decides *what*.
- **Observer / publish–subscribe:** hooks subscribe to named events, and Claude Code publishes them.
- **Process isolation, but not a sandbox:** each hook is a separate process (a crash doesn't crash Claude Code), but it runs **with your user rights**.

## 7. Step 5: update and clean up

| What happens | Concept |
| --- | --- |
| `claude plugin update` (or auto-update) refreshes the catalog and **recomputes the version** (§4.3) | — |
| same version → nothing is replaced ("already at the latest version") | **idempotency**: running it twice changes nothing more |
| new version → a **new** cache folder; the running session keeps the old one until `/reload-plugins` or a restart | **immutability** again: no half-updated state |
| the old folder gets an `.orphaned_at` marker and is deleted **14 days** later | **garbage collection with a grace period**: long-running sessions keep working |
| auto-update waits a **random delay of up to 10 minutes** after your first message | **jitter**: spreads millions of clients over time so servers aren't hit at once (avoids a "thundering herd") |
| auto-update is on only for official catalogs; third-party ones like ponytail are off unless you turn it on | **secure default**: reviewed code doesn't silently change |

## 8. Where trust is checked along the way

```text
add catalog ──► reserved names checked (official names only from github.com/anthropics/)
install     ──► you confirm (and see "Will install" in /plugin); command-type sources ask first
            ──► dependency install: pinned, no scripts, https, isolated, timed out
            ──► archive sources can be pinned to a SHA-256 digest; a mismatch is refused
load        ──► paths must stay inside the plugin; project plugins need workspace trust
run         ──► hooks, monitors, MCP/LSP servers: NOT sandboxed, NOT under permission rules
            ──► MCP tool calls and bin/ commands: under your permission rules
```

The pipeline protects **the install itself** well: nothing runs while
installing. It does **not** judge what the plugin's code does once it runs.
That part is your review ([SECURITY.md](SECURITY.md),
`python main.py audit`).

## 9. The concepts, collected

| Concept | Where in the process | The same idea in Python |
| --- | --- | --- |
| plugin architecture / open–closed | §1 | pytest plugins via entry points |
| declarative config + reconciliation | §2 | `requirements.txt` → `pip install -r` |
| package index | §4.1 | PyPI |
| fully qualified names | §4.1 | `package.module.function` |
| indirection | §4.2 | a PyPI page pointing at the files |
| content addressing | §4.3 | `pip install --require-hashes` |
| semantic versioning / pinning | §4.3 | `requests==2.32.3` |
| immutable versioned cache | §4.4 | (pip doesn't; virtual environments and `uv`'s cache come close) |
| supply-chain hardening | §4.5 | `pip install --only-binary :all: --require-hashes` |
| install vs enable | §4.6 | installed package vs `import`ed |
| layered configuration | §5 | `pip.conf` per user, per environment |
| lazy loading | §5 | importing inside a function |
| namespacing | §5 | modules |
| inversion of control, observer | §6 | `atexit.register`, `signal.signal` callbacks |
| idempotency | §7 | `pip install x` twice |
| garbage collection with grace period | §7 | (no direct equivalent) |
| jitter | §7 | `time.sleep(random.uniform(0, 600))` |

## 10. Compared with pip, npm and VS Code

| | Claude Code plugin | pip | npm | VS Code extension |
| --- | --- | --- | --- | --- |
| Index | any git repo can be one | PyPI (central) | npm registry (central) | Marketplace (central) |
| Version from | manifest, else commit SHA / digest | package metadata | package.json | package.json |
| Install runs package code? | **no** (scripts off) | can (source builds run `setup.py`) | yes, unless `--ignore-scripts` | no |
| Stored as | immutable version folders | overwritten in place | per-project `node_modules` | version folders |
| Updates | official: auto; others: manual | manual | manual | auto (12 h delay) |
| Runs code when | events (hooks), session start (servers) | when imported | when required | on activation events |

## 11. Exercises

1. Open your `installed_plugins.json` and `known_marketplaces.json`. Which stage (§2) does each belong to?
2. In `~/.claude/plugins/marketplaces/<name>/`, run `git log -1`. Does the commit match `gitCommitSha` in `installed_plugins.json`?
3. Write a plugin whose `plugin.json` has no `version`. Install it from a local marketplace, commit a change, and run `claude plugin update`. What version did it get?
4. Why is `--ignore-scripts` enough to stop code running at install time, but not enough to make a plugin safe?
5. Explain "declared, fetched, loaded" using pip and a running Python program instead.

**Self-check:** why does editing `enabledPlugins` not change the session you're in?

## References

### Official

- Claude Code: [Plugin loading reference](https://code.claude.com/docs/en/plugins/loading) ✔ (three stages, files on disk, version computation, dependency-install limits, update and cleanup, name conflicts, settings precedence), [Install and manage plugins](https://code.claude.com/docs/en/discover-plugins) ✔ (marketplace sources, private repos, scopes), [Plugin security and trust](https://code.claude.com/docs/en/plugins/security) ✔ (reserved names, what runs outside the sandbox), [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference) ✔
- npm: [`ignore-scripts`](https://docs.npmjs.com/cli/v10/using-npm/config#ignore-scripts), [package-lock.json](https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json)
- pip: [Secure installs (hash-checking mode)](https://pip.pypa.io/en/stable/topics/secure-installs/), Python: [entry points](https://packaging.python.org/en/latest/specifications/entry-points/)
- Git: [Git objects (content addressing)](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- [Semantic Versioning](https://semver.org/)

### Other

- [Plug-in (computing)](https://en.wikipedia.org/wiki/Plug-in_(computing)) (overview of plugin architectures); Mark Richards, *Software Architecture Patterns* (O'Reilly), chapter "Microkernel Architecture"
- Martin Fowler, [Inversion of Control Containers and the Dependency Injection pattern](https://martinfowler.com/articles/injection.html)
- Kubernetes: [Controllers (desired vs actual state)](https://kubernetes.io/docs/concepts/architecture/controller/)
- AWS Architecture Blog: [Exponential backoff and jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [SLSA supply-chain levels](https://slsa.dev/)

### Further learning

- *Refactoring.Guru*: [Observer pattern](https://refactoring.guru/design-patterns/observer)
- [Exercism Python track](https://exercism.org/tracks/python) (build a tiny plugin loader with entry points as practice)
