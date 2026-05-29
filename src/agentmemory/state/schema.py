class KV:
    health = "system:health"
    metadata = "system:metadata"
    sessions = "mem:sessions"
    memories = "mem:memories"
    summaries = "mem:summaries"
    memory_candidates = "mem:memoryCandidates"
    llm_processing_jobs = "mem:llmProcessingJobs"
    search_documents = "mem:searchDocuments"
    index_jobs = "mem:indexJobs"
    audit = "mem:audit"

    @staticmethod
    def observations(session_id: str) -> str:
        return f"mem:observations:{session_id}"
