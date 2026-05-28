## 1. Configuration

- [ ] 1.1 Add LLM provider settings for provider, base URL, API key, and model
- [ ] 1.2 Add embedding provider settings for provider, base URL, API key, and model
- [ ] 1.3 Extend safe configuration summaries so API keys are never returned
- [ ] 1.4 Add configuration tests for default fake providers and OpenAI-compatible settings

## 2. Provider Models And Interfaces

- [ ] 2.1 Create provider module structure
- [ ] 2.2 Define shared provider status and error models
- [ ] 2.3 Define LLM provider interface for summarize, extract memories, explain search, compress context, and update wiki
- [ ] 2.4 Define embedding provider interface for ordered batch embeddings

## 3. Fake Providers

- [ ] 3.1 Implement deterministic fake LLM provider
- [ ] 3.2 Implement deterministic fake embedding provider
- [ ] 3.3 Add unit tests for fake LLM outputs
- [ ] 3.4 Add unit tests for fake embedding order and vector stability

## 4. OpenAI-Compatible Providers

- [ ] 4.1 Add OpenAI SDK dependency
- [ ] 4.2 Implement OpenAI-compatible LLM provider construction and readiness checks
- [ ] 4.3 Implement OpenAI-compatible embedding provider construction and readiness checks
- [ ] 4.4 Map provider call failures to structured provider errors
- [ ] 4.5 Add tests for missing API key and client construction without making network calls

## 5. Provider Factory And Health

- [ ] 5.1 Implement provider factory from settings
- [ ] 5.2 Track provider status and recent error in a reusable health summary
- [ ] 5.3 Extend `/agentmemory/health` with LLM and embedding provider status
- [ ] 5.4 Extend `agentmemory doctor` with LLM and embedding provider status
- [ ] 5.5 Add REST and CLI tests confirming provider status is shown and secrets are redacted

## 6. Verification

- [ ] 6.1 Run pytest for all tests
- [ ] 6.2 Verify OpenSpec status is complete for `add-llm-provider`
