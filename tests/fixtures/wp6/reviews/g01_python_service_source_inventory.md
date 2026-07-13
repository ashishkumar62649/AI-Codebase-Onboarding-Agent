# G01 Python Service Source-Derived Oracle Inventory

- Task: WP6.1B-1B — Manually derive and record the G01 `python_service` source oracle.
- Fixture ID: G01
- Fixture root: `tests/fixtures/wp6/repos/python_service`
- Existing manifest: `tests/fixtures/wp6/manifests/python_service.json`
- Review method: Manual source inspection against accepted contracts (04_DATA_MODEL.md, 05_INDEXING_AND_RETRIEVAL.md, graph_builder.py, symbol_extractor.py, import_extractor.py, route_detector.py, python_ast.py, chunker.py, file_scanner.py). No production pipeline execution.
- Production pipeline executed: NO
- Production output copied: NO
- Fixture source modified: NO
- Manifest modified: NO
- Reviewer decision: SOURCE INVENTORY COMPLETE

---

## 1. Location Confirmation

G01_FIXTURE_ROOT=tests/fixtures/wp6/repos/python_service
G01_CURRENT_MANIFEST=tests/fixtures/wp6/manifests/python_service.json
G01_REVIEW_OUTPUT=tests/fixtures/wp6/reviews/g01_python_service_source_inventory.md

- Current manifest is outside the indexed fixture root (manifests/ vs repos/): CONFIRMED.
- New review document is outside the indexed fixture root (reviews/ vs repos/): CONFIRMED.
- Neither file can affect scanner or chunk counts: CONFIRMED (no modification to fixture source).

---

## 2. File Inventory

| Relative path | File type | Logical lines | Expected scanned | Expected parsed status | Purpose |
|---|---|---:|---|---|---|
| guide.rst | RST doc | 7 | YES | not_applicable | RST documentation file |
| README.md | Markdown doc | 5 | YES | not_applicable | Project README |
| service/__init__.py | Python package marker | 1 | YES | parsed | Package init, docstring only |
| service/helpers.py | Python source | 9 | YES | parsed | Helper functions |
| service/routes.py | Python source | 23 | YES | parsed | FastAPI route definitions |
| settings.toml | TOML config | 2 | YES | not_applicable | Service configuration |
| tests/TestRoutes.py | Python test | 5 | YES | parsed | Route test |

All 7 files are scanned (eligible, non-ignored, readable, not binary, not .env, within size limits). No files are excluded.

Line endings: all files use LF (Unix-style), no CRLF.

---

## 3. Parse-Status Inventory

| Path | Expected status | Language | Diagnostic category | Manual reason |
|---|---|---|---|---|
| guide.rst | not_applicable | NONE | NONE | Extension `.rst` → scanner sets `parse_status = NOT_APPLICABLE` (file_scanner.py L194). Index service parse-phase filter (L307-309) selects only `PENDING` files → guide.rst is never sent to `ast.parse()`. Final status remains `not_applicable`. |
| README.md | not_applicable | NONE | NONE | Extension `.md` → scanner sets `parse_status = NOT_APPLICABLE`. Never enters parse phase. Final status remains `not_applicable`. |
| service/__init__.py | parsed | Python | NONE | Single line `"""Golden service package."""` — valid Python module docstring, parses successfully. |
| service/helpers.py | parsed | Python | NONE | Valid Python: variable assignment, two functions (one sync, one async). No syntax errors. |
| service/routes.py | parsed | Python | NONE | Valid Python: imports, variable, class with methods, two route-decorated functions. No syntax errors. |
| settings.toml | not_applicable | NONE | NONE | Extension `.toml` → scanner sets `parse_status = NOT_APPLICABLE`. Never enters parse phase. Final status remains `not_applicable`. |
| tests/TestRoutes.py | parsed | Python | NONE | Valid Python: variable assignment `__test__ = False`, one test function with assert statement. No syntax errors. |

Parse status summary: 4 files parsed (all `.py` files), 3 files not_applicable (all non-Python files). 0 files with parse errors.

The scanner (file_scanner.py L179-194) sets `parse_status = PENDING` for `.py` files and `parse_status = NOT_APPLICABLE` for all others. The index service parse phase (index_service.py L307-309) filters candidates to `parse_status == PENDING and not is_binary`, so only Python files enter the parser. Non-Python files retain `not_applicable` throughout the pipeline — they are never sent to `ast.parse()`.

---

## 4. Symbol Inventory

### 4.1 Symbol Extractor Results (per file)

**service/helpers.py:**

| Semantic key | Kind | Qualified name | Path | Start | End | Parent | Source evidence |
|---|---|---|---|---:|---:|---|---|
| variable:helpers:DEFAULT_GREETING | variable | DEFAULT_GREETING | service/helpers.py | 1 | 1 | NONE | `DEFAULT_GREETING = "golden hello"` at line 1 — `ast.Assign` with single `ast.Name` target at module level. |
| function:helpers:normalize_name | function | normalize_name | service/helpers.py | 4 | 5 | NONE | `def normalize_name(name: str) -> str:` at line 4, body at line 5. Module-level `ast.FunctionDef`. |
| async_function:helpers:fetch_profile | function | fetch_profile | service/helpers.py | 8 | 9 | NONE | `async def fetch_profile(user_id: str) -> dict[str, str]:` at line 8, body at line 9. Module-level `ast.AsyncFunctionDef`. |

**service/routes.py:**

| Semantic key | Kind | Qualified name | Path | Start | End | Parent | Source evidence |
|---|---|---|---|---:|---:|---|---|
| variable:routes:app | variable | app | service/routes.py | 5 | 5 | NONE | `app = FastAPI()` at line 5 — `ast.Assign` with single `ast.Name` target at module level. |
| class:routes:GreetingService | class | GreetingService | service/routes.py | 8 | 14 | NONE | `class GreetingService:` at line 8. Module-level `ast.ClassDef`. End line = last method end (line 13 `_audit`). `end_lineno=14` from AST. |
| method:routes:GreetingService.greet | method | GreetingService.greet | service/routes.py | 9 | 10 | class:routes:GreetingService | `def greet(self, name: str) -> str:` at line 9, body at line 10. Method inside class. |
| method:routes:GreetingService._audit | method | GreetingService._audit | service/routes.py | 12 | 13 | class:routes:GreetingService | `def _audit(self, user_id: str) -> str:` at line 12, body at line 13. Method inside class. |
| function:routes:get_profile | function | get_profile | service/routes.py | 17 | 18 | NONE | `async def get_profile(user_id: str) -> dict[str, str]:` at line 17, body at line 18. Module-level `ast.AsyncFunctionDef`. Symbol extractor yields this as function type. |
| function:routes:create_profile | function | create_profile | service/routes.py | 22 | 23 | NONE | `def create_profile(name: str) -> dict[str, str]:` at line 22, body at line 23. Module-level `ast.FunctionDef`. |

**route_detector.py route identities (separate from manifest symbols):**

| Semantic key | Kind | Qualified name | Path | Start | End | Parent | Source evidence |
|---|---|---|---|---:|---:|---|---|
| route:GET:/profiles/{user_id}:service/routes.py:16 | route | get_profile | service/routes.py | 16 | 18 | NONE | `@app.get("/profiles/{user_id}")` decorator at line 16, handler function `get_profile` at line 17-18. `HttpMethod.GET`. Route ID: `route:GET:/profiles/{user_id}:service/routes.py:16`. |
| route:POST:/profiles:service/routes.py:21 | route | create_profile | service/routes.py | 21 | 23 | NONE | `@app.post("/profiles")` decorator at line 21, handler function `create_profile` at line 22-23. `HttpMethod.POST`. Route ID: `route:POST:/profiles:service/routes.py:21`. |

**tests/TestRoutes.py:**

| Semantic key | Kind | Qualified name | Path | Start | End | Parent | Source evidence |
|---|---|---|---|---:|---:|---|---|
| variable:tests:__test__ | variable | __test__ | tests/TestRoutes.py | 1 | 1 | NONE | `__test__ = False` at line 1 — `ast.Assign` with single `ast.Name` target at module level. |
| test:tests:test_greeting_service | function | test_greeting_service | tests/TestRoutes.py | 4 | 5 | NONE | `def test_greeting_service() -> None:` at line 4, body at line 5. Module-level `ast.FunctionDef`. |

**service/__init__.py:** No symbols (only docstring, no Assign/FunctionDef/ClassDef).

**guide.rst, README.md, settings.toml:** parse_status=not_applicable → no symbols extracted (never sent to parser).

### 4.2 Symbol Summary

The manifest symbol collection contains 11 source-level records: 3 variables, 2 helper functions, 1 class, 2 methods, 2 route-handler functions, and 1 test function. The two route identities are represented only in the manifest `routes` collection; they are not additional manifest symbols. The parser may carry route pseudo-symbols internally so route extraction and graph construction can share route IDs, but that internal representation is not copied into `symbols`.

ROUTE_HANDLER_IS_FUNCTION_SYMBOL=True
ROUTE_CREATES_SEPARATE_MANIFEST_SYMBOL=False
ROUTE_HAS_SEPARATE_ROUTE_RECORD=True
ROUTE_HAS_SEPARATE_GRAPH_NODE=True
ROUTE_CHUNK_OWNER_KIND=handler_function_symbol
CHUNK_OWNER_MUST_RESOLVE_TO_SYMBOL=True
MODULE_VARIABLES_ARE_MANIFEST_SYMBOLS=True
TEST_FUNCTION_IS_MANIFEST_SYMBOL=True
MANIFEST_SYMBOL_COUNT=11

The strict validator requires every non-null chunk owner to resolve to `symbols[].semantic_key`. Therefore route chunks are owned by `function:routes:get_profile` and `function:routes:create_profile`, not by route pseudo-symbol keys.

### 4.3 Candidate Classification

| # | Source construct | Source path | Source lines | Source kind | Manifest symbol | Manifest symbol kind | Route record | Graph node kind | Valid chunk owner | Reason |
|---:|---|---|---:|---|---|---|---|---|---|---|
| 1 | DEFAULT_GREETING | service/helpers.py | 1 | variable | YES | variable | NO | NONE | NONE | Source-level variable is retained in the manifest symbol oracle; variables are not graph nodes or chunks. |
| 2 | normalize_name | service/helpers.py | 4-5 | function | YES | function | NO | function | function:helpers:normalize_name | Ordinary helper function. |
| 3 | fetch_profile | service/helpers.py | 8-9 | async function | YES | function | NO | function | async_function:helpers:fetch_profile | Async function is represented as an ordinary function symbol. |
| 4 | GreetingService | service/routes.py | 8-14 | class | YES | class | NO | class | class:routes:GreetingService | Class symbol with separate method symbols. |
| 5 | GreetingService.greet | service/routes.py | 9-10 | method | YES | method | NO | method | method:routes:GreetingService.greet | Method symbol owned by the class. |
| 6 | GreetingService._audit | service/routes.py | 12-13 | method | YES | method | NO | method | method:routes:GreetingService._audit | Method symbol owned by the class. |
| 7 | app | service/routes.py | 5 | variable | YES | variable | NO | NONE | NONE | Source-level variable retained only in manifest symbols. |
| 8 | get_profile | service/routes.py | 17-18 | route handler function | YES | function | YES | function | function:routes:get_profile | Route handler remains an ordinary function symbol. |
| 9 | create_profile | service/routes.py | 22-23 | route handler function | YES | function | YES | function | function:routes:create_profile | Route handler remains an ordinary function symbol. |
| 10 | __test__ | tests/TestRoutes.py | 1 | variable | YES | variable | NO | NONE | NONE | Source-level test-file variable; not a graph node or chunk. |
| 11 | test_greeting_service | tests/TestRoutes.py | 4-5 | test function | YES | function | NO | test | test:tests:test_greeting_service | Test function is one manifest symbol and one test graph node. |
| 12 | GET `/profiles/{user_id}` | service/routes.py | 16-18 | route identity | NO | NONE | YES | route | function:routes:get_profile | Route identity is represented by the route record and graph route node. |
| 13 | POST `/profiles` | service/routes.py | 21-23 | route identity | NO | NONE | YES | route | function:routes:create_profile | Route identity is represented by the route record and graph route node. |

### 4.4 Final Manifest-Symbol Table

| # | Semantic key | Kind | Qualified name | Source path | Start | End | Parent semantic key | Source justification |
|---:|---|---|---|---|---:|---:|---|---|
| 1 | variable:helpers:DEFAULT_GREETING | variable | DEFAULT_GREETING | service/helpers.py | 1 | 1 | NONE | Module-level constant. |
| 2 | function:helpers:normalize_name | function | normalize_name | service/helpers.py | 4 | 5 | NONE | Synchronous helper function. |
| 3 | async_function:helpers:fetch_profile | function | fetch_profile | service/helpers.py | 8 | 9 | NONE | Asynchronous helper function represented as function kind. |
| 4 | variable:routes:app | variable | app | service/routes.py | 5 | 5 | NONE | FastAPI application variable. |
| 5 | class:routes:GreetingService | class | GreetingService | service/routes.py | 8 | 14 | NONE | Service class. |
| 6 | method:routes:GreetingService.greet | method | GreetingService.greet | service/routes.py | 9 | 10 | class:routes:GreetingService | Class method. |
| 7 | method:routes:GreetingService._audit | method | GreetingService._audit | service/routes.py | 12 | 13 | class:routes:GreetingService | Class method. |
| 8 | function:routes:get_profile | function | get_profile | service/routes.py | 17 | 18 | NONE | GET route handler function. |
| 9 | function:routes:create_profile | function | create_profile | service/routes.py | 22 | 23 | NONE | POST route handler function. |
| 10 | variable:tests:__test__ | variable | __test__ | tests/TestRoutes.py | 1 | 1 | NONE | Test-file module variable. |
| 11 | test:tests:test_greeting_service | function | test_greeting_service | tests/TestRoutes.py | 4 | 5 | NONE | Python test function. |

FINAL_MANIFEST_SYMBOL_COUNT=11
DUPLICATE_SYMBOL_SEMANTIC_KEYS=0
DUPLICATE_SOURCE_CONSTRUCTS=0
DANGLING_PARENT_KEYS=0
INVALID_SYMBOL_PATHS=0
INVALID_SYMBOL_RANGES=0

---

## 5. Import Inventory

Only `service/routes.py` contains Python imports:

| Source path | Source module | Imported module | Imported name | Alias | Kind | Internal fixture relationship | Line |
|---|---|---|---|---|---|---|---:|
| service/routes.py | service | fastapi | FastAPI | NONE | from import | NO — external dependency | 1 |
| service/routes.py | service | helpers | DEFAULT_GREETING | NONE | from import (relative) | YES — connects to service/helpers.py | 3 |
| service/routes.py | service | helpers | fetch_profile | NONE | from import (relative) | YES — connects to service/helpers.py | 3 |
| service/routes.py | service | helpers | normalize_name | NONE | from import (relative) | YES — connects to service/helpers.py | 3 |

The `from .helpers import ...` statement at line 3 is parsed by `import_extractor.py` as three separate `ParsedImport` records (one per alias in `node.names`), each with `module_name='helpers'`, `imported_names=[name]`, `is_relative=True`, `line_number=3`.

Internal fixture relationships: 3 of 4 imports connect `service/routes.py` → `service/helpers.py`. The `fastapi` import is external.

---

## 6. Route Inventory

| Method | Route path | Handler | Path | Decorator line | Start | End | Source evidence |
|---|---|---|---|---:|---:|---:|---|
| GET | /profiles/{user_id} | function:routes:get_profile | service/routes.py | 16 | 16 | 18 | `@app.get("/profiles/{user_id}")` at line 16, async handler `get_profile` defined at line 17, body at line 18. |
| POST | /profiles | function:routes:create_profile | service/routes.py | 21 | 21 | 23 | `@app.post("/profiles")` at line 21, sync handler `create_profile` defined at line 22, body at line 23. |

Both routes are detected by `route_detector.py` via `_parse_decorator()` which checks `deco.func.attr in FASTAPI_ATTRIBUTES` and `deco.func.value.id in ("app", "router")`. Both use `app` as the decorator target object.

FINAL_ROUTE_COUNT=2
UNRESOLVED_ROUTE_HANDLERS=0

### 6.1 Route-Chunk Ownership

| Route chunk semantic key | Method | Path pattern | Current owner | Correct owner | Owner resolves to symbol | Contract evidence |
|---|---|---|---|---|---|---|
| route:GET:/profiles/{user_id}:16-18 | GET | /profiles/{user_id} | route:GET:/profiles/{user_id}:service/routes.py:16 | function:routes:get_profile | YES | `_make_route_chunk()` creates the route chunk from `ParsedRoute`; the strict manifest validator requires a non-null owner to be in `symbols`. |
| route:POST:/profiles:21-23 | POST | /profiles | route:POST:/profiles:service/routes.py:21 | function:routes:create_profile | YES | `_make_route_chunk()` creates the route chunk from `ParsedRoute`; the strict manifest validator requires a non-null owner to be in `symbols`. |

GET_ROUTE_CHUNK_OWNER=function:routes:get_profile
POST_ROUTE_CHUNK_OWNER=function:routes:create_profile
UNRESOLVED_CHUNK_OWNERS=0
ROUTE_CHUNK_OWNER_CORRECTIONS_REQUIRED=2

GRAPH_ORACLE_CHANGE_REQUIRED=False
GRAPH_NODE_COUNT_AFTER=21
GRAPH_EDGE_COUNT_AFTER=21
GRAPH_CHANGE_REASON=Manifest symbol filtering does not alter the accepted graph-node or graph-edge oracle; route identities remain separate graph route nodes.
SYMBOL_ORACLE_AMBIGUITIES=NONE

---

## 7. Test Inventory

| Test semantic key | Qualified name | Path | Start | End | Referenced symbols | Source evidence |
|---|---|---|---:|---:|---|---|
| test:tests:test_greeting_service | test_greeting_service | tests/TestRoutes.py | 4 | 5 | NONE | `def test_greeting_service() -> None:` at line 4, `assert "GreetingService" in "Golden service test evidence"` at line 5. No function calls to named symbols in source. The string literal "GreetingService" is NOT a call node — it's a constant. No symbols referenced via AST call analysis. |

The test function `test_greeting_service` does not call `normalize_name`, `fetch_profile`, `get_profile`, `create_profile`, `GreetingService.greet`, or any other named function. The assertion uses string literals only.

The file `tests/TestRoutes.py` has `__test__ = False` at line 1 (a variable assignment, not a symbol reference).

---

## 8. Chunk-Source Inventory

### 8.0 File-Level Chunk Rules

| Path | Language/type | File-summary chunk | Symbol chunks | Heading/section chunks | Config chunks | Unsupported |
|---|---|---|---|---|---|---|
| guide.rst | RST document | NO | NO | 2 RST sections | NO | NO |
| README.md | Markdown document | NO | NO | 2 Markdown sections | NO | NO |
| service/__init__.py | Python package-marker | YES | NO | NO | NO | NO |
| service/helpers.py | Python source | YES | 2 function chunks | NO | NO | NO |
| service/routes.py | Python source | YES | 2 function, 1 class, 2 method, 2 route chunks | NO | NO | NO |
| settings.toml | recognized configuration | NO | NO | NO | 1 config block | NO |
| tests/TestRoutes.py | Python test source | YES | 1 test chunk | NO | NO | NO |

Python files receive file summaries when non-empty; the package-marker file receives one because its docstring is content. Markdown and RST use only heading/section chunks, and configuration uses only config blocks. No unsupported generic-text file exists in G01. Route chunks are separate from handler function chunks; the test chunk is separate from its function representation; class and method chunks are separate.

### 8.1 Python File Summaries

| Chunk semantic key | Path | Type | Owner | Start | End | Embedding eligible | Skip reason | Manual justification |
|---|---|---|---|---:|---:|---|---|---|
| file_summary:service/__init__.py:1-1 | service/__init__.py | file_summary | NONE | 1 | 1 | YES | NONE | Single-line docstring file. `_make_file_summary()` includes docstring `"Golden service package."` + first line. start_line=1, end_line=min(20, 1)=1. |
| file_summary:service/helpers.py:1-9 | service/helpers.py | file_summary | NONE | 1 | 9 | YES | NONE | 9 lines, all ≤ 20. No docstring, no imports in file (imports in routes.py, not helpers.py). Content is first 9 lines. start_line=1, end_line=9. |
| file_summary:service/routes.py:1-20 | service/routes.py | file_summary | NONE | 1 | 20 | YES | NONE | 23 lines. `_make_file_summary()` takes min(20, 23)=20 lines. Includes 2 import texts (from fastapi, from helpers). start_line=1, end_line=20. |
| file_summary:tests/TestRoutes.py:1-5 | tests/TestRoutes.py | file_summary | NONE | 1 | 5 | YES | NONE | 5 lines ≤ 20. No docstring, no imports. Content is first 5 lines. start_line=1, end_line=5. |

Note: `guide.rst`, `README.md`, and `settings.toml` have parse_status=not_applicable. These are non-Python files routed through `_chunk_markdown`, `_chunk_rst`, or `_chunk_config` based on extension, NOT `_chunk_python`. The `_chunk_python` method only handles `.py`/`.pyw` extensions. These files get their own chunking paths and do NOT produce file_summary chunks — they produce heading/section/config chunks instead.

### 8.2 Python Function Chunks

| Chunk semantic key | Path | Type | Owner | Start | End | Embedding eligible | Skip reason | Manual justification |
|---|---|---|---|---:|---:|---|---|---|
| function:helpers:normalize_name:4-5 | service/helpers.py | function | function:helpers:normalize_name | 4 | 5 | YES | NONE | `def normalize_name(name: str) -> str:` at L4, body at L5. AST `end_lineno=5`. ChunkType.FUNCTION. |
| function:helpers:fetch_profile:8-9 | service/helpers.py | function | async_function:helpers:fetch_profile | 8 | 9 | YES | NONE | `async def fetch_profile(user_id: str) -> dict[str, str]:` at L8, body at L9. AST `end_lineno=9`. ChunkType.FUNCTION. |
| function:routes:get_profile:17-18 | service/routes.py | function | function:routes:get_profile | 17 | 18 | YES | NONE | `async def get_profile(user_id: str) -> dict[str, str]:` at L17, body at L18. AST `end_lineno=18`. ChunkType.FUNCTION. NOT skipped by route_symbol_ids (its symbol_id is `function:routes.py:get_profile:17`, different from route_id). |
| function:routes:create_profile:22-23 | service/routes.py | function | function:routes:create_profile | 22 | 23 | YES | NONE | `def create_profile(name: str) -> dict[str, str]:` at L22, body at L23. AST `end_lineno=23`. ChunkType.FUNCTION. NOT skipped by route_symbol_ids. |

### 8.3 Python Class Chunk

| Chunk semantic key | Path | Type | Owner | Start | End | Embedding eligible | Skip reason | Manual justification |
|---|---|---|---|---:|---:|---|---|---|
| class:routes:GreetingService:8-14 | service/routes.py | class | class:routes:GreetingService | 8 | 14 | YES | NONE | `class GreetingService:` at L8. AST `end_lineno=14` (includes all methods). ChunkType.CLASS. Content is class signature line + method summaries. |

The `_make_class_summary()` extracts the header line and any docstring. `GreetingService` has no docstring, so content is `"class GreetingService:"`. The `metadata.get("methods", [])` lookup on the symbol's metadata yields empty (metadata has `"bases": []` or no methods key). So chunk content = header line only.

### 8.4 Python Method Chunks

| Chunk semantic key | Path | Type | Owner | Start | End | Embedding eligible | Skip reason | Manual justification |
|---|---|---|---|---:|---:|---|---|---|
| method:routes:GreetingService.greet:9-10 | service/routes.py | method | method:routes:GreetingService.greet | 9 | 10 | YES | NONE | `def greet(self, name: str) -> str:` at L9, body at L10. AST `end_lineno=10`. ChunkType.METHOD. |
| method:routes:GreetingService._audit:12-13 | service/routes.py | method | method:routes:GreetingService._audit | 12 | 13 | YES | NONE | `def _audit(self, user_id: str) -> str:` at L12, body at L13. AST `end_lineno=13`. ChunkType.METHOD. |

### 8.5 Python Route Chunks

| Chunk semantic key | Path | Type | Owner | Start | End | Embedding eligible | Skip reason | Manual justification |
|---|---|---|---|---:|---:|---|---|---|
| route:GET:/profiles/{user_id}:16-18 | service/routes.py | route | function:routes:get_profile | 16 | 18 | YES | NONE | Decorator at L16, handler body L17-18. Content = decorator + handler body lines 16-18. ChunkType.ROUTE. Owner is the ordinary handler-function symbol. |
| route:POST:/profiles:21-23 | service/routes.py | route | function:routes:create_profile | 21 | 23 | YES | NONE | Decorator at L21, handler body L22-23. Content = decorator + handler body lines 21-23. ChunkType.ROUTE. Owner is the ordinary handler-function symbol. |

### 8.6 Python Test Chunks

| Chunk semantic key | Path | Type | Owner | Start | End | Embedding eligible | Skip reason | Manual justification |
|---|---|---|---|---:|---:|---|---|---|
| test:tests:test_greeting_service:4-5 | tests/TestRoutes.py | test | test:tests:test_greeting_service | 4 | 5 | YES | NONE | `def test_greeting_service() -> None:` at L4, body at L5. File is `tests/TestRoutes.py` (file_type=TEST), function name starts with `test_` → `_is_test_symbol` returns True. ChunkType.TEST. |

Note: `__test__ = False` is a variable → skipped by `_chunk_python` (variable check at line 202-203). No chunk produced.

### 8.7 Python Variable Skips

Variables are NOT chunked. Per chunker rules: "Variable definitions are stored in `symbols` with `symbol_type = 'variable'`. During the first slice: Variables do not become graph nodes, no variable-related graph edges are produced." Same for chunks: `_chunk_python` explicitly skips `SymbolType.VARIABLE` at line 202-203.

Skipped variables: `DEFAULT_GREETING` (helpers.py L1), `app` (routes.py L5), `__test__` (TestRoutes.py L1).

### 8.8 Non-Python Chunks

#### Markdown

| Heading text | Heading level | Path | Start | End | Expected chunk identity |
|---|---:|---|---:|---:|---|
| Golden Service | 1 | README.md | 1 | 2 | readme_section:README.md:1-2. Content: `# Golden Service` plus the separating blank line. |
| Search Terms | 2 | README.md | 3 | 6 | readme_section:README.md:3-6. Content: `## Search Terms\n\nGolden profile service provides deterministic greeting behavior.` plus the trailing split line. |

Markdown heading detection: `_chunk_markdown` uses regex `r"^(#{1,6})\s"`. Line 1 `# Golden Service` matches level 1. Line 3 `## Search Terms` matches level 2. No preamble (first heading at line 1). The implementation retains the trailing split line, so the second chunk ends at line 6.

#### RST

| Section text | Underline style | Path | Start | End | Expected chunk identity |
|---|---|---|---:|---:|---|
| Golden Guide | = | guide.rst | 1 | 3 | readme_section:guide.rst:1-3. Content: `Golden Guide\n============\n` (title and underline, then separator). |
| Configuration | - | guide.rst | 4 | 8 | readme_section:guide.rst:4-8. Content: `Configuration\n-------------\n\nThe golden service is static.` plus the trailing split line. |

RST heading detection: `_RST_HEADING_PATTERN = re.compile(r"^([=\-~^`:'\"\._*+#<>!@$%&]){3,}\s*$", re.MULTILINE)`. The `============` at L2 matches (= repeated ≥3 times). The `-------------` at L5 matches (- repeated ≥3 times). Headings detected at i=0 (L1→underline L2) and i=3 (L4→underline L5). The resulting section ranges are `1-3` and `4-8`; the implementation retains the trailing split line.
RST_SECTION_CHUNK_COUNT=2

Note: RST content includes the underline marker line as part of the section chunk content. This is per the chunker implementation: `section_start = hdr_line - 1` captures the text line, and section_lines include the underline.

#### Configuration

| Block or semantic section | Path | Start | End | Expected chunk identity |
|---|---|---:|---:|---|
| [service] section | settings.toml | 1 | 3 | config:settings.toml:1-3. Content: `[service]\nname = "golden-profile-service"` plus the trailing split line. Config file, one short block under the 100-line block size. `block_index=0`, `block_count=1`. |

---

## 9. Chunk Count Summary

| Chunk source | Count |
|---|---:|
| service/__init__.py file_summary | 1 |
| service/helpers.py file_summary | 1 |
| service/helpers.py functions | 2 |
| service/routes.py file_summary | 1 |
| service/routes.py class | 1 |
| service/routes.py methods | 2 |
| service/routes.py functions | 2 |
| service/routes.py routes | 2 |
| tests/TestRoutes.py file_summary | 1 |
| tests/TestRoutes.py test | 1 |
| README.md readme_section | 2 |
| guide.rst readme_section | 2 |
| settings.toml config | 1 |
| **Total** | **19** |

FILE_SUMMARY_CHUNKS=4
FUNCTION_CHUNKS=4
CLASS_CHUNKS=1
METHOD_CHUNKS=2
ROUTE_CHUNKS=2
TEST_CHUNKS=1
MARKDOWN_CHUNKS=2
RST_CHUNKS=2
CONFIG_CHUNKS=1
OTHER_CHUNKS=0
TOTAL_CHUNKS=19
EMBEDDING_ELIGIBLE_CHUNKS=19
EMBEDDING_INELIGIBLE_CHUNKS=0
DUPLICATE_CHUNK_SEMANTIC_KEYS=0
INVALID_LINE_RANGES=0
MISSING_SOURCE_CONSTRUCTS=0
UNJUSTIFIED_CHUNKS=0
CHUNK_ORACLE_AMBIGUITIES=NONE

The complete arithmetic is 4 + 4 + 1 + 2 + 2 + 1 + 2 + 2 + 1 + 0 = 19. The two RST section chunks are included in the total; no generic-text chunks are present.

---

## 10. Graph-Node Inventory

### 10.0 Node Eligibility Decisions

| Source construct | Source kind | Graph node created | Graph node kind | Semantic key | Contract evidence |
|---|---|---|---|---|---|
| guide.rst, README.md, service/__init__.py, service/helpers.py, service/routes.py, settings.toml, tests/TestRoutes.py | scanned file | YES | file | `file:{path}` | `build_graph()` creates one file node for every `ParsedFile`; this includes documentation, configuration, and package-marker files. |
| DEFAULT_GREETING, app, __test__ | module-level variable | NO | NONE | NONE | `_symbol_to_node_type()` returns `None` for `SymbolType.VARIABLE`. |
| normalize_name, fetch_profile, get_profile, create_profile | function/async function | YES | function | function node IDs listed in §10.3 | `SymbolType.FUNCTION` maps to `GraphNodeType.FUNCTION`; async functions use the same symbol type. |
| GreetingService | class | YES | class | `class:service/routes.py:GreetingService:8` | `SymbolType.CLASS` maps to `GraphNodeType.CLASS`. |
| GreetingService.greet, GreetingService._audit | method | YES | method | method node IDs listed in §10.3 | `SymbolType.METHOD` maps to `GraphNodeType.METHOD`. |
| test_greeting_service | Python test function | YES | test | `test:tests/TestRoutes.py:test_greeting_service:4` | Test-file functions map to `GraphNodeType.TEST`. |
| GET `/profiles/{user_id}`, POST `/profiles` | route | YES | route | route node IDs listed in §10.2 | Each `ParsedRoute` creates a separate authoritative route node. |
| four imported names | import | YES | import | import node IDs listed in §10.4 | Each parsed import record creates a separate import node. |

Answers: route handlers create both normal function nodes and separate route nodes; imported names create separate import nodes; non-Python files create file nodes; package-marker files are file nodes; no separate module/package nodes exist.

### 10.1 File Nodes (7)

| Node semantic key | Kind | Qualified name | Source path | Linked semantic key | Manual justification |
|---|---|---|---|---|---|
| file:guide.rst | file | guide.rst | guide.rst | NONE | Every scanned file produces a file node. guide.rst is scanned (parse status not_applicable). |
| file:README.md | file | README.md | README.md | NONE | Every scanned file produces a file node. README.md is scanned (parse status not_applicable). |
| file:service/__init__.py | file | service/__init__.py | service/__init__.py | NONE | Every scanned file produces a file node. service/__init__.py is scanned and parsed (parsed status). |
| file:service/helpers.py | file | service/helpers.py | service/helpers.py | NONE | Every scanned file produces a file node. |
| file:service/routes.py | file | service/routes.py | service/routes.py | NONE | Every scanned file produces a file node. |
| file:settings.toml | file | settings.toml | settings.toml | NONE | Every scanned file produces a file node. settings.toml is scanned (parse status not_applicable). |
| file:tests/TestRoutes.py | file | tests/TestRoutes.py | tests/TestRoutes.py | NONE | Every scanned file produces a file node. |

### 10.2 Route Nodes (2)

| Node semantic key | Kind | Qualified name | Source path | Linked semantic key | Manual justification |
|---|---|---|---|---|---|
| route:GET:/profiles/{user_id}:service/routes.py:16 | route | get_profile | service/routes.py | function:routes:get_profile | Route decorator `@app.get("/profiles/{user_id}")` at L16. Handler function `get_profile`. |
| route:POST:/profiles:service/routes.py:21 | route | create_profile | service/routes.py | function:routes:create_profile | Route decorator `@app.post("/profiles")` at L21. Handler function `create_profile`. |

Route nodes are processed FIRST in `build_graph()` (lines 138-213) before regular symbol nodes. Their node_id = route_id.

### 10.3 Symbol Nodes (8)

| Node semantic key | Kind | Qualified name | Source path | Linked semantic key | Manual justification |
|---|---|---|---|---|---|
| function:service/helpers.py:normalize_name:4 | function | normalize_name | service/helpers.py | function:helpers:normalize_name | Module-level function in helpers.py. `_symbol_to_node_type` → FUNCTION. |
| function:service/helpers.py:fetch_profile:8 | function | fetch_profile | service/helpers.py | async_function:helpers:fetch_profile | Module-level async function in helpers.py. `_symbol_to_node_type` → FUNCTION. |
| class:service/routes.py:GreetingService:8 | class | GreetingService | service/routes.py | class:routes:GreetingService | Module-level class in routes.py. `_symbol_to_node_type` → CLASS. |
| method:service/routes.py:greet:9 | method | GreetingService.greet | service/routes.py | method:routes:GreetingService.greet | Method inside GreetingService. `_symbol_to_node_type` → METHOD. |
| method:service/routes.py:_audit:12 | method | GreetingService._audit | service/routes.py | method:routes:GreetingService._audit | Method inside GreetingService. `_symbol_to_node_type` → METHOD. |
| function:service/routes.py:get_profile:17 | function | get_profile | service/routes.py | function:routes:get_profile | Module-level async function. `_symbol_to_node_type` → FUNCTION. Node_id ≠ route_id → node emitted (not deduplicated). |
| function:service/routes.py:create_profile:22 | function | create_profile | service/routes.py | function:routes:create_profile | Module-level function. `_symbol_to_node_type` → FUNCTION. Node_id ≠ route_id → node emitted. |
| test:tests/TestRoutes.py:test_greeting_service:4 | test | test_greeting_service | tests/TestRoutes.py | test:tests:test_greeting_service | Function in test file. `_symbol_to_node_type` for file_type=TEST → GraphNodeType.TEST. |

Note: Variables (`DEFAULT_GREETING`, `app`, `__test__`) → `_symbol_to_node_type` returns `None` → no node. Route symbols (GET/POST) have node_id = route_id, already in node_id_set → skipped (line 234).

### 10.4 Import Nodes (4)

| Node semantic key | Kind | Qualified name | Source path | Linked semantic key | Manual justification |
|---|---|---|---|---|---|
| import:service/routes.py:fastapi:fastapi:1 | import | fastapi | service/routes.py | NONE | `from fastapi import FastAPI` at L1. `import_node_id = "import:service/routes.py:fastapi:fastapi:1"`. External dependency. |
| import:service/routes.py:helpers:DEFAULT_GREETING:3 | import | helpers | service/routes.py | NONE | `from .helpers import DEFAULT_GREETING` (first alias from L3). `import_node_id = "import:service/routes.py:helpers:DEFAULT_GREETING:3"`. |
| import:service/routes.py:helpers:fetch_profile:3 | import | helpers | service/routes.py | NONE | `from .helpers import fetch_profile` (second alias from L3). `import_node_id = "import:service/routes.py:helpers:fetch_profile:3"`. |
| import:service/routes.py:helpers:normalize_name:3 | import | helpers | service/routes.py | NONE | `from .helpers import normalize_name` (third alias from L3). `import_node_id = "import:service/routes.py:helpers:normalize_name:3"`. |

Import node identity is per-file and per-line (`import:{file_path}:{module_name}:{identity}:{line_number}`). The three relative imports from L3 produce three separate import nodes because each has a different `identity` (imported_name).

### 10.5 Graph Node Total: 21

7 (file) + 2 (route) + 8 (symbol) + 4 (import) + 0 (other) = 21.

FILE_NODE_COUNT=7
SYMBOL_NODE_COUNT=8
ROUTE_NODE_COUNT=2
IMPORT_NODE_COUNT=4
OTHER_NODE_COUNT=0
TOTAL_GRAPH_NODE_COUNT=21

The prior 22-node summary was incorrect. The detailed source inventory identifies eight eligible non-route symbol nodes: two functions, one class, two methods, two route handlers, and one test function. The three variables are explicitly excluded, and the two route symbols are represented by the two authoritative route nodes. No separate module or package nodes exist.

GRAPH_ORACLE_AMBIGUITIES=NONE

---

## 11. Graph-Edge Inventory

### 11.1 Defines Edges (12)

| Source | Target | Edge type | Qualifier | Source evidence | Manual reason |
|---|---|---|---|---|---|
| file:service/helpers.py | function:service/helpers.py:normalize_name:4 | defines | NONE | symbol at L4 in helpers.py | Function `normalize_name` defined in helpers.py. |
| file:service/helpers.py | function:service/helpers.py:fetch_profile:8 | defines | NONE | symbol at L8 in helpers.py | Function `fetch_profile` defined in helpers.py. |
| file:service/routes.py | class:service/routes.py:GreetingService:8 | defines | NONE | symbol at L8 in routes.py | Class `GreetingService` defined in routes.py. |
| file:service/routes.py | method:service/routes.py:greet:9 | defines | NONE | symbol at L9 in routes.py | Method `greet` defined in routes.py. |
| file:service/routes.py | method:service/routes.py:_audit:12 | defines | NONE | symbol at L12 in routes.py | Method `_audit` defined in routes.py. |
| file:service/routes.py | function:service/routes.py:get_profile:17 | defines | NONE | symbol at L17 in routes.py | Function `get_profile` defined in routes.py. |
| file:service/routes.py | function:service/routes.py:create_profile:22 | defines | NONE | symbol at L22 in routes.py | Function `create_profile` defined in routes.py. |
| file:tests/TestRoutes.py | test:tests/TestRoutes.py:test_greeting_service:4 | defines | NONE | symbol at L4 in tests/TestRoutes.py | Test function `test_greeting_service` defined in TestRoutes.py. |
| class:service/routes.py:GreetingService:8 | method:service/routes.py:greet:9 | defines | NONE | parent=GreetingService (in symbol metadata), method inside class | Method `greet` is child of `GreetingService` class. Edge from parent class to method (INFERRED confidence per graph_builder line 294). |
| class:service/routes.py:GreetingService:8 | method:service/routes.py:_audit:12 | defines | NONE | parent=GreetingService (in symbol metadata), method inside class | Method `_audit` is child of `GreetingService` class. Edge from parent class to method (INFERRED confidence). |

Note: Route symbols (GET/POST) have `symbol_id = route_id`, so their `node_id` is already in `node_id_set` when the symbol loop reaches them → the `defines` edge is NOT emitted for route symbols (line 253-272 is skipped by line 234-235 `continue`). The route's `defines` edge is emitted via the separate route processing at lines 174-193, but with the route as TARGET, not source — specifically, the edge `handler_id → route_node_id` with relation=DEFINES.

Actually, re-reading graph_builder.py lines 174-193: the `defines` edge is emitted as `source_node_id=handler_id, target_node_id=route_node_id, relation=GraphRelation.DEFINES`. This means the handler function defines the route (or rather, the route is defined by the handler). This edge is:
- `function:service/routes.py:get_profile:17 → route:GET:/profiles/{user_id}:service/routes.py:16` with relation=DEFINES
- `function:service/routes.py:create_profile:22 → route:POST:/profiles:service/routes.py:21` with relation=DEFINES

Wait — this is a different `defines` direction. Let me re-check:

Line 186-188:
```python
source_node_id=handler_id,
target_node_id=route_node_id,
relation=GraphRelation.DEFINES,
```

So the edge is: handler function DEFINES the route. This means the handler node is the SOURCE and the route node is the TARGET.

So there are 2 additional `defines` edges from handler to route:

| Source | Target | Edge type | Qualifier | Source evidence | Manual reason |
|---|---|---|---|---|---|
| function:service/routes.py:get_profile:17 | route:GET:/profiles/{user_id}:service/routes.py:16 | defines | NONE | graph_builder.py L186-188: handler_id → route_node_id with DEFINES | Handler function defines the GET route. |
| function:service/routes.py:create_profile:22 | route:POST:/profiles:service/routes.py:21 | defines | NONE | graph_builder.py L186-188: handler_id → route_node_id with DEFINES | Handler function defines the POST route. |

Updated defines total: 10 (file→symbol) + 2 (handler→route) = 12.

### 11.2 Handles-Route Edges (2)

| Source | Target | Edge type | Qualifier | Source evidence | Manual reason |
|---|---|---|---|---|---|
| route:GET:/profiles/{user_id}:service/routes.py:16 | function:service/routes.py:get_profile:17 | handles_route | NONE | graph_builder.py L194-213: route_node_id → handler_id with HANDLES_ROUTE | GET route handled by `get_profile` function. |
| route:POST:/profiles:service/routes.py:21 | function:service/routes.py:create_profile:22 | handles_route | NONE | graph_builder.py L194-213: route_node_id → handler_id with HANDLES_ROUTE | POST route handled by `create_profile` function. |

### 11.3 Imports Edges (4)

| Source | Target | Edge type | Qualifier | Source evidence | Manual reason |
|---|---|---|---|---|---|
| file:service/routes.py | import:service/routes.py:fastapi:fastapi:1 | imports | NONE | `from fastapi import FastAPI` at L1 | File routes.py imports external module fastapi. |
| file:service/routes.py | import:service/routes.py:helpers:DEFAULT_GREETING:3 | imports | NONE | `from .helpers import DEFAULT_GREETING` at L3 | File routes.py imports DEFAULT_GREETING from helpers. |
| file:service/routes.py | import:service/routes.py:helpers:fetch_profile:3 | imports | NONE | `from .helpers import fetch_profile` at L3 | File routes.py imports fetch_profile from helpers. |
| file:service/routes.py | import:service/routes.py:helpers:normalize_name:3 | imports | NONE | `from .helpers import normalize_name` at L3 | File routes.py imports normalize_name from helpers. |

### 11.4 Calls Edges (3)

The graph builder's `_add_calls_edges()` searches `symbol_by_name` globally (across all parsed files) for call targets.

| Source | Target | Edge type | Qualifier | Source evidence | Manual reason |
|---|---|---|---|---|---|
| method:service/routes.py:greet:9 | function:service/helpers.py:normalize_name:4 | calls | NONE | `greet()` body: `return f"{DEFAULT_GREETING}, {normalize_name(name)}"` — `ast.Call` to `normalize_name`. Symbol metadata `calls: ["normalize_name"]`. Global `symbol_by_name["normalize_name"]` finds helpers.py function. INFERRED confidence. |
| function:service/routes.py:get_profile:17 | function:service/helpers.py:fetch_profile:8 | calls | NONE | `get_profile()` body: `return await fetch_profile(user_id)` — `ast.Call` to `fetch_profile`. Symbol metadata `calls: ["fetch_profile"]`. Global `symbol_by_name["fetch_profile"]` finds helpers.py function. INFERRED confidence. |
| function:service/routes.py:create_profile:22 | function:service/helpers.py:normalize_name:4 | calls | NONE | `create_profile()` body: `return {"name": normalize_name(name)}` — `ast.Call` to `normalize_name`. Symbol metadata `calls: ["normalize_name"]`. Global `symbol_by_name["normalize_name"]` finds helpers.py function. INFERRED confidence. |

Note: The graph builder creates cross-file `calls` edges. The `05_INDEXING_AND_RETRIEVAL.md` documentation states "only if both are in the same file", but the actual `graph_builder.py` code searches `symbol_by_name` globally without file filtering. This review documents the code behavior.

### 11.5 Inherited Edges (0)

`GreetingService` has no bases (`metadata.get("bases") = []`). No `inherits` edges.

### 11.6 Tests Edges (0)

`test_greeting_service` → `_infer_tested_name("test_greeting_service")` returns `"greeting_service"`. `symbol_by_name["greeting_service"]` → no match (no symbol named `greeting_service` exists). No `tests` edges.

### 11.7 Graph Edge Total: 21

12 (defines) + 2 (handles_route) + 4 (imports) + 3 (calls) = 21.

DEFINES_EDGE_COUNT=12
HANDLES_ROUTE_EDGE_COUNT=2
IMPORTS_EDGE_COUNT=4
CALLS_EDGE_COUNT=3
OTHER_EDGE_COUNT=0
TOTAL_GRAPH_EDGE_COUNT=21
DANGLING_EDGE_ENDPOINTS=0
DUPLICATE_CANONICAL_EDGE_TUPLES=0

The prior 19-edge manifest value omitted the two handler-to-route `defines` edges. All 21 listed edges now have declared node endpoints and unique canonical tuples.

---

## 12. Safe Search-Term Inventory

| Search term | Expected matching semantic item | Source path | Why uniquely useful |
|---|---|---|---|
| normalize_name | function:helpers:normalize_name | service/helpers.py | Standalone function, unique name, finds helper. |
| fetch_profile | async_function:helpers:fetch_profile | service/helpers.py | Standalone async function, unique name. |
| GreetingService | class:routes:GreetingService | service/routes.py | Class with methods, unique name. |
| greet | method:routes:GreetingService.greet | service/routes.py | Method on class, unique name. |
| _audit | method:routes:GreetingService._audit | service/routes.py | Private method, unique name. |
| get_profile | route:GET:/profiles/{user_id}:routes.py:16 | service/routes.py | Route handler function, unique name. |
| create_profile | route:POST:/profiles:routes.py:21 | service/routes.py | Route handler function, unique name. |
| test_greeting_service | test:tests:test_greeting_service | tests/TestRoutes.py | Test function, unique name. |
| Golden Service | file_summary:README.md:1-2 | README.md | Markdown heading chunk. |
| Search Terms | readme_section:README.md:3-6 | README.md | Markdown heading chunk. |
| Golden Guide | readme_section:guide.rst:1-3 | guide.rst | RST section chunk. |
| Configuration | readme_section:guide.rst:4-8 | guide.rst | RST section chunk, also config section. |
| service | config:settings.toml:1-3 | settings.toml | TOML section header. |
| golden-profile-service | config:settings.toml:1-3 | settings.toml | TOML value, unique string. |
| DEFAULT_GREETING | variable:helpers:DEFAULT_GREETING | service/helpers.py | Module-level constant. |
| Golden hello | (content in helpers.py) | service/helpers.py | Greeting string literal. |
| golden profile | (content in README.md) | README.md | Description text. |

---

## 13. Warning and Error Inventory

| Category | Expected count | Source cause | Relevant path |
|---|---:|---|---|
| parse_warning | 0 | No files produce parse warnings. Non-Python files are never sent to `ast.parse()` (scanner assigns `not_applicable`). All 4 Python files parse successfully. | NONE |

EXPECTED_WARNINGS=0
EXPECTED_RECOVERABLE_ERRORS=0

The scanner sets `parse_status=NOT_APPLICABLE` for non-Python files (file_scanner.py L194). The index service parse phase (index_service.py L307-309) only selects files with `parse_status == PENDING`. Non-Python files never enter the parser. The `parse_warning` diagnostic (index_service.py L351-358) is emitted only when a parsed file returns `ParseStatus.ERROR`; since all 4 Python files parse successfully, no `parse_warning` diagnostics are produced.

No secret detection warnings (`file_secret_detected=0`), no file skipped warnings (`file_skipped=0`), no embedding chunk warnings (`embedding_chunk_warning=0`).

---

## 14. Deterministic Identity Inputs

| Identity category | Canonical inputs available from source | Absolute-path independent |
|---|---|---|
| File | `file_path` (repo-relative POSIX), `content_hash` (SHA-256 of file bytes) | YES |
| Symbol | `symbol_type`, `name`, `qualified_name`, `file_path`, `start_line`, `end_line` | YES |
| Chunk | `file_id`, `chunk_type`, `start_line`, `end_line`, `symbol_id`, `content_hash` | YES (file_id is UUID, not path-dependent) |
| Route | `method`, `route_path`, `handler_function`, `file_path`, `start_line` (decorator line) | YES |
| Graph node | `node_id` (format: `{type}:{path}:{name}:{line}`), `node_type` | YES |
| Graph edge | `source_node_id`, `target_node_id`, `relation`, `source_file`, `source_location` | YES |

---

## 15. Fixture Integrity Evidence

| Relative path | SHA-256 |
|---|---|
| guide.rst | 2d31246bd13edea7050a2b4e5e1b20ad65786a2b14fb9d58e972f654081be969 |
| README.md | a3f9a7f0b00803a21523f4d622c799cdeeaaf06392d1cc84906e1c17b6670d32 |
| service/__init__.py | 9f45fb258f9d7d5a8887fa78bd3d23f41d613178becb666401aed011de28c6d6 |
| service/helpers.py | 7823430b41c7be97a328cd43eaaaed4d0636b6d0d4964ecfd38370b788d84adb |
| service/routes.py | fbaaa983906c84d8294dcda154efc593673595a7caece84013fc73ae850f1dfd |
| settings.toml | 87d0fd112884eb6a440ca5aaa0b6ec395e47efddd5ad969d07b424dc09d64ac6 |
| tests/TestRoutes.py | 362f474258a4f0a916fe6af10c378c6b6c72b90e9319c895cdbdecea74fb97ae |

G01_AGGREGATE_DIGEST=bba310f73070a23fb804cf5968ec0e530419ccb01ec056c86e1abec8bb44233c
G01_FILE_COUNT=7
ABSOLUTE_PATH_INCLUDED_IN_DIGEST=False
TIMESTAMP_INCLUDED_IN_DIGEST=False

Line endings: all 7 files use LF (Unix-style). No CRLF detected.

Digests match the existing manifest integrity exactly.

---

## 16. Completeness Checklist

| Manifest category | Source inventory complete | Ambiguities |
|---|---|---|
| scanned_files | YES | NONE — all 7 files accounted for |
| excluded_files | NOT_APPLICABLE | NONE — no files excluded from this fixture |
| parse_statuses | YES | NONE — 4 parsed, 3 not_applicable (all non-Python files) |
| symbols | YES | NONE — 11 manifest symbols identified; 2 route identities remain separate route records |
| imports | YES | NONE — 4 import records from 2 import statements |
| routes | YES | NONE — 2 routes (GET, POST) accounted for |
| tests | YES | NONE — 1 test function accounted for |
| chunks | YES | NONE — 19 chunks derived from source rules |
| graph_nodes | YES | Corrected source-derived=21; prior manifest=18. See §10.5 |
| graph_edges | YES | Corrected source-derived=21; prior manifest=19. See §11.7 |
| safe_search_terms | YES | NONE — 17 terms listed |
| warnings | YES | NONE — 0 parse_warnings expected |
| errors | YES | NONE — 0 recoverable errors expected |
| deterministic_invariants | YES | NONE |

---

## 17. Divergences from Existing Manifest

| Item | Manifest value | Source-derived value | Root cause |
|---|---|---|---|
| graph_nodes | 18 | 21 | The corrected oracle includes 7 file nodes, 2 route nodes, 8 eligible symbol nodes, and 4 import nodes. Variables do not create nodes; no ninth symbol node exists. |
| graph_edges | 19 | 21 | 2 extra handler→route `defines` edges. The graph_builder emits `handler → route` edges with relation=DEFINES, which the manifest likely did not count. |
| parse_status | only 4 Python files listed | 3 non-Python files have parse_status=not_applicable | The scanner assigns `not_applicable` to non-Python files. They never enter the parse phase. The manifest correctly omits them from the `parse_status` dict because their status is `not_applicable`, not a parse outcome. |

These divergences are documented here as review evidence. The source-derived oracle is authoritative; the manifest is a snapshot from a prior pipeline run.

---

*Review complete. All fixture source files read and analyzed. Semantic truth derived directly from source inspection against accepted contracts.*
