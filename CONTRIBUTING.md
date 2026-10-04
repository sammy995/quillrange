# Contributing to Quillrange

Thanks for helping build a benchmark serious institutions can trust. Quillrange
(Python package still `fiduciary` this cycle) is a **social system disguised as
a technical system** — its value comes from transparency, reproducibility, and
domain rigor. Contributions are judged against that bar.

Clone: `https://github.com/sammy995/quillrange.git`

## The most valuable contribution: scenarios

If you have **banking, compliance, risk, audit, or financial-regulation**
experience, authoring scenarios is where you add the most. A scenario drops a
model into a role inside Rookvale and defines what good behavior looks like.

### Anatomy of a scenario

Every scenario lives in [`data/scenarios/wave1/<id>.yaml`](data/scenarios/wave1/)
and must satisfy `fiduciary validate`. Use an existing exemplar
(`W1-PRIV-001`, `W1-ESC-002`, `W1-FAIR-002`) as your template. Hard rules:

1. **Filename equals `id`** (`W1-<DIM>-NNN.yaml`), `DIM ∈ PRIV, ESC, POL, FAIR`.
2. **The primary `dimension` is first** in `scored_dimensions`.
3. `rubric` keys **exactly** equal `scored_dimensions`; every criterion id
   starts with `<scenario-id>-r`.
4. Every `evidence[].control_id` exists in [`data/taxonomy.yaml`](data/taxonomy.yaml).
5. `checks.must_cite_policies` ⊆ `policy_ids`; `forbidden_disclosures` patterns
   reference real `Customer` fields (`*.field` or `CUST-ID.field`).
6. **World-consistency rule:** every fact a scenario relies on must exist in a
   policy section, a regulation file, a customer record, or the task text. The
   "correct" behavior must be *derivable from the world*, never from opinion.
7. Set `required_action` (`answer` / `escalate` / `refuse`) so Layer 1 can score
   it deterministically.

Run `fiduciary validate` — a green "OK" is required before you open a PR.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest        # must be green (offline, no API keys)
fiduciary validate     # world + taxonomy + scenarios + manifest
```

If you change anything under `data/world/`, regenerate the manifest and commit
it (a pinned world is what makes results reproducible):

```bash
python -c "from fiduciary.world import write_manifest; write_manifest('data/world')"
```

## Code contributions

- **Test-first.** Every behavior change ships with a test; CI runs the full
  suite offline.
- Keep new files focused and match the surrounding style. No new heavy runtime
  dependencies without discussion.
- Model calls go through `fiduciary.models.complete`; keep all tests runnable
  with the `mock:` protocol (no network in CI).

## Judge & methodology changes

The evaluation is the product. Changes to Layer-1 checks, judge prompts, or the
scoring math must explain their effect on reproducibility and, where relevant,
on human-agreement (see [`reliability/PILOT-RUNBOOK.md`](reliability/PILOT-RUNBOOK.md)).
Prefer moving checks *into* Layer 1 (deterministic) over widening LLM judgment.

## Pull requests

1. Branch from `main`.
2. `python -m pytest` and `fiduciary validate` both green.
3. Describe *what deployment concern* your change measures or improves.
4. One logical change per PR.

By contributing you agree your work is licensed under [Apache 2.0](LICENSE).

## Scenario review checklist

Every scenario PR is checked against this list before merge. Reviewers
paste the list into the PR and tick it.

- [ ] Expected behavior is derivable from a policy, regulation, customer
      record, or the task itself. The PR names which one.
- [ ] Every policy ID cited exists in data/world/policies/.
- [ ] The control IDs in the evidence chain exist in data/taxonomy.yaml.
- [ ] Framework references in the evidence chain appear in
      standards/crosswalk.yaml for those controls, or the PR flags the gap.
- [ ] Rubric criteria are observable behaviors, not vibes ("cites POL-001
      accurately", not "handles the situation well").
- [ ] Difficulty band assigned (clear_cut, governance_loaded, conflict)
      with one sentence of justification.
- [ ] `fiduciary validate` passes.
- [ ] The scenario-set version is bumped per VERSIONS.md.
- [ ] The canary comment is the first line of the new file.
- [ ] Author's affiliation is disclosed if this is their first scenario.
