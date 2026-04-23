"""Enable ``python -m pos_amend <subcommand>`` invocation."""

from __future__ import annotations

from pos_amend.cli import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
