import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plugin_audit import MAX_JSON_BYTES, audit, report

EXAMPLE = ROOT / "examples" / "marketplace" / "plugins" / "study-notes"


def write(root: Path, rel: str, data: object) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "plugin"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def kinds(self, level):
        return sorted(f.kind for f in audit(self.root) if f.level == level)

    def test_example_plugin_runs_no_code(self):
        findings = audit(EXAMPLE)
        self.assertFalse([f for f in findings if f.level != "info"])
        self.assertIn("explain-file", report(EXAMPLE))

    def test_lists_every_kind_of_code(self):
        write(self.root, ".claude-plugin/plugin.json", {
            "name": "x",
            "mcpServers": {"inline": {"command": "node", "args": ["s.js"]}},
            "experimental": {"monitors": [{"name": "m", "command": "tail -f log", "description": "d"}]},
        })
        write(self.root, "hooks/hooks.json", {"hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "./check.sh"}]}]}})
        write(self.root, ".mcp.json", {"mcpServers": {"db": {"command": "python", "args": ["db.py"]}}})
        write(self.root, ".lsp.json", {"go": {"command": "gopls", "extensionToLanguage": {".go": "go"}}})
        write(self.root, "bin/tool", "#!/bin/sh\n")
        self.assertEqual(self.kinds("runs-code"), ["bin", "hook", "lsp", "mcp", "mcp", "monitor"])
        self.assertIn("PreToolUse [Bash] command: ./check.sh", report(self.root))

    def test_flags_unencrypted_remote_url_but_not_loopback(self):
        write(self.root, ".mcp.json", {"mcpServers": {
            "remote": {"url": "http://203.0.113.10/mcp"},
            "local": {"url": "http://127.0.0.1:8080/mcp"},
            "tls": {"url": "https://example.com/mcp"}}})
        warnings = [f.detail for f in audit(self.root) if f.level == "warning"]
        self.assertEqual(warnings, ["unencrypted remote URL: http://203.0.113.10/mcp"])

    def test_flags_path_traversal_in_manifest(self):
        write(self.root, ".claude-plugin/plugin.json", {"name": "x", "hooks": "../../evil/hooks.json"})
        write(self.root.parent, "evil/hooks.json", {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}})
        findings = audit(self.root)
        self.assertIn("path", [f.kind for f in findings if f.level == "warning"])
        self.assertNotIn("hook", [f.kind for f in findings])  # the escaped file is never read

    def test_refuses_oversized_json(self):
        write(self.root, ".claude-plugin/plugin.json", " " * (MAX_JSON_BYTES + 1) + "{}")
        self.assertIn("unreadable", audit(self.root)[0].detail)

    def test_malformed_json_is_a_warning_not_a_crash(self):
        write(self.root, "hooks/hooks.json", "{not json")
        self.assertEqual(self.kinds("warning"), ["hook"])


if __name__ == "__main__":
    unittest.main()
