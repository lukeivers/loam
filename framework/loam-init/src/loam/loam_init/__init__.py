# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""loam-init — `loam init` subcommand for the unified loam CLI.

Public surface:

    build_init_subcommand     — argparse subparser builder; registered
                                via `loam.cli.subcommands` entry-point
                                group (`init`) in pyproject.toml.

The builder constructs an argparse parser whose default action wraps
``loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace`` —
the existing fresh-workspace bootstrap primitive. Composition only;
``loam-init`` adds no scaffolding logic of its own.
"""

from .cli import build_init_subcommand

__version__ = "0.8.0"

__all__ = ["build_init_subcommand", "__version__"]
