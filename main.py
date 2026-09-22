"""Application entry point for Smart Learning."""

from Backend.Crash_Logger import install_crash_logger


if __name__ == "__main__":
    install_crash_logger()
    from Frontend.App_Window import run_app

    raise SystemExit(run_app())
