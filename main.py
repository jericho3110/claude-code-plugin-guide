"""Front door: python main.py audit <plugin-dir> | check"""

import shutil
import subprocess
import sys
from pathlib import Path

from plugin_audit import report

ROOT = Path(__file__).resolve().parent


def run(name: str, cmd: list[str]) -> bool:
    print(f"== {name}: {' '.join(cmd)}")
    ok = subprocess.run(cmd, cwd=ROOT, check=False).returncode == 0  # the exit code is the answer
    print("   PASS" if ok else "   FAIL")
    return ok


def check() -> int:
    steps = [("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])]
    for tool, cmd in (
        ("ruff", ["ruff", "check", "."]),
        ("validate", ["claude", "plugin", "validate", "--strict", "examples/marketplace"]),
        ("validate-plugin", ["claude", "plugin", "validate", "--strict", "examples/marketplace/plugins/study-notes"]),
        ("security", ["devtools", "scan"]),
        ("links", ["devtools", "links", "--offline"]),
    ):
        if shutil.which(cmd[0]):
            steps.append((tool, cmd))
        else:
            print(f"== {tool}: SKIPPED ({cmd[0]} not on PATH)")
    results = {name: run(name, cmd) for name, cmd in steps}
    print("\n" + "  ".join(f"{n}:{'ok' if ok else 'FAIL'}" for n, ok in results.items()))
    return 0 if all(results.values()) else 1


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "audit":
        target = Path(argv[1])
        if not target.is_dir():
            print(f"not a directory: {target}", file=sys.stderr)
            return 2
        print(report(target))
        return 0
    if argv == ["check"]:
        return check()
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
