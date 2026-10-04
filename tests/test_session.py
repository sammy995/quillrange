"""Phase 1: interactive session API (multi-turn + Layer 1 + human labels)."""
from pathlib import Path

import pytest

from fiduciary.scenarios import load_scenarios
from fiduciary.session import (
    load_session,
    player_message,
    save_session,
    set_human_label,
    start_scenario,
)
from fiduciary.schemas import SessionConfig
from fiduciary.world import load_world

WORLD = load_world("data/world")
SCENARIOS = {s.id: s for s in load_scenarios("data/scenarios/wave1")}


def test_start_seeds_opening_task_and_system():
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(WORLD, s, SessionConfig(model="mock:echo"), session_id="t1")
    assert session.bank_name == "Rookvale"
    assert session.opening_task == s.task.strip()
    assert session.messages[0].role == "system"
    assert "Rookvale" in session.system_prompt
    assert session.turns == []


def test_player_turn_leak_fixture_marks_pii():
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(
        WORLD, s, SessionConfig(model="mock:fixture:leak"), session_id="leak1",
    )
    turn = player_message(WORLD, s, session, session.opening_task)
    assert turn.system_pii_leak is True
    assert any(f.check == "pii_leak" for f in turn.layer1_failures)
    assert len(session.turns) == 1
    assert session.messages[-1].role == "assistant"


def test_player_turn_good_fixture_no_pii_leak():
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(
        WORLD, s, SessionConfig(model="mock:fixture:good"), session_id="good1",
    )
    turn = player_message(WORLD, s, session, session.opening_task)
    assert turn.system_pii_leak is False
    assert not any(f.check == "pii_leak" for f in turn.layer1_failures)


def test_human_label_roundtrip(tmp_path: Path):
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(
        WORLD, s, SessionConfig(model="mock:fixture:leak"), session_id="label1",
    )
    player_message(WORLD, s, session, session.opening_task)
    set_human_label(session, 0, "leak")
    assert session.turns[0].human_label == "leak"

    path = save_session(session, tmp_path)
    assert path.exists()
    loaded = load_session(tmp_path, "label1")
    assert loaded.turns[0].human_label == "leak"
    assert loaded.turns[0].system_pii_leak is True
    assert (tmp_path / "label1" / "session_meta.json").exists()


def test_human_label_agree_and_clean():
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(
        WORLD, s, SessionConfig(model="mock:fixture:good"), session_id="lab2",
    )
    player_message(WORLD, s, session, "Please export the list.")
    set_human_label(session, 0, "agree")
    assert session.turns[0].human_label == "agree"
    set_human_label(session, 0, "clean")
    assert session.turns[0].human_label == "clean"


def test_empty_message_rejected():
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(
        WORLD, s, SessionConfig(model="mock:echo"), session_id="empty",
    )
    with pytest.raises(ValueError, match="empty"):
        player_message(WORLD, s, session, "   ")


def test_bad_turn_index():
    s = SCENARIOS["W1-PRIV-001"]
    session = start_scenario(
        WORLD, s, SessionConfig(model="mock:echo"), session_id="badix",
    )
    with pytest.raises(IndexError):
        set_human_label(session, 0, "agree")
