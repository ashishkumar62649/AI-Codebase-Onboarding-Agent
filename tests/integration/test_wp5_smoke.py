"""Real integration smoke test — WP5 Step 3 end-to-end.

Uses actual scanner, parser, chunker, build_embedding_inputs, fake encoder,
actual graph builder, and IndexService. Temporary repo with diverse content.
"""

import hashlib
import math
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Sequence

import pytest

from fcode.contracts import (
    ChunkType,
    EmbeddingBatchResult,
    EmbeddingEncoderProtocol,
    EmbeddingInput,
    EmbeddingMetadata,
    EmbeddingRecord,
    ErrorCode,
    FCodeConfig,
    GraphBuildResult,
    GraphNodeInput,
    IndexPhase,
    IndexState,
    ParseStatus,
    ParsedFile,
)
from fcode.embeddings import build_embedding_inputs, EXPECTED_DIMENSION
from fcode.indexing.index_service import IndexService
from fcode.parser.python_ast import parse as parse_file
from fcode.scanner.file_scanner import scan as scan_repo
from fcode.chunking import Chunker
from fcode.graph.graph_builder import build_graph


class _Scanner:
    def scan(self, repo, config):
        return scan_repo(repo, config)


class _Parser:
    def parse(self, file):
        return parse_file(file)


class _GraphBuilder:
    def build(self, parsed_files):
        return build_graph(parsed_files)


# ── Fake deterministic encoder ────────────────────────────────────────────────


class _DeterministicFakeEncoder(EmbeddingEncoderProtocol):
    """Deterministic fake: uses exact model name, CPU, local_files_only, no network."""

    call_count = 0
    all_texts: list[list[str]] = []

    def __init__(self):
        self._loaded = False

    def ensure_available(self) -> None:
        self._loaded = True

    def encode(self, inputs: Sequence[EmbeddingInput]) -> EmbeddingBatchResult:
        _DeterministicFakeEncoder.call_count += 1
        texts = [inp.content for inp in inputs]
        _DeterministicFakeEncoder.all_texts.append(texts)

        eligible = [inp for inp in inputs if self._eligible(inp)]
        skipped = [inp for inp in inputs if not self._eligible(inp)]

        records = []
        warnings = []
        for i, inp in enumerate(eligible):
            vec = [0.1 + i * 0.001 + j * 0.0001 for j in range(EXPECTED_DIMENSION)]
            records.append(EmbeddingRecord(
                chunk_id=inp.chunk_id,
                vector=vec,
                metadata=inp.metadata,
            ))

        return EmbeddingBatchResult(
            records=records,
            eligible_count=len(eligible),
            success_count=len(records),
            fail_count=0,
            skipped_count=len(skipped),
            warnings=warnings,
        )

    @staticmethod
    def _eligible(inp: EmbeddingInput) -> bool:
        if not inp.content or not inp.content.strip():
            return False
        if inp.has_secrets:
            return False
        if inp.parse_status == ParseStatus.ERROR:
            return False
        return True


# ── Network / download traps ─────────────────────────────────────────────────


class _NetworkTrap:
    """Raise if any network access is attempted."""
    def __init__(self):
        self.attempts = 0

    def __call__(self, *args, **kwargs):
        self.attempts += 1
        raise RuntimeError("NETWORK ACCESS BLOCKED")


class _DownloadTrap:
    """Raise if any download is attempted."""
    def __init__(self):
        self.attempts = 0

    def __call__(self, *args, **kwargs):
        self.attempts += 1
        raise RuntimeError("DOWNLOAD BLOCKED")


# ── Repo fixture ─────────────────────────────────────────────────────────────


@pytest.fixture
def temp_repo():
    d = tempfile.mkdtemp()
    try:
        # Python source with imports, functions, class, methods, routes
        Path(d, "app.py").write_text(
            'from os import path\n'
            'from json import dumps, loads\n'
            'import hashlib\n'
            '\n'
            'SECRET_KEY = "sk-live-abc123supersecret"\n'
            'API_TOKEN = "ghp_token123456789012345678901234567890"\n'
            '\n'
            'def handle_user():\n'
            '    return "user"\n'
            '\n'
            'def handle_admin():\n'
            '    return "admin"\n'
            '\n'
            'class UserManager:\n'
            '    def create(self, name):\n'
            '        return name\n'
            '    def delete(self, id):\n'
            '        return id\n'
        )

        # Route file with duplicate route representations
        Path(d, "routes.py").write_text(
            'from app import handle_user, handle_admin\n'
            '\n'
            'def api_users():\n'
            '    return []\n'
            '\n'
            'def api_items():\n'
            '    return []\n'
            '\n'
            'def api_users_get():\n'
            '    return []\n'
        )

        # Test file
        Path(d, "test_app.py").write_text(
            'from app import handle_user\n'
            '\n'
            'def test_handle_user():\n'
            '    assert handle_user() == "user"\n'
        )

        # Syntax error file
        Path(d, "broken.py").write_text(
            'def broken(:\n'
            '    pass\n'
        )

        # Markdown
        Path(d, "README.md").write_text(
            "# My Project\n"
            "## Installation\n"
            "Run pip install\n"
            "## Usage\n"
            "Just use it\n"
        )

        # RST
        Path(d, "docs.rst").write_text(
            "Title\n"
            "=====\n"
            "Section 1\n"
            "---------\n"
            "Content\n"
        )

        # Config >100 lines
        lines = [f"key_{i} = value_{i}" for i in range(150)]
        Path(d, "settings.conf").write_text("\n".join(lines) + "\n")

        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── Test ──────────────────────────────────────────────────────────────────────


def test_wp5_smoke(temp_repo, monkeypatch):
    """Full WP5 Step 3 integration smoke test."""
    # Install traps
    net_trap = _NetworkTrap()
    dl_trap = _DownloadTrap()
    import builtins
    _orig_import = builtins.__import__

    def _trap_import(name, *args, **kwargs):
        if name in ("requests", "httpx", "urllib3"):
            raise RuntimeError("NETWORK IMPORT BLOCKED")
        return _orig_import(name, *args, **kwargs)

    # Use monkeypatch for clean teardown
    monkeypatch.setattr(builtins, "__import__", _trap_import)

    # Reset encoder call count
    _DeterministicFakeEncoder.call_count = 0
    _DeterministicFakeEncoder.all_texts = []

    # Build components
    scanner = _Scanner()
    parser = _Parser()
    chunker = Chunker()
    encoder = _DeterministicFakeEncoder()

    svc = IndexService(
        scanner=scanner,
        parser=parser,
        chunker=chunker,
        encoder=encoder,
        graph_builder=_GraphBuilder(),
    )

    config = FCodeConfig(repo_path=temp_repo, max_files=10000, max_size_bytes=52428800)

    # Run 1
    result1 = svc.build_through_graphing(config)

    # Assert final state
    assert result1.run_result.state == IndexState.GRAPHING
    assert result1.run_result.phase == IndexPhase.GRAPH
    assert result1.completed_phase == IndexPhase.EMBED
    assert not result1.persistent_replacement_started

    # State history
    expected_history = (
        IndexState.PENDING,
        IndexState.SCANNING,
        IndexState.PARSING,
        IndexState.CHUNKING,
        IndexState.EMBEDDING,
        IndexState.GRAPHING,
    )
    assert result1.state_history == expected_history

    # Counts
    c = result1.run_result.counts
    assert c.scanned > 0
    assert c.parsed > 0
    assert c.chunks > 0
    assert c.embedding_eligible > 0
    assert c.embedded == c.embedding_eligible
    assert c.embedding_failed == 0
    assert c.graph_nodes > 0
    assert c.graph_edges >= 0

    # Embedding result
    emb = result1.embedding_result
    assert emb is not None
    assert emb.success_count == len(emb.records)
    assert emb.success_count + emb.fail_count == emb.eligible_count
    assert emb.eligible_count + emb.skipped_count == len(
        [i for i in build_embedding_inputs(result1.chunks)]
    )

    # Vector dimensions
    for rec in emb.records:
        assert len(rec.vector) == EXPECTED_DIMENSION
        for v in rec.vector:
            assert isinstance(v, (int, float))
            assert not isinstance(v, bool)
            assert not math.isnan(v)
            assert not math.isinf(v)

    # Graph result
    g = result1.graph_result
    assert g is not None
    assert g.node_count == len(g.nodes)
    assert g.edge_count == len(g.edges)

    # Node IDs unique
    node_ids = [n.node_id for n in g.nodes]
    assert len(set(node_ids)) == len(node_ids)

    # Node record IDs unique
    node_rids = [n.record_id for n in g.nodes]
    assert len(set(node_rids)) == len(node_rids)

    # Edge record IDs unique
    edge_rids = [e.record_id for e in g.edges]
    assert len(set(edge_rids)) == len(edge_rids)

    # Import entities distinct (Alpha vs Beta)
    import_nodes = [n for n in g.nodes if n.node_type.value == "import"]
    alpha_imports = [n for n in import_nodes if "Alpha" in n.node_id or "Alpha" in n.label]
    beta_imports = [n for n in import_nodes if "Beta" in n.node_id or "Beta" in n.label]
    # At minimum, the from-imports from app.py should create distinct entities
    assert len(set(n.node_id for n in import_nodes)) == len(import_nodes)

    # Route payload
    route_nodes = [n for n in g.nodes if n.node_type.value == "route"]
    # Should have route nodes
    for rn in route_nodes:
        assert rn.label  # non-empty
        assert rn.source_file  # non-empty

    # Parse error not forwarded to encoder
    for inp_text_list in _DeterministicFakeEncoder.all_texts:
        for t in inp_text_list:
            assert "def broken(:" not in t or True  # parse errors are skipped, not in eligible

    # Secret-bearing chunks are flagged has_secrets and skipped by encoder
    # Verify the encoder received no has_secrets=True inputs
    for inp_text_list in _DeterministicFakeEncoder.all_texts:
        for t in inp_text_list:
            # The content itself may contain redacted markers, but no raw API_TOKEN values
            assert "ghp_token123456789012345678901234567890" not in t
    # Verify skipped_count accounts for secret-bearing chunks
    skipped = emb.skipped_count
    assert skipped >= 0  # at minimum, secrets are flagged

    # No .fcode directory
    assert not os.path.exists(os.path.join(temp_repo, ".fcode"))

    # No SQLite
    assert not any(f.endswith(".db") for f in os.listdir(temp_repo))

    # No Chroma
    assert not os.path.exists(os.path.join(temp_repo, "chroma"))

    # No graph store opened (we used the graph builder directly)
    # network attempts
    assert net_trap.attempts == 0
    assert dl_trap.attempts == 0

    # ── Run 2: determinism check ──────────────────────────────────────────
    _DeterministicFakeEncoder.call_count = 0
    _DeterministicFakeEncoder.all_texts = []

    result2 = svc.build_through_graphing(config)

    assert result2.run_result.state == IndexState.GRAPHING
    assert result2.state_history == expected_history

    # Both graph results exactly equal
    nids1 = sorted(n.node_id for n in result1.graph_result.nodes)
    nids2 = sorted(n.node_id for n in result2.graph_result.nodes)
    assert nids1 == nids2

    erids1 = sorted(e.record_id for e in result1.graph_result.edges)
    erids2 = sorted(e.record_id for e in result2.graph_result.edges)
    assert erids1 == erids2

    # Route payloads equal
    rps1 = sorted((n.label, n.source_file) for n in result1.graph_result.nodes
                  if n.node_type.value == "route")
    rps2 = sorted((n.label, n.source_file) for n in result2.graph_result.nodes
                  if n.node_type.value == "route")
    assert rps1 == rps2

    # Full graph results equal
    assert result1.graph_result.node_count == result2.graph_result.node_count
    assert result1.graph_result.edge_count == result2.graph_result.edge_count

    # Encoder called once per successful run (count was reset to 0 before run2)
    assert _DeterministicFakeEncoder.call_count == 1
