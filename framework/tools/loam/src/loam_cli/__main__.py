"""Enable ``python -m loam_cli <subcommand>`` invocation."""

from __future__ import annotations

from loam_cli.cli import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
