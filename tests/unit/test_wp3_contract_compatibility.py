"""Contract compatibility tests — verify WP3 modules satisfy canonical contracts."""

from fcode.contracts import (
    ChunkType,
    Confidence,
    FileType,
    GraphNodeType,
    GraphRelation,
    HttpMethod,
    ParseStatus,
    SymbolType,
)
from fcode.contracts import (
    GraphBuildResult,
    GraphEdgeInput,
    GraphNodeInput,
    ParsedFile,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ScanResult,
    ScannedFile,
    SkippedFileDiagnostic,
)


class TestEnumsAreCanonical:
    def test_no_stale_enums(self):
        members = {e.name for e in FileType}
        assert "PYTHON" not in members
        assert "MARKDOWN" not in members
        assert "FAILED" not in {e.name for e in ParseStatus}
        assert "SKIPPED" not in {e.name for e in ParseStatus}
        assert "SYMBOL" not in {e.name for e in ChunkType}
        assert "CHUNK" not in {e.name for e in GraphNodeType}
        assert "CONTAINS" not in {e.name for e in GraphRelation}
        assert "USES" not in {e.name for e in GraphRelation}

    def test_file_type_has_source_test_config_doc(self):
        assert FileType.SOURCE.value == "source"
        assert FileType.TEST.value == "test"
        assert FileType.CONFIG.value == "config"
        assert FileType.DOC.value == "doc"

    def test_parse_status_has_pending_parsed_error_not_applicable(self):
        assert ParseStatus.PENDING.value == "pending"
        assert ParseStatus.PARSED.value == "parsed"
        assert ParseStatus.ERROR.value == "error"
        assert ParseStatus.NOT_APPLICABLE.value == "not_applicable"

    def test_symbol_type_no_method(self):
        assert SymbolType.FUNCTION.value == "function"
        assert SymbolType.CLASS.value == "class"
        assert SymbolType.ROUTE.value == "route"
        assert SymbolType.VARIABLE.value == "variable"

    def test_graph_node_types(self):
        assert GraphNodeType.FILE.value == "file"
        assert GraphNodeType.FUNCTION.value == "function"
        assert GraphNodeType.CLASS.value == "class"
        assert GraphNodeType.METHOD.value == "method"
        assert GraphNodeType.ROUTE.value == "route"
        assert GraphNodeType.IMPORT.value == "import"
        assert GraphNodeType.TEST.value == "test"

    def test_graph_relations(self):
        assert GraphRelation.DEFINES.value == "defines"
        assert GraphRelation.IMPORTS.value == "imports"
        assert GraphRelation.INHERITS.value == "inherits"
        assert GraphRelation.CALLS.value == "calls"
        assert GraphRelation.TESTS.value == "tests"
        assert GraphRelation.HANDLES_ROUTE.value == "handles_route"

    def test_http_methods(self):
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.DELETE.value == "DELETE"
        assert HttpMethod.PATCH.value == "PATCH"

    def test_confidence_values(self):
        assert Confidence.EXTRACTED.value == "EXTRACTED"
        assert Confidence.INFERRED.value == "INFERRED"
        assert Confidence.AMBIGUOUS.value == "AMBIGUOUS"


class TestCanonicalFieldNames:
    def test_scanned_file_has_required_fields(self):
        f = ScannedFile(
            file_path="test.py",
            file_type=FileType.SOURCE,
            size_bytes=100,
            is_binary=False,
            safe_content="x = 1\n",
            content_hash="abc",
        )
        assert f.file_path == "test.py"
        assert f.file_type == FileType.SOURCE
        assert f.size_bytes == 100
        assert f.is_binary is False
        assert f.safe_content == "x = 1\n"
        assert f.content_hash == "abc"

    def test_scan_result_has_lists(self):
        r = ScanResult(
            files=[],
            skipped=[],
            total_count=0,
            total_bytes=0,
        )
        assert isinstance(r.files, list)
        assert isinstance(r.skipped, list)

    def test_parsed_file_parse_status(self):
        pf = ParsedFile(file_path="m.py")
        assert pf.file_type == FileType.SOURCE
        assert pf.status == ParseStatus.PENDING

    def test_parsed_symbol_has_start_line(self):
        s = ParsedSymbol(
            name="foo",
            symbol_type=SymbolType.FUNCTION,
            start_line=10,
            end_line=15,
            confidence=Confidence.EXTRACTED,
        )
        assert s.start_line == 10

    def test_parsed_import_has_module_name_and_imported_names(self):
        i = ParsedImport(
            module_name="os",
            imported_names=("path",),
            line_number=1,
            confidence=Confidence.EXTRACTED,
        )
        assert i.module_name == "os"
        assert i.imported_names == ("path",)

    def test_parsed_route_has_route_path_and_handler_function(self):
        r = ParsedRoute(
            route_id="route:GET:/users:m.py:1",
            route_path="/users",
            method=HttpMethod.GET,
            handler_function="list_users",
            start_line=1,
            confidence=Confidence.EXTRACTED,
        )
        assert r.route_path == "/users"
        assert r.handler_function == "list_users"

    def test_graph_build_result_has_nodes_and_edges(self):
        r = GraphBuildResult(
            nodes=[],
            edges=[],
            node_count=0,
            edge_count=0,
        )
        assert r.nodes == []
        assert r.edges == []

    def test_graph_node_input_has_node_id(self):
        n = GraphNodeInput(
            node_id="file:test.py",
            node_type=GraphNodeType.FILE,
            label="test.py",
            source_file="test.py",
            confidence=Confidence.EXTRACTED,
        )
        assert n.node_id == "file:test.py"

    def test_graph_edge_input_has_source_target_relation(self):
        e = GraphEdgeInput(
            source_node_id="file:test.py",
            target_node_id="func:foo",
            relation=GraphRelation.DEFINES,
            confidence=Confidence.EXTRACTED,
        )
        assert e.source_node_id == "file:test.py"
        assert e.target_node_id == "func:foo"
        assert e.relation == GraphRelation.DEFINES

    def test_skipped_file_diagnostic_has_reason(self):
        d = SkippedFileDiagnostic(
            file_path="big.bin",
            reason="file_skipped",
            details="Too large",
        )
        assert d.reason == "file_skipped"
        assert d.details == "Too large"

    def test_route_id_format(self):
        r = ParsedRoute(
            route_id="route:GET:/users:m.py:1",
            route_path="/users",
            method=HttpMethod.GET,
            handler_function="list_users",
            start_line=1,
            confidence=Confidence.EXTRACTED,
        )
        parts = r.route_id.split(":")
        assert parts[0] == "route"
        assert parts[1] == "GET"
        assert parts[2] == "/users"
