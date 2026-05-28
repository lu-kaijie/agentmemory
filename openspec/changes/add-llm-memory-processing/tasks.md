## 1. Models And Scopes

- [ ] 1.1 Add KV scopes for summaries, memory candidates, and LLM processing jobs
- [ ] 1.2 Add Pydantic models for SummaryRecord, MemoryCandidateRecord, and LLMProcessingJobRecord
- [ ] 1.3 Extend ObserveResponse to include processing job, summary, and candidate memory data
- [ ] 1.4 Extend AuditRecord action types for LLM processing success and failure

## 2. LLM Processing Service

- [ ] 2.1 Add LLM memory processing helper/service
- [ ] 2.2 Implement summary generation from observation
- [ ] 2.3 Implement candidate memory extraction from observation
- [ ] 2.4 Implement processing job running/done/failed status updates
- [ ] 2.5 Implement audit writes for LLM processing success and failure
- [ ] 2.6 Preserve observation when LLM processing fails

## 3. Memory Core Integration

- [ ] 3.1 Inject provider bundle or LLM provider into MemoryCoreService
- [ ] 3.2 Trigger LLM processing after successful observe
- [ ] 3.3 Save summaries and candidate memories to StateKV
- [ ] 3.4 Add list summaries, list memory candidates, and list LLM processing jobs
- [ ] 3.5 Add service tests for success, candidate not auto-remembered, and failure paths

## 4. REST API

- [ ] 4.1 Include processing result in `POST /agentmemory/observe` response
- [ ] 4.2 Add `GET /agentmemory/summaries`
- [ ] 4.3 Add `GET /agentmemory/memory-candidates`
- [ ] 4.4 Add `GET /agentmemory/llm-processing-jobs`
- [ ] 4.5 Add REST tests for observe processing and list endpoints

## 5. CLI

- [ ] 5.1 Include processing result in `agentmemory observe --json`
- [ ] 5.2 Add `agentmemory summaries`
- [ ] 5.3 Add `agentmemory memory-candidates`
- [ ] 5.4 Add `agentmemory llm-processing-jobs`
- [ ] 5.5 Add CLI tests for derived data list commands

## 6. Verification

- [ ] 6.1 Document Skill trigger guidance for low-frequency observe calls
- [ ] 6.2 Add tests or documentation checks covering low-frequency trigger guidance
- [ ] 6.3 Run pytest for all tests
- [ ] 6.4 Verify OpenSpec status is complete for `add-llm-memory-processing`
