"""Phase 2: sampling knobs + privacy deck."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from fiduciary.cli import main
from fiduciary.decks import load_deck, resolve_deck_scenarios, validate_deck
from fiduciary.models import LAST_CALL, complete
from fiduciary.scenarios import load_scenarios
from fiduciary.schemas import SessionConfig
from fiduciary.session import player_message, start_scenario
from fiduciary.world import load_world

WORLD = load_world("data/world")
SCENARIOS = load_scenarios("data/scenarios/wave1")


def test_session_config_rejects_bad_temperature():
    with pytest.raises(ValidationError):
        SessionConfig(model="mock:echo", temperature=3.0)


def test_session_config_rejects_bad_top_p():
    with pytest.raises(ValidationError):
        SessionConfig(model="mock:echo", top_p=1.5)


def test_privacy_deck_loads_fourteen():
    deck = load_deck("privacy-wave1")
    assert deck.id == "privacy-wave1"
    assert len(deck.scenario_ids) == 14
    assert validate_deck(deck, SCENARIOS) == []
    resolved = resolve_deck_scenarios(deck, SCENARIOS)
    assert [s.id for s in resolved] == deck.scenario_ids
    assert all(s.id.startswith("W1-PRIV-") for s in resolved)


def test_complete_records_sampling_knobs():
    complete(
        "mock:echo",
        [{"role": "user", "content": "hi"}],
        temperature=0.4,
        top_p=0.9,
        max_tokens=128,
        seed=7,
    )
    assert LAST_CALL["temperature"] == 0.4
    assert LAST_CALL["top_p"] == 0.9
    assert LAST_CALL["max_tokens"] == 128
    assert LAST_CALL["seed"] == 7


def test_player_message_passes_knobs():
    s = next(x for x in SCENARIOS if x.id == "W1-PRIV-001")
    cfg = SessionConfig(
        model="mock:echo", temperature=0.2, top_p=0.8, max_tokens=64, seed=42,
    )
    session = start_scenario(WORLD, s, cfg, session_id="knobs1")
    player_message(WORLD, s, session, "hello")
    assert LAST_CALL["temperature"] == 0.2
    assert LAST_CALL["top_p"] == 0.8
    assert LAST_CALL["max_tokens"] == 64
    assert LAST_CALL["seed"] == 42


def test_cli_run_deck_smoke(tmp_path: Path):
    out = tmp_path / "run"
    # mock:echo works for every scenario id; fixtures only cover a couple of PRIV cases
    assert main([
        "run",
        "--model", "mock:echo",
        "--out", str(out),
        "--deck", "privacy-wave1",
        "--temperature", "0.1",
        "--seed", "9",
    ]) == 0
    assert (out / "run_config.json").exists()
    cfg = (out / "run_config.json").read_text(encoding="utf-8")
    assert "privacy-wave1" in cfg
    assert '"temperature": 0.1' in cfg
    assert (out / "transcripts" / "W1-PRIV-001__mock_echo.json").exists()
    assert (out / "transcripts" / "W1-PRIV-014__mock_echo.json").exists()


def test_cli_play_turn_smoke(tmp_path: Path):
    out = tmp_path / "sessions"
    assert main([
        "play-turn",
        "--model", "mock:fixture:leak",
        "--scenario", "W1-PRIV-001",
        "--out", str(out),
        "--session-id", "p1",
        "--temperature", "0.0",
        "--seed", "1",
    ]) == 0
    session = (out / "p1" / "session.json").read_text(encoding="utf-8")
    assert "system_pii_leak" in session
    assert "true" in session.lower() or '"system_pii_leak": true' in session
