# Quillrange — gap and locked names

**Product name:** Quillrange  
**Synthetic bank (on screen):** Rookvale Building Society (fiction)  
**Repo folder / GitHub today:** `sammy995/fiduciary` (rename remote when Phase 0 lands)  
**Related products:** ClawWarden = PII proxy under test; Prahari = RBI MRM IDs later, not the sim  

This file is the gap. The build order is [`13-quillrange-build-phases.md`](13-quillrange-build-phases.md).

Not a lawyer clearance. Name search notes are in [Appendix A](#appendix-a--name-search-2026-10-04).

---

## Goal

Player picks a **model + knobs** as session config. Quillrange drops them into **Rookvale** banking scenes. They talk to a **persona** (the model as employee). Every assistant reply is stored. **Layer 1** marks PII leak / clean. The human can **agree or override**. Later: same turns through **ClawWarden** and compare leak rates — that is the ultra-sensitive deploy story.

Play mode: player is the *requester*; model is the employee. Batch CLI stays for CI.

---

## What exists today

| Piece | Path | Ready for game? |
|---|---|---|
| World (policies, customers, roles) | `data/world/` | Yes — rename display to Rookvale |
| Privacy policy | `POL-001-data-privacy.md` | Yes |
| 56 Wave-1 scenarios | `data/scenarios/wave1/` | Yes — privacy deck = 14 `W1-PRIV-*` |
| Forbidden PII checks | scenario YAML `forbidden_disclosures` | Yes |
| Layer 1 `pii_leak` | `src/fiduciary/layer1.py` | Yes — extend to every turn |
| One-shot runner | `src/fiduciary/runner.py` | Partial — one `task`, one reply |
| Model via litellm | `src/fiduciary/models.py` | Partial — temp fixed at 0 |
| Run config | `run_config.json` | Partial — no knobs / deck / proxy |
| Transcript JSON | results dir | Partial — not multi-turn |
| Judge / score / report | CLI | Keep for batch; not live UI |
| Tests (79) | `tests/` | Keep green every phase |

**Missing:** multi-turn messages, human leak labels, game session schema, local UI, sampling knobs, ClawWarden hook, Quillrange branding on public surfaces.

---

## What we will not do yet

- Public leaderboard (reliability gate still open)
- Real customer data
- Merging ClawWarden into this repo
- Calling the product Fiduciary AI / Fiduciary-Grade AI / TrustBank
- Building Prahari into the play loop

---

## Phase map (summary)

| Phase | Kind | Outcome |
|---|---|---|
| **0** | Enhance docs + data labels | Quillrange / Rookvale locked; no broken tests |
| **1** | Enhance engine | Session + multi-turn + Layer 1 per turn + human label fields |
| **2** | Enhance config + data | Privacy deck + model knobs in session config |
| **3** | **New** UI | Local play loop (chat, system mark, human override) |
| **4** | **New** ClawWarden path | Proxy on/off, compare leak rates |
| **5** | Enhance packaging | `quillrange` CLI/package/GitHub when ready to publish |

Detail and file-level tasks: [`13-quillrange-build-phases.md`](13-quillrange-build-phases.md).

---

## Appendix A — name search (2026-10-04)

**Fiduciary** as a product brand: descriptive legal English; FiduciaryBench (WealthSchema) and Fiducia-bench already in the space; FIDUCIARY-GRADE AI pending for Thomson Reuters — do not use that phrase. Abandoned “FIDUCIARY AI” filings are not a green light for that branding.

**TrustBank:** Trust Fintech TrustBankCBS — do not use on UI.

**Locked picks:** Quillrange (product), Rookvale (bank). Avoid Clerk*, Tally*, Policytwin, Kiln, Hexvale, Pinfold, Cinderwell.

Grab GitHub + PyPI + domain for `quillrange` before a public rename.

---

## Links

- Build phases: [13-quillrange-build-phases.md](13-quillrange-build-phases.md)
- Engine vs world: [design-decisions/0007-engine-vs-benchmark.md](design-decisions/0007-engine-vs-benchmark.md)
- Roadmap (hosted UI was a v1 cut; this reopens a *local* UI only): [06-scope-and-roadmap.md](06-scope-and-roadmap.md)
- ClawWarden: https://github.com/clawwarden/clawwarden
