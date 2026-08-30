from pathlib import Path

from ix_assistant_core.runtime import LocalActionStore


def test_local_store_persists_notes_and_lists(tmp_path: Path) -> None:
    store = LocalActionStore(tmp_path / "actions.json")
    note = store.create_note(text="UX test note", original_text="take a note UX test note")
    item = store.add_list_item(item="coffee", list_name="shopping")

    reopened = LocalActionStore(tmp_path / "actions.json")
    records = reopened.list_records()

    assert note.record_id != item.record_id
    assert len(records) == 2
    assert reopened.list_records(kind="note")[0].payload["note_text"] == "UX test note"
    assert reopened.list_records(kind="list_item")[0].payload["item"] == "coffee"


def test_timer_seconds_are_computed(tmp_path: Path) -> None:
    store = LocalActionStore(tmp_path / "actions.json")
    timer = store.create_timer(duration_value=2, duration_unit="minutes", original_text="timer")
    assert timer.payload["duration_seconds"] == 120
