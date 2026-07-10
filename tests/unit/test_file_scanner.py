"""Tests for file_scanner.py."""

import os
import tempfile

from fcode.contracts import FCodeConfig, FileType, RepoInput
from fcode.scanner.file_scanner import scan_repository


def _cfg():
    return FCodeConfig()


def _repo(tmp):
    return RepoInput(repo_path=tmp)


def test_invalid_path():
    result = scan_repository(RepoInput(repo_path="/nonexistent_path_xyz"), _cfg())
    assert result.total_count == 0


def test_empty_repository():
    with tempfile.TemporaryDirectory() as tmp:
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 0


def test_python_source():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1
        assert result.files[0].file_type == FileType.SOURCE


def test_test_classification():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "test_main.py"), "w") as f:
            f.write("def test_x(): pass\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1
        assert result.files[0].file_type == FileType.TEST


def test_markdown_doc():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "README.md"), "w") as f:
            f.write("# Title\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1
        assert result.files[0].file_type == FileType.DOC


def test_config_file():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.json"), "w") as f:
            f.write('{"key": "val"}\n')
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1
        assert result.files[0].file_type == FileType.CONFIG


def test_oversized_file():
    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "big.py")
        with open(fpath, "wb") as f:
            f.write(b"x\n" * (2 * 1024 * 1024))
        with open(os.path.join(tmp, "small.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1
        skipped_reasons = [s.reason for s in result.skipped]
        assert "file_skipped" in skipped_reasons


def test_binary_file():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "img.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
        with open(os.path.join(tmp, "app.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 2
        binary = [f for f in result.files if f.is_binary]
        assert len(binary) >= 1


def test_env_file_excluded():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".env"), "w") as f:
            f.write("API_KEY=secret\n")
        with open(os.path.join(tmp, "app.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1


def test_gitignore_respected():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".gitignore"), "w") as f:
            f.write("build/\n*.log\n")
        os.makedirs(os.path.join(tmp, "build"), exist_ok=True)
        with open(os.path.join(tmp, "build", "out.o"), "w") as f:
            f.write("data")
        with open(os.path.join(tmp, "app.log"), "w") as f:
            f.write("error")
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 2
        assert any("ignored_by_rules" in s.reason for s in result.skipped)


def test_fcode_dir_excluded():
    with tempfile.TemporaryDirectory() as tmp:
        fcode = os.path.join(tmp, ".fcode")
        os.makedirs(fcode)
        with open(os.path.join(fcode, "config.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1


def test_content_hash():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "a.py"), "w") as f:
            f.write("x = 1\n")
        result = scan_repository(_repo(tmp), _cfg())
        assert len(result.files[0].content_hash) == 64


def test_secret_redacted_in_content():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "config.py"), "w") as f:
            f.write('API_KEY="sk_test_abcdefghijklmnopqrstuvwxyz"\n')
        result = scan_repository(_repo(tmp), _cfg())
        assert result.total_count == 1
        assert "[REDACTED]" in result.files[0].safe_content
