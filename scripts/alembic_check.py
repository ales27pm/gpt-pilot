#!/usr/bin/env python3
"""Pre-commit hook to run Alembic check, skipping if database unavailable."""

from alembic import command
from alembic.config import Config
from sqlalchemy.exc import OperationalError


def main() -> int:
    cfg = Config("core/db/alembic.ini")
    try:
        command.check(cfg)
    except OperationalError:
        print("Skipping alembic check: database not available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
