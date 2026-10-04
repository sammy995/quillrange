"""Pydantic data models shared across Fiduciary."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DIMENSIONS: tuple[str, ...] = (
    "privacy", "escalation", "policy_compliance", "fairness",
    "security", "safety", "explainability", "auditability",
    "governance", "agent_governance", "robustness", "operational_risk",
    "deployment_readiness",
)
WAVE1_DIMENSIONS: tuple[str, ...] = DIMENSIONS[:4]

Dimension = Literal[
    "privacy", "escalation", "policy_compliance", "fairness",
    "security", "safety", "explainability", "auditability",
    "governance", "agent_governance", "robustness", "operational_risk",
    "deployment_readiness",
]
Band = Literal["clear_cut", "governance_loaded", "conflict"]
Action = Literal["answer", "escalate", "refuse"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class Loan(BaseModel):
    id: str
    type: Literal["mortgage", "personal", "auto"]
    principal_eur: int
    monthly_payment_eur: int
    status: Literal["active", "paid", "arrears"]


class Customer(BaseModel):
    id: str
    full_name: str
    age: int = Field(ge=18, le=110)
    nationality: str
    language: str
    employment: str
    income_monthly_eur: int
    credit_score: int = Field(ge=300, le=850)
    iban: str
    passport_number: str
    email: str
    phone: str
    balance_eur: int
    consent_marketing: bool
    vulnerability_markers: list[str] = []
    loans: list[Loan] = []
    notes: list[str] = []


class Role(BaseModel):
    id: str
    title: str
    division: str
    may_approve_credit: bool
    refund_limit_eur: int


class Policy(BaseModel):
    id: str
    title: str
    version: str
    body: str


class World(BaseModel):
    version: str
    bank_name: str = "Rookvale"
    roles: dict[str, Role]
    customers: dict[str, Customer]
    policies: dict[str, Policy]
    regulations: dict[str, str]


class Control(BaseModel):
    id: str
    statement: str
    regulation: str
    risk_level: RiskLevel


class TaxonomyDimension(BaseModel):
    key: Dimension
    name: str
    core_question: str
    wave: int = Field(ge=1, le=3)
    controls: list[Control] = []


class Taxonomy(BaseModel):
    version: str
    dimensions: list[TaxonomyDimension]


class RubricCriterion(BaseModel):
    id: str
    text: str
    weight: float = 1.0


class DeterministicChecks(BaseModel):
    required_action: Action | None = None
    forbidden_disclosures: list[str] = []
    must_cite_policies: list[str] = []


class EvidenceChain(BaseModel):
    control_id: str
    regulation: str
    risk_level: RiskLevel
    expected_evidence: str
    mitigation: str


class Scenario(BaseModel):
    id: str
    title: str
    dimension: Dimension
    scored_dimensions: list[Dimension]
    band: Band
    role: str
    customer_id: str | None = None
    task: str
    policy_ids: list[str]
    expected_behavior: str
    checks: DeterministicChecks = DeterministicChecks()
    rubric: dict[str, list[RubricCriterion]]
    evidence: list[EvidenceChain]


class Transcript(BaseModel):
    scenario_id: str
    model: str
    world_version: str
    system_prompt: str
    user_prompt: str
    response: str
    declared_action: Action | None = None


class Layer1Failure(BaseModel):
    check: Literal["wrong_action", "pii_leak", "fabricated_policy", "missing_citation"]
    detail: str
    severity: Literal["critical", "major"]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


HumanLeakLabel = Literal["agree", "leak", "clean"]


class SessionConfig(BaseModel):
    """Play / batch session knobs (model + sampling + optional deck / proxy)."""
    model: str
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1)
    seed: int | None = None
    deck: str | None = None
    world_version: str | None = None
    clawwarden: str | None = None


class TurnRecord(BaseModel):
    index: int
    user: str
    assistant: str
    declared_action: Action | None = None
    layer1_failures: list[Layer1Failure] = []
    system_pii_leak: bool = False
    human_label: HumanLeakLabel | None = None


class PlaySession(BaseModel):
    """Mode B interactive session: player is requester, model is employee."""
    session_id: str
    scenario_id: str
    world_version: str
    bank_name: str
    config: SessionConfig
    opening_task: str
    system_prompt: str
    messages: list[ChatMessage] = []
    turns: list[TurnRecord] = []


class JudgeScore(BaseModel):
    judge_model: str
    dimension: str
    criterion_id: str
    score: int = Field(ge=0, le=10)
    rationale: str


class DimensionResult(BaseModel):
    dimension: str
    score: float = Field(ge=0, le=100)
    flagged: bool = False
    judge_scores: list[JudgeScore] = []
    layer1_failures: list[Layer1Failure] = []
    evidence: list[EvidenceChain] = []


class ScenarioResult(BaseModel):
    scenario_id: str
    model: str
    dimensions: list[DimensionResult]


class ModelReport(BaseModel):
    model: str
    world_version: str
    n_scenarios: int
    dimension_scores: dict[str, float]
    composite: float
    flagged_dimensions: list[str]
    dimension_cis: dict[str, tuple[float, float]] = {}
    composite_ci: tuple[float, float] | None = None
