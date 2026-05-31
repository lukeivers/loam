# Doctrine enshrinement inserts — for owner verification

*Two exact, ready-to-paste inserts assembled 2026-05-31 from `loam-doctrine.md`.
Both are PROPOSED wording, pending the owner's single-pass verification.
Enshrinement is owner-gated — do not paste either into the live document until
the owner approves the wording.*

- **Insert A** slots into `docs/VALUE_PROPOSITION.md` as a new prime-objective
  section, placed at the very top of the document body (immediately after the
  opening two-paragraph preamble, before `## The problem loam is closing`).
- **Insert B** slots into the project `CLAUDE.md` as a new first design lens,
  **Lens 0**, placed ahead of the existing Lens 1 (and the count of "Seven
  principles" in the intro should be updated to reflect the new prime lens — see
  the note after Insert B).

Each insert matches its host document's existing voice and format.

---

## Insert A — `VALUE_PROPOSITION.md` prime-objective section

```markdown
## The prime objective — per-user-tuned translation

Everything else in this document serves one objective, and the two tests below
are the acceptance criteria of it.

AI only becomes truly useful to a person when it is tuned to that specific
person. Everyone leans on AI differently — to cover what they are weak at or do
not enjoy, so they can spend themselves on what they love. So loam's job is never
merely to execute. It is to continuously learn the specific user and translate
what they want — customised to them — down into the underlying machinery: the
frontier model, Claude Code, whatever sits beneath. The user only ever has to
know *what* they need; loam owns *how* to make it happen.

This sharpens the translation-layer framing the rest of this document develops.
That framing already said the persona "translates user intent into AI-effective
execution." The piece that makes it true is that the translation must be learned
and customised per person, continuously — the same request does not translate the
same way for two different people. Per-user-learned translation is not a footnote
on loam's value; it is loam's value.

loam runs this through a four-step loop, and the loop is what loam adds on top of
a raw model. A raw model turns the user's words into a good one-shot answer. loam
turns them into an action-oriented end-intent and proposes a healthy way to reach
it: (1) infer the real end-intent behind the literal ask; (2) design a healthy
way to enable it — should it recur? does it need a framework? should it be
deterministic?; (3) surface that back to the user to check it; (4) learn from the
answer, then repeat. The inferred intent is always a hypothesis we surface, never
an assumption we silently build on; verification both corrects the hypothesis and
teaches the per-user model the next inference draws on. The guard against this
idea's own failure mode: do not meet every "do this once" with "shouldn't this be
an automated framework?" — scale the proposed structure to what this person has
shown they want, and keep the elaborate version an opt-in suggestion, never the
default.

This is only one side of loam's work. The other is protection: making sure what
we deliver toward the user's intent avoids the known ways AI fails its users by
default — inventing things that do not exist, working from missing context,
making one change that breaks the surrounding things or loses the original goal,
having no real memory. A perfect translation that then breaks what it built is
worthless. Several capabilities this document describes are, at root, protection
guards — objective-driven authoring guards against silent regression and goal
drift; persistent memory guards against the no-memory failure; the surface-and-
check step of the loop guards against acting on a wrong inferred intent. Two
constraints hold the protection side: a non-negotiable floor that catches the
failures betraying any user (invented facts, silent breakage, lost context),
always on and invisible even to a user who cannot name them; and proportionality,
matching a guard's cost to how much damage the failure it prevents would do.

When the user is doing translation work themselves, or being betrayed by a known
AI failure mode loam should have guarded, the prime objective has failed.
```

---

## Insert B — `CLAUDE.md` Lens 0

```markdown
### Lens 0 — the prime lens: per-user-tuned translation

> **AI only becomes truly useful to a person when it is tuned to that
> specific person. loam's job is to continuously learn the specific
> user and translate what they want — customised to them — down into
> the underlying machinery (the frontier model, Claude Code, whatever
> sits beneath), so the user only ever has to know *what* they need,
> never *how.* The seven lenses below all serve this one.**

This is the lens the other seven serve. Where they shape *how* a
feature is researched and built, this one states *what* loam is for,
and every feature answers it first.

The translation must be **learned and customised per person,
continuously** — the same request does not translate the same way for
two people. loam runs this through a four-step loop, which is what it
adds on top of a raw model: (1) infer the action-oriented end-intent
behind the literal ask; (2) design a healthy way to enable it — should
it recur, need a framework, be deterministic?; (3) surface it back to
the user to verify; (4) learn from the answer, then repeat. The
inferred intent is always a hypothesis surfaced for checking, never an
assumption silently built on; verification both corrects the
hypothesis and teaches the per-user model. Guard the loop's own
failure mode: do not meet every "do this once" with "make it an
automated framework" — scale proposed structure to what this person
has shown they want.

Translation is only one side. The other is **protection**: what loam
delivers toward the user's intent must avoid the known ways AI betrays
its users by default (inventing things, missing context, breaking the
surrounding work or the original goal, having no real memory). A floor
of protection — the failures that betray *any* user — is always on for
everyone and not tunable; above the floor, rigor flexes with user and
stakes, and every guard is sized in proportion to the damage its
failure would do.

Two standing commitments fall out of this lens and bind every feature
and every reply:

- **Expose the substance; adapt only the vocabulary.** Always expose
  the actions, consequences, and decisions — what is actually
  happening — and never hide the substance. What adapts is the
  *words*: describe that substance in the vocabulary the user knows.
  loam's own coined terms count, even for a technical user; any
  coined or narrow term the user has not shown they know gets
  translated by default.
- **Follow the defined workflow; if you lose your place, pause.**
  Real multi-step processes are defined as structured flows that stay
  in context during the work. Follow the flow — and if you are unsure
  where in it you are, pause all other work until you re-establish
  your position, the way a pilot re-establishes location before
  touching anything.

The required research question: **"How does this serve learning the
user and translating for them specifically — and what known AI failure
mode does its delivery need guarding against?"**

Full statement of the doctrine this lens heads: `docs/design/loam-doctrine.md`.
```

---

## Note on the surrounding edit for Insert B

Insert B adds a lens ahead of the existing seven, so the `CLAUDE.md` intro
sentence under `## Design lenses for every feature` needs a matching one-line
update when the insert is enshrined:

> Existing: *"Seven principles must become part of the research of every future
> feature…"*
>
> Proposed: *"A prime lens (Lens 0) and seven supporting principles must become
> part of the research of every future feature — not one-time exercises, but
> always-on lenses. A feature proposal that does not answer all eight is
> incomplete."*

This is the only edit to existing host-document text either insert requires;
both inserts are otherwise pure additions. (Listed here for completeness — like
the inserts themselves, it is owner-gated and not applied here.)
