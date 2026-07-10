"""Symbol extraction — extract function, class, and method symbols from AST."""

import ast
from typing import Generator

from fcode.contracts import Confidence, ParsedSymbol, SymbolType


def extract_symbols(tree: ast.AST, file_path: str) -> Generator[ParsedSymbol, None, None]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            end_lineno = getattr(node, "end_lineno", node.lineno) or node.lineno
            yield ParsedSymbol(
                symbol_type=SymbolType.FUNCTION,
                name=node.name,
                start_line=node.lineno,
                end_line=end_lineno,
                docstring=ast.get_docstring(node),
                confidence=Confidence.EXTRACTED,
            )
        elif isinstance(node, ast.AsyncFunctionDef):
            end_lineno = getattr(node, "end_lineno", node.lineno) or node.lineno
            yield ParsedSymbol(
                symbol_type=SymbolType.FUNCTION,
                name=node.name,
                start_line=node.lineno,
                end_line=end_lineno,
                docstring=ast.get_docstring(node),
                confidence=Confidence.EXTRACTED,
            )
        elif isinstance(node, ast.ClassDef):
            end_lineno = getattr(node, "end_lineno", node.lineno) or node.lineno
            yield ParsedSymbol(
                symbol_type=SymbolType.CLASS,
                name=node.name,
                start_line=node.lineno,
                end_line=end_lineno,
                docstring=ast.get_docstring(node),
                confidence=Confidence.EXTRACTED,
            )
