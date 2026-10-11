# Context, memory and the prompt cache

Three things that sound alike but do different jobs:

| | **Context window** | **Memory** (CLAUDE.md + auto memory) | **Prompt cache** |
| --- | --- | --- | --- |
| what it is | everything the model can see in one request | text files loaded into the context at the start of each session | a server-side store of already-processed prompt prefixes |
| who writes it | Claude Code assembles it every turn | you (CLAUDE.md) and Claude (auto memory) | the API, automatically |
| lasts | one request (rebuilt each turn) | until you edit or delete the files | minutes to an hour, then expires |
| changes answers? | yes: it's all the model knows right now | yes: it's part of the context | **no**: same output as without it |
| why you care | size limit; cost grows with it | knowledge across sessions | speed and price |

## Contents

- [1. The context window](#1-the-context-window)
- [2. Memory](#2-memory)
- [3. The prompt cache](#3-the-prompt-cache)
- [4. One turn, end to end](#4-one-turn-end-to-end)
- [5. Python analogies](#5-python-analogies)
- [6. Found live](#6-found-live)
- [7. Exercises](#7-exercises)
- [References](#references)

## 1. The context window

A model has no memory between requests. Every time you send a message,
Claude Code sends the **whole conversation again**: its own instructions,
the tool definitions, your CLAUDE.md files, the memory index, every earlier
message and every tool result. That bundle is the *context*; the limit on
its size is the *context window*.

Consequences:

- **Cost grows with the conversation.** A one-line question late in a long
  session still carries the whole history.
- **When it fills up, Claude Code compacts:** it summarises older history
  to free space. `/compact` does it on request (you can say what to keep:
  `/compact Focus on the test failures`). Details from before the summary
  are gone unless the summary kept them.
- **`/clear` starts fresh**, which is free. Use it between unrelated tasks.
- `/context` shows what is taking space; `/usage` shows the tokens used.

## 2. Memory

Memory is how knowledge survives from one session to the next. It works by
**putting text back into the context** at the start of every session.

| Kind | Written by | Where | Loaded |
| --- | --- | --- | --- |
| user CLAUDE.md | you | `~/.claude/CLAUDE.md` | every session, every project |
| project CLAUDE.md | you (and your team, via git) | `./CLAUDE.md` in the project | sessions in that project |
| auto memory | Claude | `~/.claude/projects/<project>/memory/` | `MEMORY.md` (the index): first 200 lines or 25 KB; topic files when relevant |

- `<project>` comes from the **git repository** (all subfolders and
  worktrees of one repo share it) or, outside a repo, from the **folder
  path**. Moving a non-repo project folder therefore points Claude Code at
  a new, empty memory folder: copy the old one across, or set
  `autoMemoryDirectory` in settings.
- Auto memory is **machine-local**: not synced to other computers.
- Memory is **context, not enforcement.** Claude reads it and tries to follow
  it; to *block* an action whatever Claude decides, use a hook.
- Every line costs context in every session, so keep CLAUDE.md short
  (the docs suggest under 200 lines) and move rarely needed instructions
  into skills, which load only when used.

## 3. The prompt cache

Processing a long prompt is expensive. But turn after turn, most of it is
**the same**: the instructions, the tools, the earlier messages. The prompt
cache lets the API skip re-processing a prefix it has just seen.

- **Prefix, exact match:** the prompt is read in order, tools → system →
  messages. A request hits the cache only for the part that is 100%
  identical from the start. Change something early (the tools, for
  example) and everything after it is processed again.
- **Lifetime:** 5 minutes by default, refreshed free on each hit. A 1-hour
  lifetime is available at a higher write price. In Claude Code it's an hour
  on a subscription, and 5 minutes by default on an API key.
- **Price** (relative to normal input tokens):

  | | multiplier |
  | --- | --- |
  | writing to the 5-minute cache | 1.25× |
  | writing to the 1-hour cache | 2× |
  | reading from the cache | 0.1× in general; **0.05×** on Opus 5.5 and Sonnet 5.5; 0.025× on Fable 5.1 |

- **Minimum size:** prompts shorter than the model's minimum (512 tokens on
  the current models) aren't cached, silently.
- **It never changes the answer.** The docs: the response is identical to
  what you'd get without caching.
- **Private:** caches are never shared between organizations.

So a long session is affordable because each turn re-reads the history at
a small fraction of the price. The first message after a break longer than
the lifetime is a *cache miss*: the whole context is processed at full
price again.

## 4. One turn, end to end

```text
you type a message
   │
   ▼
Claude Code builds the request
   tools ─ system prompt ─ CLAUDE.md + MEMORY.md ─ earlier messages ─ your new message
   └──────────── same as last turn: cache HIT (cheap) ────────────┘   └ new: full price ┘
   │
   ▼
model answers, maybe calls tools ──► tool results appended ──► next request (cache hit again)
   │
   ▼
context near the limit? ──► compaction: history replaced by a summary (cache rebuilt once)
   │
   ▼
Claude learned something lasting? ──► writes a memory file ──► loaded next session
```

## 5. Python analogies

| Concept | Python analogy |
| --- | --- |
| context window | the arguments of one function call: `answer(everything_so_far)`; nothing survives the call |
| memory | a file you write and read back: `Path("notes.md").write_text(...)` next session `read_text()` |
| prompt cache | `functools.lru_cache` with a timeout: saved work for identical input, same result, expires |
| compaction | replacing a long list with a summary because it won't fit: `history = [summarise(history)]` |

## 6. Found live

In the session that wrote this guide:

- **Compaction happened.** The conversation grew past the window; it carried on
  from a summary, and some files had to be re-read because their contents
  were no longer in context.
- **Memory carried rules across sessions.** A preference stated once ("never
  write outputs to hidden temporary folders") was saved as a memory file,
  and later sessions followed it without being told again.
- **A planned folder move would have lost memory.** The project wasn't a git
  repository, so its memory folder name came from the folder path. The move
  plan was changed to copy the memory folder to the new name.
- **An earlier explanation was wrong and was corrected:** cache reads were
  first described as "about 10% of the price"; the docs say 5% for the model
  in use (Opus 5.5).

## 7. Exercises

1. Run `/context` at the start of a session and again after reading a few files. What grew?
2. Open `~/.claude/projects/` and find your project's `memory/MEMORY.md`. Which lines would you delete?
3. Start a session, wait over the cache lifetime, send a message, then run `/usage`. Find the cache miss in the `Prompt cache` line.

**Self-check:** why does moving a project folder change its auto memory,
but not its git history?

## References

### Official

- Claude Code docs: [How Claude remembers your project (memory)](https://code.claude.com/docs/en/memory) ✔ (200 lines / 25 KB; path from the git repo; machine-local; `autoMemoryDirectory`)
- Claude Code docs: [Manage costs effectively](https://code.claude.com/docs/en/costs) ✔ (`/compact`, `/clear`, cache lifetime per plan, why usage climbs)
- Claude Code docs: [Prompt caching in Claude Code](https://code.claude.com/docs/en/prompt-caching)
- Claude API docs: [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) ✔ (prefix order, exact match, lifetimes, multipliers, minimums, no effect on output, isolation)
- Claude API docs: [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- Python: [functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)

### Further learning

- Claude API docs: [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Claude Code docs: [Skills](https://code.claude.com/docs/en/skills) (keep CLAUDE.md small by moving workflows into skills)
