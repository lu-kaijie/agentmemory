class KV:
    health = "system:health"
    metadata = "system:metadata"
    projects = "mem:projects"
    project_profiles = "mem:projectProfiles"
    pinned_memory = "mem:pinnedMemory"
    project_current_sessions = "mem:projectCurrentSessions"
    sessions = "mem:sessions"
    memories = "mem:memories"
    summaries = "mem:summaries"
    knowledge = "mem:knowledge"
    insights = "mem:insights"
    wiki_pages = "mem:wikiPages"
    wiki_update_jobs = "mem:wikiUpdateJobs"
    memory_candidates = "mem:memoryCandidates"
    llm_processing_jobs = "mem:llmProcessingJobs"
    search_documents = "mem:searchDocuments"
    index_jobs = "mem:indexJobs"
    audit = "mem:audit"

    @staticmethod
    def observations(session_id: str) -> str:
        return f"mem:observations:{session_id}"
