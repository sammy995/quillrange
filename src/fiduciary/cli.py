"""Fiduciary command-line interface: validate -> run -> judge -> score -> report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fiduciary.aggregate import build_model_report, score_scenario
from fiduciary.crosswalk import load_crosswalk, validate_crosswalk
from fiduciary.decks import DEFAULT_DECK_DIR, load_deck, resolve_deck_scenarios, validate_deck
from fiduciary.judge import judge_transcript
from fiduciary.layer1 import run_layer1
from fiduciary.report import render_leaderboard, render_model_report
from fiduciary.runner import _safe_model_name, run_scenario, save_transcript, transcript_path
from fiduciary.scenarios import load_scenarios, validate_scenarios
from fiduciary.schemas import JudgeScore, ModelReport, ScenarioResult, SessionConfig, Transcript
from fiduciary.session import player_message, save_session, start_scenario
from fiduciary.reliability import (agreement_metrics, automated_criterion_means,
                                  export_rating_sheets, read_rating_csvs,
                                  render_reliability_report)
from fiduciary.taxonomy import load_taxonomy
from fiduciary.world import load_world, verify_manifest, write_manifest

WORLD_ROOT = "data/world"
SCENARIO_DIR = "data/scenarios/wave1"


def _select(scenario_dir: str, ids: str | None):
    scenarios = load_scenarios(scenario_dir)
    if ids:
        wanted = set(ids.split(","))
        scenarios = [s for s in scenarios if s.id in wanted]
        missing = wanted - {s.id for s in scenarios}
        if missing:
            raise SystemExit(f"unknown scenario ids: {sorted(missing)}")
    return scenarios


def _session_config_from_args(args) -> SessionConfig:
    return SessionConfig(
        model=args.model,
        temperature=getattr(args, "temperature", 0.0),
        top_p=getattr(args, "top_p", None),
        max_tokens=getattr(args, "max_tokens", None),
        seed=getattr(args, "seed", None),
        deck=getattr(args, "deck", None),
    )


def _add_sampling_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", dest="top_p", type=float, default=None)
    p.add_argument("--max-tokens", dest="max_tokens", type=int, default=None)
    p.add_argument("--seed", type=int, default=None)


def cmd_validate(_args) -> int:
    world = load_world(WORLD_ROOT)
    taxonomy = load_taxonomy()
    scenarios = load_scenarios(SCENARIO_DIR)
    problems = validate_scenarios(scenarios, world, taxonomy)
    problems += verify_manifest(WORLD_ROOT)
    problems += validate_crosswalk(load_crosswalk(), taxonomy)
    for path in sorted(DEFAULT_DECK_DIR.glob("*.yaml")):
        try:
            problems += validate_deck(load_deck(path.stem), scenarios)
        except Exception as e:  # noqa: BLE001 — surface deck load errors in validate
            problems.append(f"deck {path.name}: {e}")
    for p in problems:
        print(f"PROBLEM: {p}")
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_manifest(_args) -> int:
    print(f"wrote {write_manifest(WORLD_ROOT)}")
    return 0


def cmd_run(args) -> int:
    problems = verify_manifest(WORLD_ROOT)
    if problems:
        for p in problems:
            print(f"MANIFEST: {p}")
        return 1
    world = load_world(WORLD_ROOT)
    run_dir = Path(args.out)
    cfg = _session_config_from_args(args)
    if args.deck:
        deck = load_deck(args.deck)
        scenarios = resolve_deck_scenarios(deck, load_scenarios(args.scenarios))
        cfg.deck = deck.id
    else:
        scenarios = _select(args.scenarios, args.ids)
    for scenario in scenarios:
        transcript = run_scenario(world, scenario, args.model, config=cfg)
        print(f"ran {scenario.id} -> {save_transcript(transcript, run_dir)}")
    (run_dir / "run_config.json").write_text(
        json.dumps({**cfg.model_dump(), "world_version": world.version,
                    "scenario_dir": args.scenarios, "ids": args.ids,
                    "n_scenarios": len(scenarios)}, indent=2),
        encoding="utf-8",
    )
    return 0


def cmd_play_turn(args) -> int:
    """One Mode-B turn: requester message → employee reply → Layer 1 → save session."""
    world = load_world(WORLD_ROOT)
    scenarios = {s.id: s for s in load_scenarios(SCENARIO_DIR)}
    if args.scenario not in scenarios:
        raise SystemExit(f"unknown scenario {args.scenario!r}")
    scenario = scenarios[args.scenario]
    cfg = _session_config_from_args(args)
    cfg.world_version = world.version
    out = Path(args.out)
    session_id = args.session_id or out.name
    from fiduciary.session import load_session

    session_file = out / session_id / "session.json"
    if session_file.exists():
        session = load_session(out, session_id)
        session.config = cfg
    else:
        session = start_scenario(world, scenario, cfg, session_id=session_id)
    text = args.message if args.message is not None else session.opening_task
    turn = player_message(world, scenario, session, text)
    path = save_session(session, out)
    leak = "LEAK" if turn.system_pii_leak else "clean"
    print(f"turn {turn.index} system={leak} action={turn.declared_action} -> {path}")
    return 0


def cmd_judge(args) -> int:
    run_dir = Path(args.run)
    judges = args.judges.split(",")
    dimension_names = {d.key: d.name for d in load_taxonomy().dimensions}
    out_dir = run_dir / "judgements"
    out_dir.mkdir(parents=True, exist_ok=True)
    for scenario in _select(SCENARIO_DIR, None):
        t_path = transcript_path(run_dir, scenario.id, args.model)
        if not t_path.exists():
            continue
        transcript = Transcript.model_validate_json(t_path.read_text(encoding="utf-8"))
        scores = judge_transcript(scenario, transcript, judges, dimension_names)
        out = out_dir / f"{scenario.id}__{_safe_model_name(args.model)}.json"
        out.write_text(json.dumps([s.model_dump() for s in scores], indent=2), encoding="utf-8")
        print(f"judged {scenario.id} ({len(scores)} criterion scores)")
    return 0


def cmd_score(args) -> int:
    run_dir = Path(args.run)
    world = load_world(WORLD_ROOT)
    results: list[ScenarioResult] = []
    for scenario in _select(SCENARIO_DIR, None):
        t_path = transcript_path(run_dir, scenario.id, args.model)
        j_path = run_dir / "judgements" / f"{scenario.id}__{_safe_model_name(args.model)}.json"
        if not (t_path.exists() and j_path.exists()):
            continue
        transcript = Transcript.model_validate_json(t_path.read_text(encoding="utf-8"))
        judge_scores = [JudgeScore.model_validate(x)
                        for x in json.loads(j_path.read_text(encoding="utf-8"))]
        failures = run_layer1(world, scenario, transcript)
        results.append(score_scenario(scenario, failures, judge_scores, args.model))
    if not results:
        print("nothing to score")
        return 1
    report = build_model_report(results, args.model, world.version)
    scores_dir = run_dir / "scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    out = scores_dir / f"{_safe_model_name(args.model)}.json"
    out.write_text(json.dumps(
        {"results": [r.model_dump() for r in results],
         "report": report.model_dump()}, indent=2), encoding="utf-8")
    print(f"scored {len(results)} scenarios -> {out}")
    return 0


def cmd_report(args) -> int:
    run_dir = Path(args.run)
    report_dir = run_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        crosswalk = load_crosswalk()
    except FileNotFoundError:
        crosswalk = None
    if crosswalk and crosswalk.get("review_status") != "reviewed":
        crosswalk = None  # mappings are not citable until a human reviews them
    reports: list[ModelReport] = []
    for path in sorted((run_dir / "scores").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        report = ModelReport.model_validate(data["report"])
        results = [ScenarioResult.model_validate(r) for r in data["results"]]
        (report_dir / f"{path.stem}.md").write_text(
            render_model_report(report, results, crosswalk=crosswalk), encoding="utf-8")
        reports.append(report)
    (report_dir / "leaderboard.md").write_text(render_leaderboard(reports), encoding="utf-8")
    print(f"wrote {len(reports)} report(s) + leaderboard -> {report_dir}")
    return 0


def cmd_reliability_export(args) -> int:
    sheet = export_rating_sheets(Path(args.run), args.model, Path(args.out), args.n)
    print(f"wrote {sheet} — copy per rater, fill human_score with integers 0-10")
    return 0


def cmd_reliability_compute(args) -> int:
    run_dir = Path(args.run)
    human = read_rating_csvs(Path(args.ratings))
    auto = automated_criterion_means(run_dir, args.model)
    overall = agreement_metrics(human, auto)

    by_dim: dict[str, dict] = {}
    dims: dict[str, set] = {}
    for key in human:
        scenario_id = key.split("|")[0]
        prefix = scenario_id.rsplit("-", 1)[0]  # e.g. W1-PRIV
        dims.setdefault(prefix, set()).add(key)
    for prefix, keys in dims.items():
        h = {k: human[k] for k in keys if k in auto}
        a = {k: auto[k] for k in keys if k in auto}
        if h:
            by_dim[prefix] = agreement_metrics(h, a)

    report = render_reliability_report(overall, by_dim)
    (run_dir / "reliability_report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fiduciary")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    sub.add_parser("manifest").set_defaults(fn=cmd_manifest)

    p = sub.add_parser("run")
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--scenarios", default=SCENARIO_DIR)
    p.add_argument("--ids", default=None)
    p.add_argument("--deck", default=None, help="named deck under data/decks/ (e.g. privacy-wave1)")
    _add_sampling_args(p)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("play-turn", help="one interactive requester turn (Mode B)")
    p.add_argument("--model", required=True)
    p.add_argument("--scenario", required=True)
    p.add_argument("--out", required=True, help="results root directory")
    p.add_argument("--session-id", dest="session_id", default=None)
    p.add_argument("--message", default=None, help="requester text; default = scenario opening task")
    p.add_argument("--deck", default=None)
    _add_sampling_args(p)
    p.set_defaults(fn=cmd_play_turn)

    p = sub.add_parser("judge")
    p.add_argument("--run", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--judges", required=True)
    p.set_defaults(fn=cmd_judge)

    p = sub.add_parser("score")
    p.add_argument("--run", required=True)
    p.add_argument("--model", required=True)
    p.set_defaults(fn=cmd_score)

    p = sub.add_parser("report")
    p.add_argument("--run", required=True)
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("reliability-export")
    p.add_argument("--run", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--n", type=int, default=3)
    p.set_defaults(fn=cmd_reliability_export)

    p = sub.add_parser("reliability-compute")
    p.add_argument("--run", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--ratings", required=True)
    p.set_defaults(fn=cmd_reliability_compute)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
