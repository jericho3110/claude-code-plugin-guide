# Case studies: two real installs

Two "plugins" installed on this machine in October 2026, done two very
different ways. They show what the theory in
[HOW_PLUGINS_WORK.md](HOW_PLUGINS_WORK.md) looks like in practice.

## Contents

1. [ponytail: a real Claude Code plugin](#1-ponytail-a-real-claude-code-plugin)
2. [graphify: a skill with its own installer](#2-graphify-a-skill-with-its-own-installer)
3. [Side by side](#3-side-by-side)
4. [Surprises found while installing](#4-surprises-found-while-installing)
5. [References](#references)

---

## 1. ponytail: a real Claude Code plugin

**What it does:** puts Claude in "lazy senior developer" mode: the smallest
change that fully works, standard library first, no unrequested abstractions.

**Install:**

```bash
claude plugin marketplace add DietrichGebert/ponytail   # the repo is its own one-plugin marketplace
claude plugin install ponytail@ponytail                 # user scope by default
```

**What it contains** (`claude plugin details ponytail@ponytail`):

```text
Skills (6)  ponytail, ponytail-audit, ponytail-debt, ponytail-gain, ponytail-help, ponytail-review
Hooks (3)  SessionStart, SubagentStart, UserPromptSubmit
Always-on:   ~639 tok   added to every session
```

**How it works:** the hooks are the engine. Each runs a small Node script
from `${CLAUDE_PLUGIN_ROOT}/hooks/`:

| Hook | When | What the script does |
| --- | --- | --- |
| `SessionStart` (startup, resume, clear, compact) | each session start | prints the ponytail rules and a short map of the repo's files; hook output goes into Claude's context |
| `SubagentStart` | each subagent | gives subagents the same rules |
| `UserPromptSubmit` | each message you send | tracks "stop ponytail" or "/ponytail lite" to change the mode |

**One repo, many tools:** the repo also carries `.cursor/`, `.windsurf/`,
`.codex-plugin/`, `.github/copilot-instructions.md` and others. The same
rules are packaged for many AI coding tools, and Claude Code reads only
`.claude-plugin/`.

**Security review** (done before trusting it; reproduce with
`python main.py audit <path>`):

```text
Plugin: ponytail
  [runs-code] hook  hooks/claude-codex-hooks.json: SessionStart [startup|resume|clear|compact] command: node -e "require(...'hooks/ponytail-activate.js')"
  [runs-code] hook  hooks/claude-codex-hooks.json: SubagentStart [*] command: node -e "require(...'hooks/ponytail-subagent.js')"
  [runs-code] hook  hooks/claude-codex-hooks.json: UserPromptSubmit [*] command: node -e "require(...'hooks/ponytail-mode-tracker.js')"
  [info     ] skill skills/: instructions for Claude: ponytail, ponytail-audit, ...
3 thing(s) that run code, 0 warning(s).
```

Then the ~990 lines of hook JavaScript were read, with a search for
anything that runs commands, makes network requests or writes files:

| Looked for | Found | Verdict |
| --- | --- | --- |
| network (`http`, `fetch`) | none | ✔ |
| shell / processes | one `execFileSync('git', ['ls-files'], {timeout: 3000})`: an argument list, no shell | ✔ no injection |
| `vm` module | `vm.runInNewContext('re.test(s)', ..., {timeout: 100})`: a fixed string, used only to time-limit a regex from the config | ✔ (not used as a sandbox) |
| file writes | its own mode/config files under the Claude config folder | ✔ |

## 2. graphify: a skill with its own installer

**What it does:** turns a folder of code and documents into a knowledge
graph (`graphify-out/graph.json`, an HTML view and a report), which Claude
can query instead of re-reading files.

**Install:** it isn't in a Claude Code marketplace. It's a Python package
(`graphifyy` on PyPI) with an installer that writes into Claude's folders:

```bash
uv tool install graphifyy      # installs the `graphify` command in its own isolated environment
graphify install               # writes the skill + a CLAUDE.md block
```

`uv tool install` is like `pipx install`: one virtual environment per tool,
so its dependencies can't clash with your projects.

**What `graphify install` changed:**

| File | Change |
| --- | --- |
| `~/.claude/skills/graphify/SKILL.md` | a new **skill**: what `/graphify` does and which commands Claude should run |
| `~/.claude/CLAUDE.md` | 4 lines appended so every session knows the skill exists |

**What runs code:** the skill doesn't, but it tells Claude to run the
`graphify` program through the Bash tool. So, unlike a plugin hook, **each run
goes through Claude Code's permission rules**: you see and approve the command.

**Self-modification is guarded:** Claude Code's auto mode refused to run
`graphify install` until the user explicitly approved it, because the
command edits Claude's own configuration (`~/.claude/`). That's the
safety net working: an agent shouldn't quietly change its own rules.

## 3. Side by side

| | ponytail | graphify |
| --- | --- | --- |
| Kind | Claude Code plugin | standalone skill + Python CLI |
| Comes from | a GitHub marketplace | PyPI |
| Installed by | `claude plugin install` | `uv tool install` + its own `graphify install` |
| Code runs as | hooks, automatically, outside permission rules | Bash commands Claude runs, inside permission rules |
| Version recorded | `installed_plugins.json` (version + git commit) | `uv tool list` |
| Context cost | ~639 tokens per session | the skill description + the CLAUDE.md lines |
| Update | `claude plugin update ponytail@ponytail` | `uv tool upgrade graphifyy`, then `graphify install` again |
| Remove | `claude plugin uninstall ponytail@ponytail` | delete `~/.claude/skills/graphify/`, remove the CLAUDE.md block, `uv tool uninstall graphifyy` |

**Lesson:** "install a plugin" can mean very different things. Before
installing, find out *which mechanism* it uses, because that decides what
can run without asking you.

## 4. Surprises found while installing

| Found live | Why | What to do |
| --- | --- | --- |
| `/plugin marketplace add ...` did nothing in the VS Code chat | `/plugin` is the terminal UI's command; VS Code's is `/plugins` | run `claude plugin ...` in any shell (same settings files) |
| the graphify GitHub link 404'd with `blob/main/` | its default branch isn't `main` | link with `blob/HEAD/`, which follows the default branch |
| auto mode blocked `graphify install` | it edits Claude's own config | approve explicitly, after reading what it changes |
| `claude plugin list` doesn't show graphify | it's a skill, not a plugin | look in `~/.claude/skills/` |

## References

### Official

- Claude Code: [Plugin security and trust](https://code.claude.com/docs/en/plugins/security) ✔, [Hooks reference](https://code.claude.com/docs/en/hooks), [Skills](https://code.claude.com/docs/en/skills)
- uv: [Using tools](https://docs.astral.sh/uv/guides/tools/) (`uv tool install`)
- Node.js: [`vm` module](https://nodejs.org/api/vm.html) ✔ ("The node:vm module is not a security mechanism"), [`child_process.execFileSync`](https://nodejs.org/api/child_process.html#child_processexecfilesyncfile-args-options)

### The projects

- [ponytail on GitHub](https://github.com/DietrichGebert/ponytail)
- [graphify on GitHub](https://github.com/Graphify-Labs/graphify), [graphifyy on PyPI](https://pypi.org/project/graphifyy/)

### Further learning

- [pipx](https://pipx.pypa.io/) (the older tool `uv tool` replaces)
- [OWASP: OS command injection](https://owasp.org/www-community/attacks/Command_Injection) (why argument lists beat shell strings)
