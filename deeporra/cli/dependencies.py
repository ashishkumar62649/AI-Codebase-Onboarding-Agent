"""Lazy production composition for one CLI invocation."""

from pathlib import Path

from deeporra.chunking import Chunker
from deeporra.config.settings import CONFIG_FILE_NAME, load_config
from deeporra.contracts import DeepOrraConfig
from deeporra.embeddings import EmbeddingEncoder
from deeporra.graph.graph_builder import build
from deeporra.indexing import IndexService
from deeporra.indexing.status_reader import ActiveStatusReader
from deeporra.parser.python_ast import parse
from deeporra.scanner.file_scanner import scan


class _Scanner:
    def scan(self, repo, config):
        return scan(repo, config)


class _Parser:
    def parse(self, file):
        return parse(file)


class _GraphBuilder:
    def build(self, parsed_files):
        return build(parsed_files)


def resolve_config(repo_path: str) -> DeepOrraConfig:
    path = Path(repo_path).resolve()
    if not path.is_dir():
        raise ValueError("Repository path is unavailable.")
    if (path / CONFIG_FILE_NAME).is_file():
        return load_config(str(path))
    return DeepOrraConfig(repo_path=str(path))


def create_index_service(config: DeepOrraConfig, *, for_status: bool = False) -> IndexService:
    return IndexService(
        _Scanner(),
        _Parser(),
        Chunker(),
        encoder=None if for_status else EmbeddingEncoder(),
        graph_builder=None if for_status else _GraphBuilder(),
        status_reader=ActiveStatusReader(config.repo_path),
    )
