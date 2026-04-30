# Core Development Convention — shutdown-path broad-catch exception

> *A broad catch inside a teardown method (`close()`, `stop()`, `cancel()`, `shutdown()`, `__aexit__`, or semantically-equivalent cleanup) is ODD-legit without per-component acceptance-criterion backing — but the caught exception must be surfaced to observability. When an observability span is in scope at the catch site, use `span.add_event(name, {"exception": type(exc).__name__, ...})`. Otherwise, log at least `logger.debug("teardown_exception", exc_info=True)`. Bare `pass` is insufficient. The teardown must not raise; the exception information must not disappear.*

Rationale. Observability is a first-class primitive in pos-v2 (sealed `observability-aggregator` component; every other sealed component emits span events and OTel signals by design). A teardown that silently discards exception information undermines that primitive — the aggregator has nothing to aggregate, the forensic trail dies at the try-except boundary, and shutdown-path debugging devolves into guesswork. The original CDC 2 (bare `pass` tolerated) was consistent with "shutdown shouldn't cascade" but weaker than pos-v2's observability posture warrants. The tightened form preserves the no-cascade guarantee (broad catch still swallows) while restoring the forensic trail (emission preserves what happened, even if the caller doesn't need to act on it).

How to apply. When writing or reviewing teardown broad-catches, pair the catch with one of two observability emissions: a `span.add_event(...)` call when an already-open span is in scope at the catch site, or a `logger.debug("teardown_exception", exc_info=True)` call when no span is in scope. The emission goes *before* the swallow (pass/return). For `CancelledError` specifically, continue to treat it as expected-flow: catch `asyncio.CancelledError` separately with bare `pass`, catch broader `Exception` with the observability emission. Example pattern:

```python
try:
    await task
except asyncio.CancelledError:
    pass  # expected on cancel
except Exception as exc:
    logger.debug("background_task_stop_exception", exc_info=True)
    # or span.add_event("teardown_failed", {"exception": type(exc).__name__})
```

Applied immediately to: amendment #23 (queued) retrofits the ~44 bucket-(b) teardown broad-catches currently using bare `pass` to the tightened pattern. Going forward, new teardown code must follow the tightened CDC from the start.
