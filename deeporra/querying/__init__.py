"""DeepOrra read-only query service — reusable internal API for MCP, dashboard, and CLI."""

from deeporra.querying.models import (
    CodeSearchResult,
    ImpactAnalysis,
    QueryValidationError,
    RelatedNode,
    RepositoryNotIndexedError,
    RepositorySummary,
    RouteRecord,
    SymbolRecord,
    to_json,
)

from deeporra.querying.service import QueryService

__all__ = [
    "QueryService",
    "RepositorySummary",
    "CodeSearchResult",
    "SymbolRecord",
    "RouteRecord",
    "RelatedNode",
    "ImpactAnalysis",
    "RepositoryNotIndexedError",
    "QueryValidationError",
    "to_json",
]
