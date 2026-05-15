# subloam-driver

Isolated sub-loam test-instance driver. Part 2 of the
`loam-init-persona-wiring-and-isolated-subloam-driver` MINOR amendment.

Stands up a fresh persona-active loam workspace via the production
bootstrap path (made persona-active by Part 1's first-run scaffold
extension), then drives an **interactive** `claude` session inside it
over a PTY harness — fed a **frozen** `build_prompt` as the first user
turn (unchanged; no substitution, no `--append-system-prompt`; owner
constraint for bench + paper integrity).

## The one isolation mechanism (AC.LIPW.6)

A single `IsolationConfig` object drives BOTH:

- **operator-protection** — the operator's telegram/bun poller is
  never SIGTERM'd: no telegram plugin reachable → no competing
  `bun server.ts` → the sole kill vector (plan §2 point 9) is removed;
  isolated `CLAUDE_CONFIG_DIR` → the operator's bot token /
  plugin-cache singleton is unreachable; namespaced workspace slug +
  `service_bootstrap=False` → no launchd collision.
- **bench-validity** — empty MCP (`--strict-mcp-config --mcp-config
  <empty>`) + isolated config + no channels → the measured behaviour
  is loam-the-persona-and-loop, not loam-plus-the-operator's ambient
  environment.

These are not coordinated; they fall out of the same fields. There is
no second isolation surface.

## Usage

    subloam-driver \
        --scratch-root /tmp/pb-subloam-<task>-<ts> \
        --from /Users/lukeivers/loam \
        --slug pb-subloam-<task>-<ts> \
        --prompt-file <frozen-build-prompt.txt>

NO Anthropic API key — the real `claude` binary, default Sonnet
(`feedback_no_anthropic_api_key`). Stdlib-only.
