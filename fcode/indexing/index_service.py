"""Index service — orchestrates the scan → parse → chunk pipeline.

Step 2 implements repository validation, single scanner invocation,
parser candidate selection with recoverable errors, and chunker invocation.
Results remain entirely in memory. No storage, embeddings, or graph work
is performed yet.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Sequence

from fcode.contracts import (
    ChunkerProtocol,
    CodeChunk,
    DiagnosticSeverity,
    ErrorCode,
    FCodeConfig,
    IndexBuildResult,
    IndexCounts,
    IndexDiagnostic,
    IndexPhase,
    IndexRunResult,
    IndexState,
    ParseStatus,
    ParsedFile,
    PythonParserProtocol,
    RepoInput,
    ScanResult,
    ScannedFile,
    ScannerProtocol,
)
from fcode.indexing.state_machine import IndexStateMachine


class IndexService:
    """Dependency-injected indexing orchestrator (Step 2: scan→parse→chunk)."""

    def __init__(
        self,
        scanner: ScannerProtocol,
        parser: PythonParserProtocol,
        chunker: ChunkerProtocol,
    ) -> None:
        if scanner is None:
            raise TypeError("scanner must not be None")
        if parser is None:
            raise TypeError("parser must not be None")
        if chunker is None:
            raise TypeError("chunker must not be None")
        self._scanner = scanner
        self._parser = parser
        self._chunker = chunker

    def build_through_chunking(
        self,
        config: FCodeConfig,
    ) -> IndexBuildResult:
        if not isinstance(config, FCodeConfig):
            raise TypeError(
                f"expected FCodeConfig, got {type(config).__name__}"
            )

        sm = IndexStateMachine()
        diagnostics: list[IndexDiagnostic] = []
        compat_errors: list[str] = []

        # ── Repository and config validation ────────────────────────────────

        validation_error = self._validate_config(config)
        if validation_error is not None:
            diag, compat = validation_error
            diagnostics.append(diag)
            compat_errors.append(compat)
            return self._build_fatal(
                sm, diagnostics, compat_errors, IndexState.ERROR, None
            )

        # ── RepoInput construction ──────────────────────────────────────────

        resolved_path = str(Path(config.repo_path).resolve())
        repo_input = RepoInput(
            repo_path=resolved_path,
            max_files=config.max_files,
            max_size_bytes=config.max_size_bytes,
            skip_hidden=not config.scan_hidden,
            skip_binary=True,
        )

        # ── SCANNING ────────────────────────────────────────────────────────

        sm.transition(IndexState.SCANNING)

        scan_result: ScanResult
        try:
            scan_result = self._scanner.scan(repo_input, config)
        except BaseException:
            diag = IndexDiagnostic(
                code=ErrorCode.SCAN_FAILED.value,
                message="File scanning failed unexpectedly.",
                phase=IndexPhase.SCAN,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            diagnostics.append(diag)
            compat_errors.append(diag.message)
            return self._build_fatal(
                sm, diagnostics, compat_errors, IndexState.ERROR, scan_result=None
            )

        scan_validation = self._validate_scan_result(scan_result, config)
        if scan_validation is not None:
            diag, compat = scan_validation
            diagnostics.append(diag)
            compat_errors.append(compat)
            return self._build_fatal(
                sm, diagnostics, compat_errors, IndexState.ERROR,
                scan_result=scan_result,
            )

        # ── Scanner warning conversion ──────────────────────────────────────

        warning_diags = self._convert_scanner_warnings(scan_result)
        diagnostics.extend(warning_diags)

        # ── PARSING ─────────────────────────────────────────────────────────

        sm.transition(IndexState.PARSING)

        candidates = [
            sf for sf in scan_result.files
            if sf.parse_status == ParseStatus.PENDING and not sf.is_binary
        ]

        parsed_files: list[ParsedFile] = []
        parse_ok_count = 0
        parse_err_count = 0
        symbol_count = 0

        for sf in candidates:
            try:
                pf = self._parser.parse(sf)
            except BaseException:
                diag = IndexDiagnostic(
                    code=ErrorCode.PARSE_FAILED.value,
                    message="Python parsing failed unexpectedly.",
                    phase=IndexPhase.PARSE,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                diagnostics.append(diag)
                compat_errors.append(diag.message)
                return self._build_fatal(
                    sm, diagnostics, compat_errors, IndexState.ERROR,
                    scan_result=scan_result, parsed_files=parsed_files,
                )

            parse_valid = self._validate_parse_result(pf, sf)
            if parse_valid is not None:
                diag, compat = parse_valid
                diagnostics.append(diag)
                compat_errors.append(compat)
                return self._build_fatal(
                    sm, diagnostics, compat_errors, IndexState.ERROR,
                    scan_result=scan_result, parsed_files=parsed_files,
                )

            parsed_files.append(pf)

            if pf.status == ParseStatus.PARSED:
                parse_ok_count += 1
            elif pf.status == ParseStatus.ERROR:
                parse_err_count += 1
                wdiag = IndexDiagnostic(
                    code="parse_warning",
                    message="Python file could not be parsed.",
                    phase=IndexPhase.PARSE,
                    recoverable=True,
                    severity=DiagnosticSeverity.WARNING,
                    repo_relative_path=pf.file_path,
                )
                diagnostics.append(wdiag)

            symbol_count += len(pf.symbols)

        # ── CHUNKING ────────────────────────────────────────────────────────

        sm.transition(IndexState.CHUNKING)

        chunks: list[CodeChunk] = []
        try:
            chunks = self._chunker.chunk(scan_result.files, parsed_files)
        except BaseException:
            diag = IndexDiagnostic(
                code="chunk_failed",
                message="Semantic chunk creation failed.",
                phase=IndexPhase.CHUNK,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            diagnostics.append(diag)
            compat_errors.append(diag.message)
            return self._build_fatal(
                sm, diagnostics, compat_errors, IndexState.ERROR,
                scan_result=scan_result, parsed_files=parsed_files,
            )

        chunk_valid = self._validate_chunks(chunks, scan_result.files)
        if chunk_valid is not None:
            diag, compat = chunk_valid
            diagnostics.append(diag)
            compat_errors.append(compat)
            return self._build_fatal(
                sm, diagnostics, compat_errors, IndexState.ERROR,
                scan_result=scan_result, parsed_files=parsed_files,
            )

        # ── Counts ──────────────────────────────────────────────────────────

        scanned_count = scan_result.eligible_file_count
        counts = IndexCounts(
            scanned=scanned_count,
            parsed=parse_ok_count,
            chunks=len(chunks),
            parse_errors=parse_err_count,
            symbols=symbol_count,
            warnings=len([d for d in diagnostics if d.severity == DiagnosticSeverity.WARNING]),
            errors=len([d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]),
        )

        run_result = IndexRunResult(
            state=sm.state,
            phase=sm.phase,
            counts=counts,
            diagnostics=diagnostics,
            errors=compat_errors,
        )

        counts.validate()
        run_result.validate()
        for d in diagnostics:
            d.validate()

        return IndexBuildResult(
            run_result=run_result,
            completed_phase=sm.completed_phase,
            state_history=sm.history,
            persistent_replacement_started=sm.persistent_replacement_started,
            scan_result=scan_result,
            parsed_files=parsed_files,
            chunks=chunks,
            embedding_result=None,
            graph_result=None,
        )

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _validate_config(
        config: FCodeConfig,
    ) -> Optional[tuple[IndexDiagnostic, str]]:
        path = config.repo_path
        if not path or not isinstance(path, str):
            d = IndexDiagnostic(
                code=ErrorCode.INVALID_REPOSITORY_PATH.value,
                message="Repository path is missing or is not a readable directory.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        p = Path(path)
        if not p.exists():
            d = IndexDiagnostic(
                code=ErrorCode.INVALID_REPOSITORY_PATH.value,
                message="Repository path is missing or is not a readable directory.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        if not p.is_dir():
            d = IndexDiagnostic(
                code=ErrorCode.INVALID_REPOSITORY_PATH.value,
                message="Repository path is missing or is not a readable directory.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        if not os.access(str(p), os.R_OK | os.X_OK):
            d = IndexDiagnostic(
                code="permission_denied",
                message="Repository path is not readable.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        max_files = config.max_files
        if isinstance(max_files, bool) or not isinstance(max_files, int):
            d = IndexDiagnostic(
                code="config_invalid",
                message="max_files must be a positive integer.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message
        if max_files <= 0:
            d = IndexDiagnostic(
                code="config_invalid",
                message="max_files must be a positive integer.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        max_bytes = config.max_size_bytes
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
            d = IndexDiagnostic(
                code="config_invalid",
                message="max_size_bytes must be a positive integer.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message
        if max_bytes <= 0:
            d = IndexDiagnostic(
                code="config_invalid",
                message="max_size_bytes must be a positive integer.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        return None

    @staticmethod
    def _validate_scan_result(
        result: ScanResult,
        config: FCodeConfig,
    ) -> Optional[tuple[IndexDiagnostic, str]]:
        if not isinstance(result, ScanResult):
            d = IndexDiagnostic(
                code=ErrorCode.SCAN_FAILED.value,
                message="Scanner returned an invalid result type.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        files = result.files
        seen_ids: set[str] = set()
        seen_paths: set[str] = set()

        for sf in files:
            if not sf.file_id:
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned a file without an ID.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if sf.file_id in seen_ids:
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned duplicate file IDs.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            seen_ids.add(sf.file_id)

            if not sf.file_path:
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned a file without a path.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if sf.file_path.startswith("/") or sf.file_path.startswith("\\"):
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned an absolute file path.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if ".." in sf.file_path.split("/"):
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned a path with '..' traversal.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if "\\" in sf.file_path:
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned a path with backslash separators.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if sf.file_path in seen_paths:
                d = IndexDiagnostic(
                    code=ErrorCode.SCAN_FAILED.value,
                    message="Scanner returned duplicate file paths.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            seen_paths.add(sf.file_path)

        ec = result.eligible_file_count
        if ec != len(files):
            d = IndexDiagnostic(
                code=ErrorCode.SCAN_FAILED.value,
                message="Scanner eligible_file_count does not match files length.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        tc = result.total_count
        if tc != len(files):
            d = IndexDiagnostic(
                code=ErrorCode.SCAN_FAILED.value,
                message="Scanner total_count does not match files length.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        if result.eligible_file_count < 0:
            d = IndexDiagnostic(
                code=ErrorCode.SCAN_FAILED.value,
                message="Scanner eligible_file_count is negative.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        if result.eligible_total_bytes < 0:
            d = IndexDiagnostic(
                code=ErrorCode.SCAN_FAILED.value,
                message="Scanner eligible_total_bytes is negative.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        # Repository limit checks
        if result.eligible_file_count > config.max_files:
            d = IndexDiagnostic(
                code=ErrorCode.REPOSITORY_LIMIT_EXCEEDED.value,
                message="Repository exceeds maximum file count.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        if result.eligible_total_bytes > config.max_size_bytes:
            d = IndexDiagnostic(
                code=ErrorCode.REPOSITORY_LIMIT_EXCEEDED.value,
                message="Repository exceeds maximum content size.",
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        for sk in result.skipped:
            if sk.reason == "repository_limit_exceeded":
                d = IndexDiagnostic(
                    code=ErrorCode.REPOSITORY_LIMIT_EXCEEDED.value,
                    message="Repository exceeds indexing limits.",
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

        return None

    @staticmethod
    def _convert_scanner_warnings(
        scan_result: ScanResult,
    ) -> list[IndexDiagnostic]:
        result: list[IndexDiagnostic] = []
        for w in scan_result.warnings:
            if not isinstance(w, dict):
                result.append(IndexDiagnostic(
                    code=ErrorCode.FILE_SKIPPED.value,
                    message="A file was skipped during scanning.",
                    phase=IndexPhase.SCAN,
                    recoverable=True,
                    severity=DiagnosticSeverity.WARNING,
                ))
                continue
            code = w.get("code") or ErrorCode.FILE_SKIPPED.value
            if not isinstance(code, str):
                code = ErrorCode.FILE_SKIPPED.value
            msg = w.get("message") or "A file was skipped during scanning."
            if not isinstance(msg, str):
                msg = "A file was skipped during scanning."
            msg = msg[:500]
            raw_path = w.get("repo_relative_path") or w.get("path") or w.get("file_path")
            safe_path: Optional[str] = None
            if isinstance(raw_path, str) and raw_path:
                if (not raw_path.startswith("/")
                        and not raw_path.startswith("\\")
                        and ".." not in raw_path.split("/")):
                    safe_path = raw_path.replace("\\", "/")
            result.append(IndexDiagnostic(
                code=code,
                message=msg,
                phase=IndexPhase.SCAN,
                recoverable=True,
                severity=DiagnosticSeverity.WARNING,
                repo_relative_path=safe_path,
            ))
        return result

    @staticmethod
    def _validate_parse_result(
        pf: ParsedFile,
        sf: ScannedFile,
    ) -> Optional[tuple[IndexDiagnostic, str]]:
        if not isinstance(pf, ParsedFile):
            d = IndexDiagnostic(
                code=ErrorCode.PARSE_FAILED.value,
                message="Parser returned an invalid result type.",
                phase=IndexPhase.PARSE,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message
        if pf.file_id != sf.file_id:
            d = IndexDiagnostic(
                code=ErrorCode.PARSE_FAILED.value,
                message="Parser returned mismatched file ID.",
                phase=IndexPhase.PARSE,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message
        if pf.file_path != sf.file_path:
            d = IndexDiagnostic(
                code=ErrorCode.PARSE_FAILED.value,
                message="Parser returned mismatched file path.",
                phase=IndexPhase.PARSE,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message
        if pf.status not in (ParseStatus.PARSED, ParseStatus.ERROR, ParseStatus.NOT_APPLICABLE):
            d = IndexDiagnostic(
                code=ErrorCode.PARSE_FAILED.value,
                message="Parser returned a file with PENDING status.",
                phase=IndexPhase.PARSE,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        seen_sym: set[str] = set()
        for sym in pf.symbols:
            if not sym.symbol_id:
                d = IndexDiagnostic(
                    code=ErrorCode.PARSE_FAILED.value,
                    message="Parser returned a symbol without an ID.",
                    phase=IndexPhase.PARSE,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if sym.symbol_id in seen_sym:
                d = IndexDiagnostic(
                    code=ErrorCode.PARSE_FAILED.value,
                    message="Parser returned duplicate symbol IDs.",
                    phase=IndexPhase.PARSE,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            seen_sym.add(sym.symbol_id)

        seen_route: set[str] = set()
        for rt in pf.routes:
            if not rt.route_id:
                d = IndexDiagnostic(
                    code=ErrorCode.PARSE_FAILED.value,
                    message="Parser returned a route without an ID.",
                    phase=IndexPhase.PARSE,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if rt.route_id in seen_route:
                d = IndexDiagnostic(
                    code=ErrorCode.PARSE_FAILED.value,
                    message="Parser returned duplicate route IDs.",
                    phase=IndexPhase.PARSE,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            seen_route.add(rt.route_id)

        return None

    @staticmethod
    def _validate_chunks(
        chunks: list[CodeChunk],
        scanned_files: Sequence[ScannedFile],
    ) -> Optional[tuple[IndexDiagnostic, str]]:
        if not isinstance(chunks, list):
            d = IndexDiagnostic(
                code="chunk_failed",
                message="Chunker returned an invalid result type.",
                phase=IndexPhase.CHUNK,
                recoverable=False,
                severity=DiagnosticSeverity.ERROR,
            )
            return d, d.message

        scanned_ids = {sf.file_id for sf in scanned_files}
        scanned_paths = {sf.file_path for sf in scanned_files}
        seen_ids: set[str] = set()

        for ch in chunks:
            if not isinstance(ch, CodeChunk):
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a non-CodeChunk item.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

            if not ch.chunk_id:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a chunk without an ID.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if ch.chunk_id in seen_ids:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned duplicate chunk IDs.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            seen_ids.add(ch.chunk_id)

            if ch.file_id not in scanned_ids:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker referenced unknown file ID.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

            if ch.file_path not in scanned_paths:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker referenced unknown file path.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

            fp = ch.file_path
            if fp.startswith("/") or fp.startswith("\\"):
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned an absolute file path.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if ".." in fp.split("/"):
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a path with '..' traversal.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if "\\" in fp:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a path with backslash separators.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

            if ch.start_line < 1:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a chunk with invalid start_line.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message
            if ch.end_line < ch.start_line:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a chunk with end_line < start_line.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

            if not isinstance(ch.content, str) or not ch.content.strip():
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a chunk with empty content.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

            expected_hash = hashlib.sha256(ch.content.encode("utf-8")).hexdigest()
            if ch.content_hash and ch.content_hash != expected_hash:
                d = IndexDiagnostic(
                    code="chunk_failed",
                    message="Chunker returned a chunk with incorrect content hash.",
                    phase=IndexPhase.CHUNK,
                    recoverable=False,
                    severity=DiagnosticSeverity.ERROR,
                )
                return d, d.message

        return None

    @staticmethod
    def _build_fatal(
        sm: IndexStateMachine,
        diagnostics: list[IndexDiagnostic],
        compat_errors: list[str],
        final_state: IndexState,
        scan_result: Optional[ScanResult],
        parsed_files: Optional[list[ParsedFile]] = None,
    ) -> IndexBuildResult:
        if sm.state != IndexState.ERROR:
            sm.fail()

        fatal_count = len([d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR and not d.recoverable])
        warn_count = len([d for d in diagnostics if d.severity == DiagnosticSeverity.WARNING])

        counts = IndexCounts(
            warnings=warn_count,
            errors=fatal_count,
        )

        run_result = IndexRunResult(
            state=IndexState.ERROR,
            phase=sm.phase,
            counts=counts,
            diagnostics=diagnostics,
            errors=compat_errors,
        )

        return IndexBuildResult(
            run_result=run_result,
            completed_phase=sm.completed_phase,
            state_history=sm.history,
            persistent_replacement_started=sm.persistent_replacement_started,
            scan_result=scan_result,
            parsed_files=parsed_files or [],
            chunks=[],
            embedding_result=None,
            graph_result=None,
        )
