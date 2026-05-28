## 1. Configuration

- [x] 1.1 Add required LLM settings for base URL, API key, and model
- [x] 1.2 Add required embedding settings for base URL, API key, and model
- [x] 1.3 Extend safe configuration summaries so API keys are never returned
- [x] 1.4 Add configuration tests for missing AI settings and complete OpenAI-compatible settings

## 2. Provider Models And Interfaces

- [x] 2.1 Create provider module structure
- [x] 2.2 Define shared provider status and error models
- [x] 2.3 Define LLM provider interface for summarize, extract memories, explain search, compress context, and update wiki
- [x] 2.4 Define embedding provider interface for ordered batch embeddings

## 3. OpenAI-Compatible Providers

- [x] 3.1 Add OpenAI SDK dependency
- [x] 3.2 Implement OpenAI-compatible LLM provider construction and readiness checks
- [x] 3.3 Implement OpenAI-compatible embedding provider construction and readiness checks
- [x] 3.4 Map provider call failures to structured provider errors
- [x] 3.5 Add real provider tests for summarize and embedding calls using configured credentials

## 4. Provider Factory And Required Startup

- [x] 4.1 Implement provider factory from settings
- [x] 4.2 Block app creation and `serve` startup when LLM settings are missing
- [x] 4.3 Block app creation and `serve` startup when embedding settings are missing
- [x] 4.4 Track provider status and recent error in a reusable health summary
- [x] 4.5 Add tests confirming missing AI settings fail loudly

## 5. Health And Doctor

- [x] 5.1 Extend `/agentmemory/health` with LLM and embedding provider status
- [x] 5.2 Extend `agentmemory doctor` with LLM and embedding provider status
- [x] 5.3 Add REST and CLI tests confirming provider status is shown and secrets are redacted
- [x] 5.4 Add manual verification commands for users to validate real LLM and embedding configuration

## 6. Verification

- [x] 6.1 Run pytest for all tests
- [x] 6.2 Verify OpenSpec status is complete for `add-llm-provider`
