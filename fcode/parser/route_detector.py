"""Route detection — detect Flask/FastAPI route decorators in AST."""

import ast
from typing import Generator

from fcode.contracts import Confidence, HttpMethod, ParsedRoute

FLASK_APP_ATTRIBUTES = {"route", "get", "post", "put", "delete", "patch"}
FASTAPI_ATTRIBUTES = {"get", "post", "put", "delete", "patch"}


def extract_routes(tree: ast.AST, file_path: str) -> Generator[ParsedRoute, None, None]:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            result = _parse_decorator(deco)
            if result:
                method, route_path = result
                route_id = f"route:{method.value}:{route_path}:{file_path}:{node.lineno}"
                yield ParsedRoute(
                    route_id=route_id,
                    route_path=route_path,
                    method=method,
                    handler_function=node.name,
                    start_line=node.lineno,
                    confidence=Confidence.EXTRACTED,
                )


def _parse_decorator(deco: ast.expr) -> tuple[HttpMethod, str] | None:
    if isinstance(deco, ast.Attribute) and deco.attr in FLASK_APP_ATTRIBUTES:
        if deco.attr == "route":
            return HttpMethod.GET, _extract_flask_route_path(deco) or "/"
        return HttpMethod(deco.attr.upper()), "/"

    if isinstance(deco, ast.Call):
        if isinstance(deco.func, ast.Attribute):
            if deco.func.attr in FLASK_APP_ATTRIBUTES:
                path = _extract_flask_route_args(deco) or "/"
                methods = _extract_flask_methods(deco)
                if deco.func.attr == "route" and methods:
                    return methods[0], path
                if deco.func.attr == "route":
                    return HttpMethod.GET, path
                return HttpMethod(deco.func.attr.upper()), path
            if deco.func.attr in FASTAPI_ATTRIBUTES:
                path = _extract_fastapi_route_args(deco) or "/"
                return HttpMethod(deco.func.attr.upper()), path

        if isinstance(deco.func, ast.Attribute) and deco.func.attr == "route" and isinstance(deco.func.value, ast.Attribute) and deco.func.value.attr == "app":
            path = _extract_flask_route_args(deco) or "/"
            methods = _extract_flask_methods(deco)
            if methods:
                return methods[0], path
            return HttpMethod.GET, path

    return None


def _extract_flask_route_path(deco: ast.Attribute) -> str | None:
    return None


def _extract_flask_route_args(deco: ast.Call) -> str | None:
    if deco.args and isinstance(deco.args[0], ast.Constant) and isinstance(deco.args[0].value, str):
        return deco.args[0].value
    return None


def _extract_flask_methods(deco: ast.Call) -> list[HttpMethod]:
    for kw in deco.keywords:
        if kw.arg == "methods" and isinstance(kw.value, ast.List):
            methods = []
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    try:
                        methods.append(HttpMethod(elt.value.upper()))
                    except ValueError:
                        pass
            return methods
    return []


def _extract_fastapi_route_args(deco: ast.Call) -> str | None:
    if deco.args and isinstance(deco.args[0], ast.Constant) and isinstance(deco.args[0].value, str):
        return deco.args[0].value
    return None
