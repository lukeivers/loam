# launchd hosting for the Graphiti prototype service

The plist in this directory makes the FastAPI service from
`src/service.py` a managed local service: auto-start on login, restart
on crash, log to `data/graphiti-service*.log`.

## Install

```bash
cp launchd/com.pos-v2.memory-graphiti.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pos-v2.memory-graphiti.plist
```

Verify:

```bash
launchctl list | grep com.pos-v2.memory-graphiti
curl -s http://127.0.0.1:9876/health
```

## Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.pos-v2.memory-graphiti.plist
rm ~/Library/LaunchAgents/com.pos-v2.memory-graphiti.plist
```

## Why launchd, why a service

D1's acceptance criterion calls for "service auto-starts and survives a
restart." A library-only Python embedding of Graphiti satisfies the
restart-survival half (the Kuzu DB is the persistent state), but does
not provide the auto-start half. Hosting `src/service.py` under launchd
gives both: the Kuzu DB survives because it's a file on disk, and the
service comes back after reboot because launchd brings it back.

For the **full build**, this becomes the proposal's adaptation #4
(Graphiti MCP hosting). That layer adds health probes, a richer API
surface (the official `mcp_server` tool set: add_episode, search_nodes,
search_facts, etc.), and proper concurrency controls. The plist shape
stays the same.
