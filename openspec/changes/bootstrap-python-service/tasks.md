## 1. Project Skeleton

- [x] 1.1 Create `pyproject.toml` with Python 3.11+, runtime dependencies, dev dependencies, and `agentmemory` CLI entry point
- [x] 1.2 Create `src/agentmemory/` package structure and `tests/` directory
- [x] 1.3 Add basic package metadata and version constant

## 2. Configuration

- [x] 2.1 Implement `agentmemory.config.Settings` with Pydantic Settings
- [x] 2.2 Add defaults for host, port, database path, secret, and log level
- [x] 2.3 Implement safe configuration summary with secret redaction
- [x] 2.4 Add tests for default configuration and secret redaction

## 3. StateKV

- [x] 3.1 Implement SQLite engine/session initialization with SQLAlchemy
- [x] 3.2 Implement KV table creation with `(scope, key)` primary key
- [x] 3.3 Implement `StateKV.get`, `set`, `delete`, and `list`
- [x] 3.4 Add created and updated timestamp handling
- [x] 3.5 Add tests for set/get/list/delete and timestamp updates

## 4. FastAPI Service

- [x] 4.1 Implement FastAPI app factory in `agentmemory.api.app`
- [x] 4.2 Implement `GET /agentmemory/livez`
- [x] 4.3 Implement `GET /agentmemory/health` with database probe and redacted config summary
- [x] 4.4 Add FastAPI TestClient tests for health endpoints

## 5. CLI

- [x] 5.1 Implement Typer app in `agentmemory.cli`
- [x] 5.2 Implement `agentmemory serve` using Uvicorn and configured host/port
- [x] 5.3 Implement `agentmemory doctor` with configuration and database checks
- [x] 5.4 Add Typer CliRunner tests for `doctor`

## 6. Verification

- [x] 6.1 Run formatting/lint checks where configured
- [x] 6.2 Run pytest for all bootstrap tests
- [x] 6.3 Verify OpenSpec status remains complete
