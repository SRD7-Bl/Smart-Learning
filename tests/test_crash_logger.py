from __future__ import annotations

import sys
import threading

from Backend.Crash_Logger import install_crash_logger, write_crash_log


def test_crash_log_records_traceback_without_frame_locals(tmp_path) -> None:
    secret_value = "must-not-appear-in-crash-log"

    try:
        raise RuntimeError("test failure")
    except RuntimeError:
        exception_type, exception, exception_traceback = sys.exc_info()

    report_path = write_crash_log(
        exception_type,
        exception,
        exception_traceback,
        log_dir=tmp_path,
    )

    assert report_path is not None
    report = report_path.read_text(encoding="utf-8")
    assert "Smart Learning crash report" in report
    assert "Exception: RuntimeError" in report
    assert "RuntimeError: test failure" in report
    assert secret_value not in report


def test_installed_exception_hook_writes_a_crash_log(tmp_path) -> None:
    original_exception_hook = sys.excepthook
    original_thread_hook = threading.excepthook
    sys.excepthook = lambda *_args: None

    try:
        install_crash_logger(log_dir=tmp_path)
        try:
            raise ValueError("hook failure")
        except ValueError:
            sys.excepthook(*sys.exc_info())
    finally:
        sys.excepthook = original_exception_hook
        threading.excepthook = original_thread_hook

    reports = list(tmp_path.glob("crash-*.log"))
    assert len(reports) == 1
    assert "ValueError: hook failure" in reports[0].read_text(encoding="utf-8")
