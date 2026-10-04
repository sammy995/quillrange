# Design decisions (ADRs)

Every major choice in Fiduciary is recorded here as an Architecture Decision
Record, with the **rejected alternatives** and why. Six months from now the
reasoning is forgotten; a contributor should be able to reconstruct it — and
challenge it — from these files.

Format per ADR: **Context → Decision → Rejected alternatives → Consequences.**

| ADR | Decision |
|---|---|
| [0001](0001-methodology-before-code.md) | Methodology and taxonomy before code |
| [0002](0002-simulated-organization.md) | Evaluate inside a simulated organization, not a prompt list |
| [0003](0003-banking-first.md) | Banking as the first domain |
| [0004](0004-yaml-and-files.md) | Plain versioned files (YAML/JSON/Markdown), no database |
| [0005](0005-layered-judge.md) | A layered judge (deterministic + multi-model), not one LLM |
| [0006](0006-weighted-rubric-scoring.md) | Weighted rubric scoring with Layer-1 caps |
| [0007](0007-engine-vs-benchmark.md) | Fiduciary is an evaluation *engine*; banking is instance #1 |
| [0008](0008-anti-reward-hacking.md) | Design against benchmark reward-hacking from day one |
| [0009](0009-independent-versioning.md) | Version the benchmark, world, scenario set, judge, and taxonomy independently |

Interactive privacy game — gap + locked names (**Quillrange** / **Rookvale**): [`12-interactive-privacy-eval.md`](../12-interactive-privacy-eval.md).  
Build order (enhance existing, then new): [`13-quillrange-build-phases.md`](../13-quillrange-build-phases.md).
