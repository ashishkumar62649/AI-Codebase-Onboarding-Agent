"""Typer-level index/status activation using the real production factory."""

import sys
import types

from typer.testing import CliRunner

from fcode.cli.main import app
from fcode.embeddings import EXPECTED_DIMENSION
from fcode.storage.chroma_store import ChromaStore


class _FakeSentenceTransformer:
    calls = []
    def __init__(self, model_name, *, device, local_files_only):
        self.calls.append((model_name, device, local_files_only))
    def get_sentence_embedding_dimension(self):
        return EXPECTED_DIMENSION
    def encode(self, texts, **_):
        return [[0.1] * EXPECTED_DIMENSION for _ in texts]


def _write(repo, term):
    (repo / "app.py").write_text(
        f"@app.get('/{term}')\ndef {term}_handler():\n    return '{term}'\n\n"
        "API_TOKEN = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text(f"# {term}\n", encoding="utf-8")


def test_cli_activates_full_index_and_active_status(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _write(repo, "alpha")
    fake = types.ModuleType("sentence_transformers")
    fake.SentenceTransformer = _FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake)
    runner = CliRunner()
    _FakeSentenceTransformer.calls.clear()

    before = runner.invoke(app, ["status", str(repo)])
    assert before.exit_code == 0 and "No active index." in before.output
    assert not (repo / ".fcode").exists()

    first = runner.invoke(app, ["index", str(repo)])
    assert first.exit_code == 0 and "Index complete." in first.output
    assert "ghp_" not in first.output
    after = runner.invoke(app, ["status", str(repo)])
    assert after.exit_code == 0 and "state=complete" in after.output
    assert "chunks=" in after.output

    _write(repo, "beta")
    original_upsert = ChromaStore.upsert_embeddings
    with monkeypatch.context() as patch:
        patch.setattr(ChromaStore, "upsert_embeddings", lambda self, *a: (_ for _ in ()).throw(RuntimeError("private failure")))
        failed = runner.invoke(app, ["index", str(repo)])
    assert failed.exit_code == 1 and "Index failed." in failed.output
    preserved = runner.invoke(app, ["status", str(repo)])
    assert preserved.exit_code == 0 and "state=complete" in preserved.output

    final = runner.invoke(app, ["index", str(repo)])
    assert final.exit_code == 0 and "Index complete." in final.output
    assert _FakeSentenceTransformer.calls == [
        ("sentence-transformers/all-MiniLM-L6-v2", "cpu", True)
    ] * 3
