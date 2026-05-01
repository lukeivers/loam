# Security policy

loam takes security reports seriously. This document describes how to
report a vulnerability, what to expect after you report, and what
falls inside the project's security scope.

## Reporting a vulnerability

**Preferred channel — GitHub Security Advisories.** Use GitHub's
private vulnerability reporting feature on the loam repository:

1. Navigate to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Fill in the advisory form with reproduction steps, affected
   versions, and any proof-of-concept material.

GitHub Security Advisories let the maintainer collaborate with you
privately on a fix, draft a coordinated disclosure timeline, and
publish a CVE if warranted — without the report being publicly
visible during triage.

**Fallback channel.** If GitHub Security Advisories is not available
to you for any reason, open a minimal placeholder issue titled
"security: please contact me privately" (no details in the public
issue) and wait for the maintainer to reach out with a private
channel.

**Do not** report vulnerabilities through the public issue tracker,
public discussion forums, or social media. Public disclosure before
a fix is available puts users at risk.

## What to include in a report

A useful security report includes:

- **A clear description of the vulnerability** — what the issue is,
  not just what the symptom looks like.
- **Affected versions** — at minimum, the loam release tag (or
  commit SHA) where you observed the issue.
- **Reproduction steps** — minimal, deterministic. If a step depends
  on environment, name the environment.
- **Impact assessment** — what an attacker could do, what data is at
  risk, what privileges are required.
- **Suggested mitigation, if any** — optional; the maintainer will
  triage the fix shape regardless.

If you have a proof-of-concept, attach it to the advisory. If the
proof-of-concept itself contains sensitive data (real credentials,
real personal information), redact before sharing.

## What to expect after you report

The maintainer is one person on a personal account. The cadence
below is the target; real life sometimes shifts it.

| Step | Target turnaround |
|------|-------------------|
| Acknowledge receipt of the report | within 5 business days |
| First triage assessment (severity + scope) | within 14 days |
| Coordinated-disclosure timeline proposed | within 30 days |
| Fix landed (severity-dependent) | 30–90 days for high-severity; longer for lower |
| Public disclosure (advisory + CVE if warranted) | after fix lands, coordinated with reporter |

If you have not heard back within the acknowledge-receipt window,
the report may not have reached the maintainer. Use the GitHub
Security Advisories channel rather than relying on email; the
advisories surface in the maintainer's notification flow more
reliably.

If a vulnerability is **actively being exploited in the wild**, name
that in the report. Active exploitation shortens every step in the
table above.

## Disclosure policy

loam practices **coordinated disclosure**. The maintainer and the
reporter agree on a public-disclosure date together; that date is
typically when the fix lands plus a short embargo window for users
to upgrade. The reporter is credited in the advisory unless they
prefer otherwise.

Public disclosure includes:

- a GitHub Security Advisory entry with the affected versions, the
  fix version, and a description of the vulnerability,
- a CVE if the issue qualifies and the reporter has not already
  filed one,
- a release note in the patched version that names the advisory.

## In-scope

The following are in-scope for security reports:

- **Runtime components** shipped in `framework/` — every component
  listed in [`docs/components/index.md`](docs/components/index.md).
- **The Dev/SDLC plugin** shipped at v0.1.0.
- **The `loam` CLI binary** and its subcommands.
- **Workspace-bootstrap's first-run scaffolding** — anything the
  bootstrap touches on a fresh machine.
- **The memory primitive** — file read/write paths the persona uses
  at SessionStart and Stop.

## Out-of-scope

The following are **not** in scope for the loam security policy. They
are real concerns; they are someone else's responsibility.

- **Vulnerabilities in upstream dependencies.** Report those to the
  upstream project. If a dependency vulnerability is actively
  affecting loam users, the maintainer will track and update — but
  the report goes upstream first.
- **Vulnerabilities in Claude itself, the Claude Code CLI, or the
  Anthropic SDK.** Report those to Anthropic via their security
  channels. loam composes on Claude; loam does not own Claude.
- **Vulnerabilities in your operating system, your shell, your
  hardware, or your browser.** loam runs in those environments; it
  does not vouch for them.
- **Issues that require a malicious user to already have control of
  the workspace.** A workspace under attacker control is a different
  threat model than the one loam guards against.
- **Reports that amount to "this design is bad."** Open a regular
  issue; design feedback is welcome but it is not a security report.

## Bounties

loam does not offer a bug-bounty programme. The project is run by
one person on a personal account; there is no budget for bounties at
v0.1.0. Reporters are credited in advisories.

If you are looking for paid security research targets, loam is not
the right project. If you found something here while doing other
work and want to report it anyway, that is generously appreciated
and acknowledged in the advisory.

## Where to go next

- [`README.md`](README.md) — project overview and quickstart.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — non-security contribution
  workflow.
- [`LICENSE`](LICENSE) — Apache-2.0.
