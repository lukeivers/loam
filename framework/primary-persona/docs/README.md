# Primary-persona layer — documentation

This directory is the bundled documentation required by v1.1 R4. The
following files are the authoritative reference for the component:

1. **`prose-explanation.md`** — what the layer is, why it exists, how
   its three halves fit together. Read this first.
2. **`architecture.md`** — the architecture diagram (three halves +
   their shared contract artifact).
3. **`data-flow.md`** — a representative lifecycle walkthrough:
   session start → loader → monitor tick → authoring trigger →
   authoring pipeline → introduction → activation → retirement.
4. **`relationship-map.md`** — how this layer connects to scope-of-
   work, memory-system, observability, and the safety layer.
5. **`api-reference.md`** — one-page API reference for the loader,
   monitor, authoring triggers, introduction protocol, and retirement.
6. **`retirement-reference.md`** — user-facing reference for retiring,
   un-retiring, and understanding retirement reasons.

A non-technical reader can answer "what does this layer do and how
does it fit with the others" from these files alone (the v1.1 R4
acceptance criterion).
