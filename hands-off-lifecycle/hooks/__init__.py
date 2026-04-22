"""hands-off-lifecycle hook surfaces.

Phase-5-second-component: ``true-first-run`` installs here because
first-run is hands-off-lifecycle's mechanical prerequisite — the
supervisor the hook fragment describes only becomes invokable once
first-run has built the venv it needs.

Modules:
    first_run_inventory — stdlib-only YAML-subset parser for
        ``first-run-inventory.yaml``.
    first_run_settings  — .claude/settings.json stanza-specific merge.
    first_run_helper    — entry point invoked by ``first-run.sh``.
"""
