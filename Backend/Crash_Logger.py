"""Write uncaught Python exceptions to local crash-report files."""

from __future__ import annotations

import platform
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Type

from Backend.Storage_Paths import default_log_dir


def write_crash_log(
    exception_type: Type[BaseException],
    exception: BaseException,
    exception_traceback: TracebackType | None,
    log_dir: Path | None = None,
    thread_name: str | None = None,
) -> Path | None:
    """Persist an uncaught exception without including stack-frame local values."""
    try:
        target_dir = log_dir or default_log_dir()
        occurred_at = datetime.now().astimezone()
        filename = f"crash-{occurred_at.strftime('%Y%m%d-%H%M%S-%f')}.log"
        report_path = target_dir / filename
        thread_line = f"Thread: {thread_name}\n" if thread_name else ""
        report = (
            "Smart Learning crash report\n"
            f"Time: {occurred_at.isoformat(timespec='seconds')}\n"
            f"Platform: {platform.platform()}\n"
            f"Python: {platform.python_version()}\n"
            f"Exception: {exception_type.__name__}\n"
            f"{thread_line}\n"
            + "".join(traceback.format_exception(exception_type, exception, exception_traceback))
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
    except Exception:
        return None

    return report_path


def install_crash_logger(log_dir: Path | None = None) -> None:
    """Install handlers for uncaught exceptions on the main and worker threads."""
    original_exception_hook = sys.excepthook
    original_thread_hook = threading.excepthook

    def handle_exception(
        exception_type: Type[BaseException],
        exception: BaseException,
        exception_traceback: TracebackType | None,
    ) -> None:
        write_crash_log(exception_type, exception, exception_traceback, log_dir=log_dir)
        original_exception_hook(exception_type, exception, exception_traceback)

    def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        write_crash_log(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            log_dir=log_dir,
            thread_name=args.thread.name if args.thread else None,
        )
        original_thread_hook(args)

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception
