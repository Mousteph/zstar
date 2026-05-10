from __future__ import annotations

import traceback
from pathlib import Path
from traceback import FrameSummary
from typing import Optional
from typing import Tuple


class StrategyValidationErrorFormatter:
    def __init__(self, strategy_filename: str, strategy_path: Optional[Path] = None):
        self.strategy_filename = strategy_filename
        self.strategy_path = strategy_path

    def format_syntax_error(self, error: SyntaxError, code: str) -> Tuple[str, Optional[int]]:
        line = error.lineno if isinstance(error.lineno, int) else None
        column = error.offset if isinstance(error.offset, int) else None
        file_name = error.filename or self.strategy_filename

        lines = [
            "Strategy failed to load (SyntaxError)",
            f"File        : {file_name}",
            f"Line        : {line if line is not None else 'N/A'}",
            f"Column      : {column if column is not None else 'N/A'}",
            f"Error       : {error.msg}",
        ]

        context = self._code_context(code, line, column)
        if context:
            lines.extend(["", context])

        return "\n".join(lines), line

    def format_exception_detail(
        self,
        error: Exception,
        code: Optional[str],
    ) -> Tuple[str, Optional[int], str]:
        extracted = traceback.extract_tb(error.__traceback__)
        frame = self._select_relevant_frame(extracted)

        file_name = frame.filename if frame else self.strategy_filename
        line = frame.lineno if frame else None
        where = frame.name if frame else "N/A"
        error_text = str(error) if str(error) else repr(error)

        lines = [
            f"Strategy execution failed ({type(error).__name__})",
            f"File        : {file_name}",
            f"Line        : {line if line is not None else 'N/A'}",
            f"Where       : {where}",
            f"Error       : {error_text}",
        ]

        context = self._resolve_code_context(file_name, line, code)
        if context:
            lines.extend(["", context])

        if error.args:
            lines.append("")
            lines.append("Exception args:")
            for idx, arg in enumerate(error.args, 1):
                lines.append(f"  [{idx}] {repr(arg)}")

        return "\n".join(lines), line, file_name

    def _select_relevant_frame(self, frames: list[FrameSummary]) -> Optional[FrameSummary]:
        if not frames:
            return None

        if self.strategy_path is not None:
            root = self.strategy_path.parent.resolve()
            for frame in reversed(frames):
                try:
                    Path(frame.filename).resolve().relative_to(root)
                    return frame
                except ValueError:
                    continue

        for frame in reversed(frames):
            if frame.filename == self.strategy_filename:
                return frame

        return frames[-1]

    def _resolve_code_context(self, file_name: str, line: Optional[int], code: Optional[str]) -> str:
        if line is None:
            return ""

        if code is not None and file_name == self.strategy_filename:
            return self._code_context(code, line)

        if self.strategy_path is not None and file_name == str(self.strategy_path):
            try:
                source = self.strategy_path.read_text(encoding="utf-8")
            except OSError:
                return ""
            return self._code_context(source, line)

        path = Path(file_name)
        if not path.is_file():
            return ""

        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            return ""

        return self._code_context(source, line)

    def _code_context(self, source: str, line: Optional[int], column: Optional[int] = None, radius: int = 2) -> str:
        if line is None:
            return ""

        rows = source.splitlines()
        if not rows:
            return ""

        start = max(1, line - radius)
        end = min(len(rows), line + radius)
        lines = ["Code context:"]

        for idx in range(start, end + 1):
            marker = ">>" if idx == line else "  "
            lines.append(f"{marker} {idx:>4} | {rows[idx - 1]}")
            if idx == line and column is not None and column > 0:
                lines.append(f"      | {' ' * (column + 1)}^")

        return "\n".join(lines)
