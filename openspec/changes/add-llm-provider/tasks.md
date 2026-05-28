## 1. Configuration

- [ ] 1.1 Add required LLM settings for base URL, API key, and model
- [ ] 1.2 Add required embedding settings for base URL, API key, and model
- [ ] 1.3 Extend safe configuration summaries so API keys are never returned
- [ ] 1.4 Add configuration tests for missing AI settings and complete OpenAI-compatible settings

## 2. Provider Models And Interfaces

- [ ] 2.1 Create provider module structure
- [ ] 2.2 Define shared provider status and error models
- [ ] 2.3 Define LLM provider interface for summarize, extract memories, explain search, compress context, and update wiki
- [ ] 2.4 Define embedding provider interface for ordered batch embeddings

## 3. OpenAI-Compatible Providers

- [ ] 3.1 Add OpenAI SDK dependency
- [ ] 3.2 Implement OpenAI-compatible LLM provider construction and readiness checks
- [ ] 3.3 Implement OpenAI-compatible embedding provider construction and readiness checks
- [ ] 3.4 Map provider call failures to structured provider errors
- [ ] 3.5 Add real provider tests for summarize and embedding calls using configured credentials

## 4. Provider Factory And Required Startup

- [ ] 4.1 Implement provider factory from settings
- [ ] 4.2 Block app creation and `serve` startup when LLM settings are missing
- [ ] 4.3 Block app creation and `serve` startup when embedding settings are missing
- [ ] 4.4 Track provider status and recent error in a reusable health summary
- [ ] 4.5 Add tests confirming missing AI settings fail loudly

## 5. Health And Doctor

- [ ] 5.1 Extend `/agentmemory/health` with LLM and embedding provider status
- [ ] 5.2 Extend `agentmemory doctor` with LLM and embedding provider status
- [ ] 5.3 Add REST and CLI tests confirming provider status is shown and secrets are redacted
- [ ] 5.4 Add manual verification commands for users to validate real LLM and embedding configuration

## 6. Verification

- [ ] 6.1 Run pytest for all tests
- [ ] 6.2 Verify OpenSpec status is complete for `add-llm-provider`
