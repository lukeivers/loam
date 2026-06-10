"""loam — unified top-level CLI for the loam framework.

The ``loam`` binary dispatches to subcommands via argparse subparsers.
The dev-sdlc plugin contributes the ``amend`` subcommand (the
amendment-dispatch tooling); the top-level dispatcher reserves
namespace for future subcommands like ``loam scope new``,
``loam status``, ``loam plot create``.
"""

__version__ = "1.5.0"
