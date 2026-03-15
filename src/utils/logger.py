"""
utils/logger.py
~~~~~~~~~~~~~~~
Centralised logging for MemoShot.

Features
--------
- Single root logger shared across all modules via get_logger(name).
- Timestamped rotating log files: log_memoshot_YYYYMMDD_HHMMSS.txt
  (max 1 MB per file, 5 rotating backups kept).
- Separate console handler for development feedback.
- Runtime on/off toggle via apply_log_settings(settings).
- Log level configurable between DEBUG and INFO.
- Safe to call get_logger() before apply_log_settings() — the logger
  is created immediately; the file handler is added later.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# ── Module-level state ────────────────────────────────────────────────────────

_LOG_NAME      = "memoshot"
_file_handler: Optional[RotatingFileHandler] = None
_console_handler: Optional[logging.StreamHandler] = None
_current_log_path: Optional[str] = None

# Format used by all handlers
_FMT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the 'memoshot' root.
    Safe to call from any module at import time.
    """
    root = logging.getLogger(_LOG_NAME)
    # Ensure the root logger has at least a NullHandler so it never
    # prints "No handlers could be found" warnings before configuration.
    if not root.handlers:
        root.addHandler(logging.NullHandler())
        root.setLevel(logging.DEBUG)   # root level open; handlers filter
    return logging.getLogger(f"{_LOG_NAME}.{name}")


def apply_log_settings(settings: dict) -> None:
    """
    Configure (or reconfigure) all log handlers based on the settings dict.

    Called once at startup from app.py and again whenever the user changes
    logging settings in the UI.

    Keys read from settings
    -----------------------
    logging_enabled : bool  — master switch
    log_folder      : str   — directory for log files (created if absent)
    log_level       : str   — "DEBUG" or "INFO"
    """
    global _file_handler, _console_handler, _current_log_path

    root = logging.getLogger(_LOG_NAME)

    # Remove any existing handlers cleanly
    for h in root.handlers[:]:
        try:
            h.flush()
            h.close()
        except Exception:
            pass
        root.removeHandler(h)
    _file_handler    = None
    _console_handler = None

    enabled = settings.get("logging_enabled", True)
    if not enabled:
        root.addHandler(logging.NullHandler())
        return

    level_name = settings.get("log_level", "INFO").upper()
    level = logging.DEBUG if level_name == "DEBUG" else logging.INFO
    root.setLevel(logging.DEBUG)   # root always open; handlers filter by level

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # ── File handler ──────────────────────────────────────────────────────────
    # Resolve folder: treat empty string as "use default"
    raw_folder = settings.get("log_folder", "")
    log_folder = raw_folder.strip() if raw_folder else _default_log_folder()
    try:
        os.makedirs(log_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path  = os.path.join(log_folder, f"log_memoshot_{timestamp}.txt")
        _current_log_path = log_path

        fh = RotatingFileHandler(
            log_path,
            maxBytes=1_048_576,   # 1 MB
            backupCount=5,
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root.addHandler(fh)
        _file_handler = fh
    except Exception as exc:
        # Could not create the log file — fall back to console-only
        _current_log_path = None
        root.addHandler(logging.NullHandler())
        logging.getLogger(_LOG_NAME).warning(
            f"Could not create log file in {log_folder}: {exc}"
        )

    # ── Console handler (always on when logging enabled) ──────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    root.addHandler(ch)
    _console_handler = ch

    root.info(
        f"Logging started — level={level_name}  file={_current_log_path}"
    )


def current_log_path() -> Optional[str]:
    """Return the path of the current log file, or None if logging is off."""
    return _current_log_path


def _default_log_folder() -> str:
    """
    Default log folder: a 'Logs' sub-directory next to the running script,
    i.e. <project_root>/src/Logs/ when run as 'python src/main.py'.
    Falls back to ~/.memoshot/Logs if the script dir is not writable.
    """
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        # __file__ is utils/logger.py — go up two levels to reach src/
        src_dir = os.path.dirname(base)
        candidate = os.path.join(src_dir, "Logs")
        # Quick write-test
        os.makedirs(candidate, exist_ok=True)
        return candidate
    except Exception:
        return os.path.join(os.path.expanduser("~"), ".memoshot", "Logs")
