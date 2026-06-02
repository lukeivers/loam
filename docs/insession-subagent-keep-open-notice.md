# Keep loam open in the background to finish while you're away

When loam does longer work for you — researching your role, building something,
running a batch of tasks — it now does that work **inside your open session**,
using Claude's in-session helpers instead of launching separate detached
processes.

**What this means for you, in plain language:**

- **Leave loam open and it keeps working.** You can start a long task, switch to
  something else, and come back later. As long as the loam session stays open in
  the background, the work keeps running and finishing on its own.

- **Close the session and the work pauses.** If you quit loam (or close the
  window/session that's running the work), the long-running work pauses. It
  isn't lost — but it won't keep going until you reopen the session. Nothing runs
  "headless" in the background after you've closed everything.

- **So: keep loam open in the background to finish while you're away.** The
  simplest rule — if you want a long task to complete while you step away, just
  leave the loam session running. Don't close it until the work is done.

**Why it works this way.** Running the work inside your open session means it
runs on the Claude plan you already have, with no separate metered "agent"
credit to manage on the side. The trade is that the work lives with your
session: open session, work runs; closed session, work waits for you to come
back.

If you need work to run completely unattended overnight with nothing open,
that's a different setup — ask and loam will walk you through the options.
