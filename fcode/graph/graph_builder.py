"""Graph builder — build a code graph from parsed files."""

from typing import Sequence

from fcode.contracts import (
    Confidence,
    GraphBuildResult,
    GraphEdgeInput,
    GraphNodeInput,
    GraphNodeType,
    GraphRelation,
    ParsedFile,
)


def build_graph(parsed_files: Sequence[ParsedFile]) -> GraphBuildResult:
    nodes: list[GraphNodeInput] = []
    edges: list[GraphEdgeInput] = []

    for pf in parsed_files:
        file_node_id = f"file:{pf.file_path}"
        nodes.append(
            GraphNodeInput(
                node_id=file_node_id,
                node_type=GraphNodeType.FILE,
                label=pf.file_path,
                source_file=pf.file_path,
                confidence=Confidence.EXTRACTED,
            )
        )

        for sym in pf.symbols:
            symbol_node_id = f"{sym.symbol_type.value}:{pf.file_path}:{sym.name}:{sym.start_line}"
            nodes.append(
                GraphNodeInput(
                    node_id=symbol_node_id,
                    node_type=_symbol_to_node_type(sym.symbol_type),
                    label=sym.name,
                    source_file=pf.file_path,
                    source_location=f"{pf.file_path}:{sym.start_line}",
                    confidence=sym.confidence,
                )
            )
            edges.append(
                GraphEdgeInput(
                    source_node_id=file_node_id,
                    target_node_id=symbol_node_id,
                    relation=GraphRelation.DEFINES,
                    confidence=Confidence.EXTRACTED,
                )
            )

        for imp in pf.imports:
            import_node_id = f"import:{pf.file_path}:{imp.module_name}:{imp.line_number}"
            nodes.append(
                GraphNodeInput(
                    node_id=import_node_id,
                    node_type=GraphNodeType.IMPORT,
                    label=imp.module_name,
                    source_file=pf.file_path,
                    confidence=imp.confidence,
                )
            )
            edges.append(
                GraphEdgeInput(
                    source_node_id=file_node_id,
                    target_node_id=import_node_id,
                    relation=GraphRelation.IMPORTS,
                    confidence=Confidence.EXTRACTED,
                )
            )

        for route in pf.routes:
            route_node_id = route.route_id
            nodes.append(
                GraphNodeInput(
                    node_id=route_node_id,
                    node_type=GraphNodeType.ROUTE,
                    label=f"{route.method.value} {route.route_path}",
                    source_file=pf.file_path,
                    confidence=route.confidence,
                )
            )
            edges.append(
                GraphEdgeInput(
                    source_node_id=route_node_id,
                    target_node_id=file_node_id,
                    relation=GraphRelation.HANDLES_ROUTE,
                    confidence=Confidence.EXTRACTED,
                )
            )

    return GraphBuildResult(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )


def _symbol_to_node_type(st) -> GraphNodeType:
    mapping = {
        "function": GraphNodeType.FUNCTION,
        "class": GraphNodeType.CLASS,
    }
    return mapping.get(st.value, GraphNodeType.FILE)
