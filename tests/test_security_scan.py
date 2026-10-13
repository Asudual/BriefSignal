"""Regression checks for the shell scanner using synthetic values only."""

import shutil
import subprocess
from pathlib import Path

import pytest


BASH = shutil.which("bash")
GIT = shutil.which("git")
pytestmark = pytest.mark.skipif(not BASH or not GIT, reason="bash and git required")
SCANNER = Path(__file__).resolve().parents[1] / "scripts" / "security_scan.sh"


@pytest.fixture
def scan_repo(tmp_path):
    subprocess.run([GIT, "init", "-q", str(tmp_path)], check=True)
    scanner = tmp_path / "scripts" / "security_scan.sh"
    scanner.parent.mkdir()
    scanner.write_bytes(SCANNER.read_bytes())
    return tmp_path, scanner


def run_scan(scan_repo, *args):
    root, scanner = scan_repo
    return subprocess.run(
        [BASH, scanner.as_posix(), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


@pytest.mark.parametrize(
    "value",
    [
        "Bearer " + "test" * 10,
        "ab12" * 8,
        "qqbot:c2c:" + "TEST" * 8,
        "/root/" + ".openclaw/workspace",
    ],
)
def test_detects_values_without_printing_them(scan_repo, value):
    root, _ = scan_repo
    (root / "sample.txt").write_text(value, encoding="utf-8")
    result = run_scan(scan_repo)
    assert result.returncode == 1
    assert "sample.txt:1" in result.stdout
    assert value not in result.stdout + result.stderr


def test_scans_its_own_source(scan_repo):
    _, scanner = scan_repo
    with scanner.open("a", encoding="utf-8") as output:
        output.write("\n# " + "cd34" * 8 + "\n")
    result = run_scan(scan_repo)
    assert result.returncode == 1
    assert "scripts/security_scan.sh:" in result.stdout


def test_scans_skills_directory(scan_repo):
    root, _ = scan_repo
    (root / "skills").mkdir()
    (root / "skills" / "sample.md").write_text("ef56" * 8, encoding="utf-8")
    assert run_scan(scan_repo).returncode == 1


def test_allows_placeholders_and_ignores_git_metadata(scan_repo):
    root, _ = scan_repo
    (root / "example.txt").write_text(
        "Bearer <YOUR_TOKEN>\nqqbot:c2c:<YOUR_TARGET_ID>\n", encoding="utf-8"
    )
    (root / ".git" / "test-data").write_text("ab12" * 8, encoding="utf-8")
    assert run_scan(scan_repo).returncode == 0


def test_scan_error_is_not_reported_as_clean(scan_repo):
    result = run_scan(scan_repo, "missing-directory")
    assert result.returncode == 1
    assert "Could not complete scan" in result.stdout


def test_ignores_generated_test_cache(scan_repo):
    root, _ = scan_repo
    (root / ".pytest_cache").mkdir()
    (root / ".pytest_cache" / "nodeids").write_text("ab12" * 8, encoding="utf-8")
    assert run_scan(scan_repo).returncode == 0


def test_scan_path_is_not_shell_code(scan_repo):
    root, _ = scan_repo
    directory = "with space'; touch UNEXPECTED; '"
    (root / directory).mkdir()
    (root / directory / "sample.txt").write_text("ab12" * 8, encoding="utf-8")
    assert run_scan(scan_repo, directory).returncode == 1
    assert not (root / "UNEXPECTED").exists()
