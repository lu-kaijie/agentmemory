from agentmemory.state import StateKV


def test_state_kv_set_get_list_delete(tmp_path):
    kv = StateKV(tmp_path / "state.sqlite3")

    kv.set("scope", "a", {"value": 1})
    kv.set("scope", "b", {"value": 2})

    assert kv.get("scope", "a") == {"value": 1}
    assert kv.list("scope") == [{"value": 1}, {"value": 2}]
    assert kv.delete("scope", "a") is True
    assert kv.get("scope", "a") is None
    assert kv.delete("scope", "missing") is False


def test_state_kv_timestamps_update(tmp_path):
    kv = StateKV(tmp_path / "state.sqlite3")

    kv.set("scope", "key", {"value": 1})
    first = kv.metadata("scope", "key")
    kv.set("scope", "key", {"value": 2})
    second = kv.metadata("scope", "key")

    assert first is not None
    assert second is not None
    assert first["created_at"] == second["created_at"]
    assert first["updated_at"] <= second["updated_at"]
    assert kv.get("scope", "key") == {"value": 2}

def test_state_kv_initializes_database(tmp_path):
    db_path = tmp_path / "new" / "state.sqlite3"

    StateKV(db_path)

    assert db_path.exists()

