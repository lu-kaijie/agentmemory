## Manual Verification

Configure real OpenAI-compatible providers before running the service or tests:

```bash
export AGENTMEMORY_LLM_BASE_URL="https://api.openai.com/v1"
export AGENTMEMORY_LLM_API_KEY="<your-llm-api-key>"
export AGENTMEMORY_LLM_MODEL="<your-chat-model>"
export AGENTMEMORY_EMBEDDING_BASE_URL="https://api.openai.com/v1"
export AGENTMEMORY_EMBEDDING_API_KEY="<your-embedding-api-key>"
export AGENTMEMORY_EMBEDDING_MODEL="<your-embedding-model>"
```

Run real provider tests:

```bash
uv run pytest tests/test_openai_provider.py
```

Run all tests:

```bash
uv run pytest
```

Verify doctor output:

```bash
uv run agentmemory doctor
```

Start the service:

```bash
uv run agentmemory serve
```

Check health in another terminal:

```bash
curl -s http://127.0.0.1:3111/agentmemory/health
```

Expected results:

- `doctor` exits successfully and shows LLM/embedding provider status.
- Health response includes `providers.llm` and `providers.embedding`.
- API keys are never printed in CLI or REST output.
- If any required provider setting is missing, `doctor`, `serve`, app creation, and tests fail loudly.
