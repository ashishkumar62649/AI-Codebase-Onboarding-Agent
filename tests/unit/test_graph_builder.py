"""Tests for graph_builder.py."""

from fcode.contracts import (
    Confidence,
    GraphNodeType,
    GraphRelation,
    HttpMethod,
    ParsedFile,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    SymbolType,
)
from fcode.graph.graph_builder import build_graph


def _file(path, symbols=None, imports=None, routes=None):
    return ParsedFile(
        file_path=path,
        symbols=tuple(symbols or []),
        imports=tuple(imports or []),
        routes=tuple(routes or []),
    )


def _sym(name, stype, line=1):
    return ParsedSymbol(
        name=name,
        symbol_type=stype,
        start_line=line,
        end_line=line + 5,
        confidence=Confidence.EXTRACTED,
    )


def _imp(module_name, line=1):
    return ParsedImport(
        module_name=module_name,
        imported_names=(module_name,),
        line_number=line,
        confidence=Confidence.EXTRACTED,
    )


def _route(method, path, handler, line=1):
    return ParsedRoute(
        route_id=f"route:{method}:{path}:file:{line}",
        route_path=path,
        method=method,
        handler_function=handler,
        start_line=line,
        confidence=Confidence.EXTRACTED,
    )


def test_file_node():
    pf = _file("app/main.py")
    result = build_graph([pf])
    assert result.node_count >= 1


def test_function_node():
    pf = _file("app/main.py", symbols=[_sym("hello", SymbolType.FUNCTION)])
    result = build_graph([pf])
    assert result.node_count >= 2
    assert result.edge_count >= 1


def test_class_node():
    pf = _file("app/main.py", symbols=[_sym("MyClass", SymbolType.CLASS)])
    result = build_graph([pf])
    assert result.node_count >= 2


def test_import_node():
    pf = _file("app/main.py", imports=[_imp("os")])
    result = build_graph([pf])
    assert result.node_count >= 2
    assert result.edge_count >= 1


def test_route_node():
    pf = _file("app/routes.py", routes=[_route(HttpMethod.GET, "/users", "get_users")])
    result = build_graph([pf])
    assert result.node_count >= 2
    assert result.edge_count >= 1


def test_deterministic_ordering():
    pf1 = _file("aa.py", symbols=[_sym("a", SymbolType.FUNCTION)])
    pf2 = _file("bb.py", symbols=[_sym("b", SymbolType.FUNCTION)])
    result = build_graph([pf1, pf2])
    assert result.node_count == 4


def test_empty_result():
    result = build_graph([])
    assert result.node_count == 0
    assert result.edge_count == 0


def test_node_types():
    pf = _file("app/main.py", symbols=[_sym("foo", SymbolType.FUNCTION)])
    result = build_graph([pf])
    nodes_by_type = {n.node_type for n in result.nodes}
    assert GraphNodeType.FILE in nodes_by_type
    assert GraphNodeType.FUNCTION in nodes_by_type


def test_edges():
    pf = _file("app/main.py", symbols=[_sym("foo", SymbolType.FUNCTION)])
    result = build_graph([pf])
    assert any(e.relation == GraphRelation.DEFINES for e in result.edges)
