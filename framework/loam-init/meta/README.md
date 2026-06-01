# loam

The single-command install surface for the **loam** CLI.

```
pipx install loam      # recommended — isolated managed venv, `loam` on PATH
pip  install loam      # equivalent
```

`loam` here is a *dependencies-only meta-distribution*: it ships no code
of its own and resolves the whole loam command-line dependency graph
(`loam init`, `loam amend`, `loam migrate`, `loam release`, `loam audit`,
`loam flow`, `loam pr-safety`, and the dev/SDLC + skills surfaces). After
install:

```
loam --help            # lists the real subcommands
loam init ./my-space    # scaffolds a fresh loam workspace
```

The equivalent explicit install names the components directly:

```
pip install loam-cli loam-init loam-amend loam-pr-safety loam-mode \
            loam-plugin-dev-sdlc loam-odd-extractor loam-per-project-pm \
            loam-plugin-loam-skills loam-workspace-sync loam-self-upgrade
```

See the repository for the contributor / source-install path
(`install-from-source.txt`).
