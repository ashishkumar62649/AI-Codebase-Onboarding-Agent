"""Tests for symbol_extractor.py."""

import ast
from fcode.parser.symbol_extractor import extract_symbols
from fcode.contracts import SymbolType


def test_function():
    code = "def hello():\n    pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    assert len(syms) == 1
    assert syms[0].name == "hello"
    assert syms[0].symbol_type == SymbolType.FUNCTION


def test_async_function():
    code = "async def fetch():\n    pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    assert len(syms) == 1
    assert syms[0].symbol_type == SymbolType.FUNCTION


def test_class():
    code = "class MyClass:\n    pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    assert len(syms) == 1
    assert syms[0].name == "MyClass"
    assert syms[0].symbol_type == SymbolType.CLASS


def test_nested_function():
    code = "def outer():\n    def inner():\n        pass\n    pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    assert len(syms) == 2
    names = {s.name for s in syms}
    assert names == {"outer", "inner"}


def test_duplicate_names():
    code = "def foo(): pass\ndef foo(x): pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    foos = [s for s in syms if s.name == "foo"]
    assert len(foos) == 2


def test_docstring():
    code = 'def foo():\n    """Do stuff."""\n    pass\n'
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    assert syms[0].docstring == "Do stuff."


def test_empty_module():
    tree = ast.parse("")
    syms = list(extract_symbols(tree, "module.py"))
    assert syms == []


def test_start_line():
    code = "def foo():\n    pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    assert syms[0].start_line == 1


def test_deterministic_ordering():
    code = "def b(): pass\ndef a(): pass\n"
    tree = ast.parse(code)
    syms = list(extract_symbols(tree, "module.py"))
    names = [s.name for s in syms]
    assert names == ["b", "a"]
