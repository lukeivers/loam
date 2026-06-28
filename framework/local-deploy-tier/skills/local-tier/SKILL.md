---
name: local-tier
description: The LOCAL deploy tier runbook (P1 of the dev->build->deploy spine). Invoke when a non-technical owner expresses plain intent to run, build, or check their project on their own machine ("run it", "is it working", "build it locally", "give me a clean copy"). Brings up + verifies the project against the LOCAL environment profile, produces a shared-shape Acceptance record judged by an independent check, surfaces the backing-service parity gap against any downstream environment in plain language, and keeps every LOCAL secret in the OS keychain (never a repo-committed file). The sealed deploy-safety floor stays idle at LOCAL because no irreversible action exists here. Does NOT publish, promote, or deploy anywhere remote — that is a separate, owner-asked step the higher tiers (P2/P3) own.
---

# LOCAL deploy tier (P1)

The owner brings WHAT ("run it on my machine", "is it working"); this tier owns
HOW. The substance is always exposed in plain words; only the vocabulary
adapts (Lens 0). Nothing here crosses the deploy boundary — LOCAL builds and
verifies, it never ships.

## The verbs LOCAL enables

`build` · `verify` · `run` · `migrate` · `seed` · `reset` · `status` · `open`.

Every one is reversible or inspect-only at LOCAL; the local database is
disposable, so even `reset` is a free undo. There is deliberately **no**
`promote` / `deploy-prod` / `provision` / `destroy` verb — those belong to the
higher tiers. Because no irreversible action is reachable, the sealed
deploy-safety floor has nothing to gate and stays idle (AC.LOCAL.2).

## What a LOCAL build does (the entry-point)

`loam.local_deploy_tier.build.build_local(workspace_root)`:

1. Reads the additive `role` / `backing_services` fields from the project's
   `deploy.yaml` / `.loam/environments.yaml` — the same file the floor reads,
   the extra fields it ignores (a strict additive superset, P0 §5.1).
2. Runs the project's own declared check (`.loam/local-tier.yaml` →
   `verify_command`) as a real subprocess and produces a shared-shape
   **Acceptance** record from its actual verdict. A failing check is an honest
   "not done yet, here is why" — never retried to green (AC.LOCAL.1).
3. Surfaces, in plain language, where this machine differs from any downstream
   environment's backing services (engine / version gaps) **before** any
   promotion is offered. A clean diff still carries the honest caveat that a
   local machine is never identical to the live setup (AC.LOCAL.3).
4. Reports a plain-language status: what ran, what it touched, that nothing is
   public.

## Secrets at LOCAL

A LOCAL secret lives in the operating system's keychain
(`loam.local_deploy_tier.secrets.LocalSecretStore`), **never** a file under the
repository — so there is nothing for `git add` to capture. This composes on the
secure-build baseline's secrets-never-committed boundary: the secret is removed
from disk-under-repo at the source, not only caught at the commit gate
(AC.LOCAL.4). The store never prints a resolved secret value.

## The destructive-action rule (carries to the higher tiers)

The destructiveness is in the **target**, not the verb. A `reset` / `drop` /
`truncate` against a provably-local target is a free undo — the guard warns
("this wipes your local copy"), then proceeds. The identical operation against
a target that is **not** provably local is handed to the sealed floor, which
gates it. When the target is unknown, the guard fails closed (treats it as
non-local). This is the single highest-stakes design point the LOCAL tier hands
forward.
