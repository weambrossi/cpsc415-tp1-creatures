"""No-key checks on the repository itself: the rules every pull request must keep."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = re.compile(r"sk-or-v1-[0-9a-f]{20,}")   # a real key, not the "sk-or-v1-..." placeholder


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines()]


def test_no_api_key_in_tracked_files():
    for path in tracked_files():
        if path.suffix in {".png", ".jpg", ".jpeg", ".webp"} or not path.is_file():
            continue
        assert not KEY.search(path.read_text(errors="ignore")), f"API key in {path.name}"


def test_key_pattern_catches_a_real_key_and_skips_the_placeholder():
    assert KEY.search("sk-or-v1-" + "0123456789abcdef" * 4)
    assert not KEY.search("sk-or-v1-...")


def test_secrets_are_ignored():
    names = [p.name for p in tracked_files()]
    assert ".env" not in names
    assert "settings.local.json" not in names


def test_every_requirement_is_named_in_spec():
    spec = (ROOT / "spec.md").read_text().lower()
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        package = line.split("==")[0].strip().lower()
        if package:
            assert f"`{package}`" in spec, f"{package} is in requirements.txt but not in spec.md"


def test_guard_is_installed():
    assert (ROOT / ".claude/hooks/guard.py").is_file()
    assert "guard.py" in (ROOT / ".claude/settings.json").read_text()
