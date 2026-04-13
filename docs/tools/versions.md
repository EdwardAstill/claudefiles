# af versions

Dependency versions from `package.json`, `Cargo.toml`, `pyproject.toml`, lockfiles, etc.

**Source:** `tools/python/src/af/versions.py`

## Usage

```bash
af versions            # print to stdout
af versions --write    # also save to .agentfiles/versions.md
```

## Options

| Flag | Description |
|------|-------------|
| `--write` | Save output to `.agentfiles/versions.md` |

## Supported Lockfiles

`uv.lock`, `Cargo.lock`, `poetry.lock`, `package-lock.json`, `bun.lock`, `yarn.lock`, `Gemfile.lock`, `go.mod`, `pyproject.toml`, `requirements.txt`
