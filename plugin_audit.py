"""List everything in a Claude Code plugin that can run code, before you install it.

Read-only: it parses JSON and lists files. It never runs, imports or
downloads anything from the plugin, because the plugin is untrusted input.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

MAX_JSON_BYTES = 1_000_000  # a real manifest is a few KB; refuse anything huge
MAX_FILES = 20_000          # stop walking a folder that is suspiciously large
LOOPBACK = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class Finding:
    level: str   # "runs-code", "warning" or "info"
    kind: str    # hook, mcp, lsp, monitor, bin, path, url, ...
    where: str   # file inside the plugin
    detail: str


def read_json(path: Path) -> object:
    """Parse one JSON file, refusing oversized input. Raises ValueError."""
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"{path.name} is larger than {MAX_JSON_BYTES} bytes")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def inside(root: Path, rel: str) -> Path | None:
    """Resolve a manifest path; None if it escapes the plugin root (path traversal)."""
    target = (root / rel).resolve()
    return target if target.is_relative_to(root.resolve()) else None


def hook_findings(hooks: object, where: str) -> list[Finding]:
    """Each command a hooks object would run. `hooks` is {event: [{matcher, hooks: [...]}]}."""
    out: list[Finding] = []
    if not isinstance(hooks, dict):
        return [Finding("warning", "hook", where, "hooks is not an object")]
    for event, groups in hooks.items():
        for group in groups if isinstance(groups, list) else []:
            matcher = group.get("matcher", "*") if isinstance(group, dict) else "?"
            handlers = group.get("hooks", []) if isinstance(group, dict) else []
            for h in handlers if isinstance(handlers, list) else []:
                if not isinstance(h, dict):
                    continue
                what = h.get("command") or h.get("url") or h.get("prompt") or "?"
                args = " ".join(map(str, h.get("args", []))) if isinstance(h.get("args"), list) else ""
                out.append(Finding("runs-code", "hook", where,
                                   f"{event} [{matcher}] {h.get('type', '?')}: {what} {args}".rstrip()))
    return out


def url_finding(url: str, where: str, kind: str) -> Finding:
    host = urlparse(url).hostname or ""
    if url.startswith(("http://", "ws://")) and host not in LOOPBACK:
        return Finding("warning", kind, where, f"unencrypted remote URL: {url}")
    return Finding("info", kind, where, f"connects to {url}")


def server_findings(servers: object, where: str, kind: str) -> list[Finding]:
    """MCP or LSP servers: a `command` is a process on your machine, a `url` is a remote service."""
    if not isinstance(servers, dict):
        return [Finding("warning", kind, where, f"{kind} config is not an object")]
    servers = servers.get("mcpServers", servers)  # .mcp.json may wrap the map
    out: list[Finding] = []
    for name, cfg in servers.items() if isinstance(servers, dict) else []:
        if not isinstance(cfg, dict):
            continue
        if "command" in cfg:
            args = " ".join(map(str, cfg.get("args", []))) if isinstance(cfg.get("args"), list) else ""
            out.append(Finding("runs-code", kind, where, f"{name}: {cfg['command']} {args}".rstrip()))
        if "url" in cfg:
            out.append(url_finding(str(cfg["url"]), where, kind))
        if "headersHelper" in cfg:
            out.append(Finding("runs-code", kind, where, f"{name} headersHelper: {cfg['headersHelper']}"))
    return out


def component_files(root: Path, manifest: dict, key: str, default: str) -> list[Path]:
    """The JSON files a component key points at, plus its default file. Inline objects are returned as-is by the caller."""
    paths = [root / default] if (root / default).is_file() else []
    value = manifest.get(key)
    for item in value if isinstance(value, list) else [value]:
        if isinstance(item, str) and item.endswith(".json"):
            resolved = inside(root, item)
            if resolved is not None and resolved.is_file():
                paths.append(resolved)
    return paths


def audit(root: Path) -> list[Finding]:
    """Everything in the plugin at `root` that runs code or deserves a second look."""
    root = root.resolve()
    out: list[Finding] = []
    manifest: dict = {}
    manifest_path = root / ".claude-plugin" / "plugin.json"
    if manifest_path.is_file():
        try:
            loaded = read_json(manifest_path)
            manifest = loaded if isinstance(loaded, dict) else {}
        except (ValueError, OSError) as e:
            return [Finding("warning", "manifest", "plugin.json", f"unreadable: {e}")]

    # Paths in the manifest must stay inside the plugin (Claude Code refuses them too).
    for key, value in manifest.items():
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, str) and item.startswith(("./", "../", "/")) and inside(root, item) is None:
                out.append(Finding("warning", "path", "plugin.json", f"{key} escapes the plugin root: {item}"))

    def rel(p: Path) -> str:
        return p.relative_to(root).as_posix()

    for f in component_files(root, manifest, "hooks", "hooks/hooks.json"):
        try:
            out += hook_findings(read_json(f).get("hooks", {}), rel(f))  # files wrap the map in "hooks"
        except (ValueError, OSError, AttributeError) as e:
            out.append(Finding("warning", "hook", rel(f), f"unreadable: {e}"))
    for item in manifest.get("hooks", []) if isinstance(manifest.get("hooks"), list) else [manifest.get("hooks")]:
        if isinstance(item, dict):
            out += hook_findings(item, "plugin.json (inline)")

    for key, default, kind in (("mcpServers", ".mcp.json", "mcp"), ("lspServers", ".lsp.json", "lsp")):
        for f in component_files(root, manifest, key, default):
            try:
                out += server_findings(read_json(f), rel(f), kind)
            except (ValueError, OSError) as e:
                out.append(Finding("warning", kind, rel(f), f"unreadable: {e}"))
        value = manifest.get(key)
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, dict):
                out += server_findings(item, "plugin.json (inline)", kind)
            elif isinstance(item, str) and item.endswith((".mcpb", ".dxt")):
                out.append(Finding("runs-code", kind, "plugin.json", f"bundle (code you can't read here): {item}"))

    monitors = manifest.get("experimental", {}).get("monitors") if isinstance(manifest.get("experimental"), dict) else None
    monitor_file = root / "monitors" / "monitors.json"
    if monitors is None and monitor_file.is_file():
        try:
            monitors = read_json(monitor_file)
        except (ValueError, OSError) as e:
            out.append(Finding("warning", "monitor", rel(monitor_file), f"unreadable: {e}"))
    for m in monitors if isinstance(monitors, list) else []:
        if isinstance(m, dict):
            out.append(Finding("runs-code", "monitor", "monitors", f"{m.get('name', '?')}: {m.get('command', '?')}"))

    # Walk the tree once: bin/ executables, symlinks that leave the plugin, and file counts.
    counted = 0
    for p in sorted(root.rglob("*")):
        counted += 1
        if counted > MAX_FILES:
            out.append(Finding("warning", "size", ".", f"more than {MAX_FILES} files; stopped walking"))
            break
        if ".git" in p.relative_to(root).parts:
            continue
        if p.is_symlink() and not p.resolve().is_relative_to(root):
            out.append(Finding("warning", "symlink", rel(p), f"points outside the plugin: {p.resolve()}"))
        elif p.is_file() and p.relative_to(root).parts[0] == "bin":
            out.append(Finding("runs-code", "bin", rel(p), "on the Bash tool's PATH while enabled"))

    skills = sorted(p.parent.name for p in root.glob("skills/*/SKILL.md"))
    if (root / "SKILL.md").is_file():
        skills.append(root.name)
    agents = sorted(p.stem for p in root.glob("agents/**/*.md"))
    commands = sorted(p.stem for p in root.glob("commands/*.md"))
    for kind, names in (("skill", skills), ("agent", agents), ("command", commands)):
        if names:
            out.append(Finding("info", kind, kind + "s/", "instructions for Claude: " + ", ".join(names)))
    return out


def report(root: Path) -> str:
    findings = audit(root)
    order = {"runs-code": 0, "warning": 1, "info": 2}
    name = root.resolve().name  # the folder; the manifest's name is better when there is one
    try:
        name = str(read_json(root / ".claude-plugin" / "plugin.json").get("name", name))
    except (ValueError, OSError, AttributeError):
        pass
    lines = [f"Plugin: {name}"]
    for f in sorted(findings, key=lambda f: (order[f.level], f.kind)):
        lines.append(f"  [{f.level:9}] {f.kind:8} {f.where}: {f.detail}")
    runs = sum(f.level == "runs-code" for f in findings)
    warns = sum(f.level == "warning" for f in findings)
    lines.append(f"{runs} thing(s) that run code, {warns} warning(s). Read each one before installing.")
    return "\n".join(lines)
