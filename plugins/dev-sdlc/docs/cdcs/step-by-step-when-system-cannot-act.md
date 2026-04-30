# Core Development Convention — step-by-step when the system cannot act

> **When the system cannot do a step on the user's behalf, it produces exact step-by-step instructions for that step — not advice, not encouragement to figure it out, not a link to documentation.**

Rationale. The fourth lens's aspiration is zero manual steps. Physical reality sometimes prevents it — a third-party service whose API key belongs to the user is literally impossible for the system to obtain for them. The pragmatic rule is a three-tier gradient, not a binary:

1. **Silent** when possible. The system does it.
2. **Step-by-step instructions** when impossible. Numbered, unambiguous, with expected time ("this takes about two minutes"). No narrative, no "and then you'll want to...," no implicit steps that presume the user understands the system's architecture. The instructions are a concrete, testable product — if a reader follows them verbatim, the step gets done.
3. **Loud failure** when even instructions aren't enough. Named diagnostic, contact surface.

Step-by-step instructions carry the same discipline as code: they are authored with specific target users in mind, they are tested (can a non-technical reader follow them without asking for clarification?), and they are updated when their environment changes. "See the documentation" is not instructions; it is a non-answer.

Applied to every future feature that interacts with user-owned external surfaces (Telegram bot tokens, OAuth flows, API keys for paid services, service-account creation on cloud providers, etc.).
