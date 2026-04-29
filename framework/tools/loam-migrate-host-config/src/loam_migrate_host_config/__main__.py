"""``python -m loam_migrate_host_config`` entry point — delegates to ``cli.main``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
