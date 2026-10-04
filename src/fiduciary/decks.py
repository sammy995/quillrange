"""Load named scenario decks (privacy pack, etc.)."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from fiduciary.schemas import Scenario


DEFAULT_DECK_DIR = Path("data/decks")


class Deck(BaseModel):
    id: str
    title: str
    description: str = ""
    scenario_ids: list[str] = Field(min_length=1)


def deck_path(deck_id: str, deck_dir: str | Path = DEFAULT_DECK_DIR) -> Path:
    return Path(deck_dir) / f"{deck_id}.yaml"


def load_deck(deck_id: str, deck_dir: str | Path = DEFAULT_DECK_DIR) -> Deck:
    path = deck_path(deck_id, deck_dir)
    if not path.exists():
        raise FileNotFoundError(f"deck not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    deck = Deck.model_validate(raw)
    if deck.id != deck_id:
        raise ValueError(f"deck file id {deck.id!r} does not match {deck_id!r}")
    return deck


def resolve_deck_scenarios(
    deck: Deck,
    scenarios: list[Scenario],
) -> list[Scenario]:
    by_id = {s.id: s for s in scenarios}
    missing = [i for i in deck.scenario_ids if i not in by_id]
    if missing:
        raise ValueError(f"deck {deck.id} unknown scenario ids: {missing}")
    return [by_id[i] for i in deck.scenario_ids]


def validate_deck(deck: Deck, scenarios: list[Scenario]) -> list[str]:
    known = {s.id for s in scenarios}
    return [f"deck {deck.id}: unknown scenario {i}" for i in deck.scenario_ids if i not in known]
