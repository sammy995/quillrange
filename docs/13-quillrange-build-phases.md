# Quillrange build phases

**Goal:** interactive privacy eval on Rookvale scenarios — model as config, persona chat, Layer 1 + human leak labels, then ClawWarden compare.

**Rule:** enhance what is already in `src/fiduciary/` and `data/` before adding new packages or a UI. Every phase ends with `pytest` green and `fiduciary validate` OK (CLI name may still be `fiduciary` until Phase 5).

**Names (locked):** product **Quillrange**, bank **Rookvale**. Gap: [12-interactive-privacy-eval.md](12-interactive-privacy-eval.md).

---

## File map (target)

| Path | Role | When |
|---|---|---|
| `data/world/org.yaml` | `bank_name` / display → Rookvale | Phase 0 |
| `src/fiduciary/runner.py` | System prompt uses world bank name; later multi-turn | 0 → 1 |
| `src/fiduciary/schemas.py` | `SessionConfig`, `Turn`, `HumanLeakLabel`, message list | Phase 1 |
| `src/fiduciary/layer1.py` | Run on one assistant string (already); call per turn | Phase 1 |
| `src/fiduciary/models.py` | Pass temperature / top_p / max_tokens / seed | Phase 2 |
| `src/fiduciary/session.py` | **New** — play one turn, attach Layer 1 + optional human label | Phase 1 |
| `data/decks/privacy-wave1.yaml` | **New** — list of 14 `W1-PRIV-*` ids | Phase 2 |
| `apps/play/` or `play/` | **New** — local UI | Phase 3 |
| `src/fiduciary/proxy.py` | **New** — optional ClawWarden HTTP wrap | Phase 4 |
| `pyproject.toml` / CLI entry | Rename package script to `quillrange` | Phase 5 |

Keep batch CLI (`run` / `judge` / `score` / `report`) working the whole time.

---

## Phase 0 — Branding in existing data (no new features)

**Done when:** UI-facing and prompt-facing bank name is Rookvale; docs say Quillrange; tests still pass.

1. In `data/world/org.yaml`, set `bank_name: Rookvale` (or `Rookvale Building Society`). Keep IBANs as fictional `TB…` if rewrite is huge; note in SECURITY that TB = fiction, not TrustBank product.
2. Grep prompts/docs that say `TrustBank` in player-facing copy (`runner.py` SYSTEM_TEMPLATE, README blurb, SECURITY). Change display strings to Rookvale. Internal paths may stay.
3. Point README status line at Quillrange as the product name for the interactive path; keep “fiduciary duties” as the *concept* in prose.
4. Update this gap pair (12 + 13) as the source of truth.
5. Run `pytest` and `fiduciary validate`.

**Do not** rename the Python package or GitHub repo in this phase.

---

## Phase 1 — Enhance engine for multi-turn + labels

**Done when:** a Python API can run turn N, return Layer 1 failures, and store a human label without a UI.

1. Extend `Transcript` (or add `Conversation`) in `schemas.py`:
   - `messages: list[{role, content}]`
   - `turns: list[{ assistant, layer1_failures, human_label: agree|leak|clean|null }]`
2. Add `session.py`:
   - `start_scenario(world, scenario, config) → state` (system prompt from existing `build_system_prompt`)
   - `player_message(state, text) → assistant reply + layer1` (Mode B: player = requester)
   - First user message may seed from `scenario.task` as the opening line the player can edit or send as-is
3. Call `run_layer1` on **each** assistant reply (reuse forbidden_disclosures / ACTION checks as today where they still apply).
4. Persist JSON under `results/<session_id>/` compatible enough that batch `score` can ignore new fields.
5. Tests: mock model, known leak fixture → `pii_leak`; human_label round-trip; no network.

**Enhance, don’t rewrite:** keep `run_scenario` for Mode A / CI by wrapping the same prompt builder.

---

## Phase 2 — Enhance config + privacy deck

**Done when:** a session file names model, knobs, and the privacy deck; knobs reach litellm.

1. `SessionConfig`: `model`, `temperature`, `top_p`, `max_tokens`, `seed`, `deck`, `world_version`, `clawwarden: null`.
2. Thread knobs through `models.complete` (today hardcodes temperature 0).
3. Add `data/decks/privacy-wave1.yaml` listing the 14 privacy scenario ids.
4. CLI: `fiduciary play-turn` or extend `run` with `--deck privacy-wave1` for smoke (optional; UI can wait for Phase 3).
5. Tests: config validation; deck load; knob passed into mock/complete.

---

## Phase 3 — New local play UI

**Done when:** one local page runs the privacy deck with system mark + human buttons.

1. Small app under `play/` (static + thin FastAPI, or Vite talking to FastAPI) — pick one stack and stay.
2. Sidebar: model string + knobs (Phase 2 config).
3. Main: scene (role, Rookvale), chat, after each reply show **System: leak / clean** and buttons **Agree / Mark leak / Mark clean**.
4. All I/O through `session.py`; no duplicate Layer 1 in the frontend.
5. Manual smoke on `W1-PRIV-001` with `mock:fixture:…` or a tiny local Ollama model.

**Not in this phase:** accounts, cloud hosting, leaderboard.

---

## Phase 4 — New ClawWarden comparison

**Done when:** same session can run raw vs proxy and show leak counts.

1. `proxy.py`: if `clawwarden` URL set, send prompts through gateway; else direct.
2. UI toggle or dual-run report: Layer 1 leak rate + human-agreed leaks.
3. Document: ClawWarden must run locally; this repo only stores the URL.
4. Tests: mock HTTP; offline default remains direct.

---

## Phase 5 — Packaging rename (when publishing)

**Done when:** public name matches code entrypoints.

1. Reserve GitHub `quillrange` (or org), PyPI `quillrange`, domain if needed.
2. Rename package/CLI `fiduciary` → `quillrange` (or thin wrapper that calls both during transition).
3. LICENSE / SECURITY / CREDITS / CONTRIBUTING already real — refresh product name only ([public-surfaces](../../.cursor/rules/public-surfaces.mdc) habit).
4. Update workspace `AGENTS.md` / `REPO-MAP.md` folder note: `fiduciary` folder may lag the remote name.

---

## Suggested cadence

| Week focus | Phase |
|---|---|
| Names + Rookvale strings + validate | 0 |
| Session API + tests | 1 |
| Knobs + privacy deck | 2 |
| Local UI | 3 |
| ClawWarden toggle | 4 |
| Public rename when you open the repo under Quillrange | 5 |

---

## Exit criteria for “privacy game v0”

- [ ] Rookvale on screen; Quillrange in docs
- [ ] Privacy deck playable locally
- [ ] Every assistant turn has Layer 1 + optional human label on disk
- [ ] Model + knobs in session config
- [ ] Batch CLI still green in CI
- [ ] ClawWarden optional (nice-to-have for v0; required for “ultra-sensitive” demo)

## GitHub layout (2026-10-04)

| Remote | Visibility | Role |
|---|---|---|
| [sammy995/quillrange](https://github.com/sammy995/quillrange) | **public** | Only public face. Stub until Phase 0–2 land. |
| [sammy995/fiduciary](https://github.com/sammy995/fiduciary) | **private** | Old name; keep history private. Do not point people here. |

Local folder stays `E:\AI learning\fiduciary` until a rename. When Phase 0–2 (branding + data/engine) are done, push that tree to **quillrange** `main`. UI (Phase 3) starts only after that push.

```bash
# one-time (already planned):
git remote add quillrange https://github.com/sammy995/quillrange.git
# when ready:
git push quillrange HEAD:main
```

## Phase 0 status (started 2026-10-04)

- [x] `org.yaml` → Rookvale, world `0.1.1`, manifest rewritten
- [x] `World.bank_name` + runner prompt uses it
- [x] `W1-PRIV-007` task text; SECURITY + README product/world names
- [x] Local `pytest` + `validate` green (`PYTHONPATH=src`)
- [x] Public `quillrange` created; `fiduciary` set private
- [ ] Historical docs (`docs/04-…`, ADRs) still say TrustBank — doc sweep before first quillrange push
- [ ] First full push to `quillrange` after Phase 1–2

## Phase 1 status (done 2026-10-04)

- [x] `SessionConfig`, `ChatMessage`, `TurnRecord`, `PlaySession` in `schemas.py`
- [x] `session.py`: `start_scenario`, `player_message`, `set_human_label`, `save_session` / `load_session`
- [x] Layer 1 on every assistant turn; `system_pii_leak` + human `agree|leak|clean`
- [x] Persist under `results/<session_id>/session.json` (+ batch-shaped transcript of last turn)
- [x] `tests/test_session.py` — leak/good fixtures, labels, empty message (full suite green)

## Phase 2 status (done 2026-10-04)

- [x] `SessionConfig` validates temperature / top_p / max_tokens
- [x] `models.complete` takes `top_p`, `max_tokens`, `seed`; session + `run_scenario` pass them
- [x] `data/decks/privacy-wave1.yaml` (14 `W1-PRIV-*`) + `decks.py`
- [x] CLI: `run --deck privacy-wave1`, sampling flags, `play-turn`
- [x] `validate` checks decks; `tests/test_phase2.py` green

Next: **first push to `quillrange`**, then Phase 3 UI.
