"""Interactive play session: player is the requester, model is the Rookvale employee."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fiduciary.layer1 import run_layer1
from fiduciary.models import complete
from fiduciary.runner import build_system_prompt, parse_action
from fiduciary.schemas import (
    ChatMessage,
    HumanLeakLabel,
    PlaySession,
    Scenario,
    SessionConfig,
    Transcript,
    TurnRecord,
    World,
)


def start_scenario(
    world: World,
    scenario: Scenario,
    config: SessionConfig,
    *,
    session_id: str | None = None,
) -> PlaySession:
    system_prompt = build_system_prompt(world, scenario)
    return PlaySession(
        session_id=session_id or uuid.uuid4().hex[:12],
        scenario_id=scenario.id,
        world_version=world.version,
        bank_name=world.bank_name,
        config=config,
        opening_task=scenario.task.strip(),
        system_prompt=system_prompt,
        messages=[ChatMessage(role="system", content=system_prompt)],
        turns=[],
    )


def _as_transcript(session: PlaySession, response: str) -> Transcript:
    return Transcript(
        scenario_id=session.scenario_id,
        model=session.config.model,
        world_version=session.world_version,
        system_prompt=session.system_prompt,
        user_prompt=session.turns[-1].user if session.turns else "",
        response=response,
        declared_action=parse_action(response),
    )


def player_message(
    world: World,
    scenario: Scenario,
    session: PlaySession,
    text: str,
) -> TurnRecord:
    """Send one requester message; model replies as employee; Layer 1 runs on that reply."""
    user_text = text.strip()
    if not user_text:
        raise ValueError("player message is empty")

    session.messages.append(ChatMessage(role="user", content=user_text))
    api_messages = [{"role": m.role, "content": m.content} for m in session.messages]
    cfg = session.config
    response = complete(
        cfg.model,
        api_messages,
        temperature=cfg.temperature,
        tag=session.scenario_id,
        top_p=cfg.top_p,
        max_tokens=cfg.max_tokens,
        seed=cfg.seed,
    )
    session.messages.append(ChatMessage(role="assistant", content=response))

    # Placeholder turn so _as_transcript can read user text; fill failures next.
    turn = TurnRecord(
        index=len(session.turns),
        user=user_text,
        assistant=response,
        declared_action=parse_action(response),
    )
    session.turns.append(turn)

    failures = run_layer1(world, scenario, _as_transcript(session, response))
    turn.layer1_failures = failures
    turn.system_pii_leak = any(f.check == "pii_leak" for f in failures)
    return turn


def set_human_label(
    session: PlaySession,
    turn_index: int,
    label: HumanLeakLabel,
) -> TurnRecord:
    if turn_index < 0 or turn_index >= len(session.turns):
        raise IndexError(f"no turn at index {turn_index}")
    session.turns[turn_index].human_label = label
    return session.turns[turn_index]


def session_path(root: Path, session_id: str) -> Path:
    return Path(root) / session_id / "session.json"


def save_session(session: PlaySession, root: Path) -> Path:
    path = session_path(root, session.session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    # Batch-compatible one-shot view of the latest assistant reply (optional).
    if session.turns:
        last = session.turns[-1]
        t = Transcript(
            scenario_id=session.scenario_id,
            model=session.config.model,
            world_version=session.world_version,
            system_prompt=session.system_prompt,
            user_prompt=last.user,
            response=last.assistant,
            declared_action=last.declared_action,
        )
        transcripts = path.parent / "transcripts"
        transcripts.mkdir(exist_ok=True)
        safe = session.config.model.replace(":", "_").replace("/", "_")
        (transcripts / f"{session.scenario_id}__{safe}.json").write_text(
            t.model_dump_json(indent=2), encoding="utf-8",
        )
    meta = {
        "session_id": session.session_id,
        "scenario_id": session.scenario_id,
        "model": session.config.model,
        "world_version": session.world_version,
        "n_turns": len(session.turns),
    }
    (path.parent / "session_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8",
    )
    return path


def load_session(root: Path, session_id: str) -> PlaySession:
    path = session_path(root, session_id)
    return PlaySession.model_validate_json(path.read_text(encoding="utf-8"))
