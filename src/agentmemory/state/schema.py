class KV:
    health = "system:health"
    metadata = "system:metadata"
    sessions = "mem:sessions"
    memories = "mem:memories"
    audit = "mem:audit"

    @staticmethod
    def observations(session_id: str) -> str:
        return f"mem:observations:{session_id}"
