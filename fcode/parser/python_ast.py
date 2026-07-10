"""Python AST — parse a Python source file into its AST."""

import ast
from typing import Optional

from fcode.contracts import ParseStatus, ParsedFile, ParsedImport, ParsedRoute, ParsedSymbol, ScannedFile, SymbolType, HttpMethod, Confidence
from fcode.parser.symbol_extractor import extract_symbols
from fcode.parser.import_extractor import extract_imports
from fcode.parser.route_detector import extract_routes


def parse_python_file(file: ScannedFile) -> ParsedFile:
    if file.is_binary or not file.safe_content.strip():
        return ParsedFile(
            file_path=file.file_path,
            file_type=file.file_type,
            status=ParseStatus.NOT_APPLICABLE,
        )

    try:
        tree = ast.parse(file.safe_content, filename=file.file_path)
    except SyntaxError as exc:
        error_msg = f"{exc.msg} at line {exc.lineno}"
        return ParsedFile(
            file_path=file.file_path,
            file_type=file.file_type,
            status=ParseStatus.ERROR,
            errors=[error_msg],
        )

    symbols = list(extract_symbols(tree, file.file_path))
    imports = list(extract_imports(tree, file.file_path))
    routes = list(extract_routes(tree, file.file_path))

    return ParsedFile(
        file_path=file.file_path,
        file_type=file.file_type,
        status=ParseStatus.PARSED,
        symbols=symbols,
        imports=imports,
        routes=routes,
    )
