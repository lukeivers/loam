"""``python -m loam_migrate_dormancy_config`` entry-point."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
