"""``python -m heavy_b_migrate`` entry point — delegates to the CLI."""

from heavy_b_migrate.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
