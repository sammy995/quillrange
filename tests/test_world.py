import json
from pathlib import Path

from fiduciary.world import load_world, make_manifest, parse_front_matter, verify_manifest, write_manifest

ORG = """\
version: "0.1.0"
bank_name: Rookvale
divisions: [Support]
roles:
  support_agent:
    id: support_agent
    title: Customer Support Agent
    division: Support
    may_approve_credit: false
    refund_limit_eur: 200
"""

POLICY = """\
---
id: POL-001
title: Test Policy
version: "1.0"
---
## 1. Scope
Body text here.
"""

CUSTOMER = {
    "id": "CUST-001", "full_name": "Test Person", "age": 30,
    "nationality": "Fictland", "language": "English", "employment": "engineer",
    "income_monthly_eur": 3000, "credit_score": 700,
    "iban": "TB00 0000 0000 0000", "passport_number": "P0000000",
    "email": "t@example.com", "phone": "+000", "balance_eur": 100,
    "consent_marketing": True,
}


def build_world(root: Path) -> Path:
    (root / "policies").mkdir(parents=True)
    (root / "regulations").mkdir()
    (root / "org.yaml").write_text(ORG, encoding="utf-8")
    (root / "customers.json").write_text(json.dumps([CUSTOMER]), encoding="utf-8")
    (root / "policies" / "POL-001-test.md").write_text(POLICY, encoding="utf-8")
    (root / "regulations" / "REG-TEST.md").write_text(
        "---\nid: REG-TEST\ntitle: Test Reg\n---\nReg body.", encoding="utf-8")
    return root


def test_parse_front_matter():
    meta, body = parse_front_matter(POLICY)
    assert meta["id"] == "POL-001"
    assert body.startswith("## 1. Scope")


def test_load_world(tmp_path):
    world = load_world(build_world(tmp_path / "world"))
    assert world.version == "0.1.0"
    assert world.roles["support_agent"].refund_limit_eur == 200
    assert world.customers["CUST-001"].credit_score == 700
    assert world.policies["POL-001"].body.startswith("## 1. Scope")
    assert "REG-TEST" in world.regulations


def test_manifest_roundtrip(tmp_path):
    root = build_world(tmp_path / "world")
    write_manifest(root)
    assert verify_manifest(root) == []
    (root / "org.yaml").write_text(ORG + "# tampered\n", encoding="utf-8")
    problems = verify_manifest(root)
    assert any("org.yaml" in p for p in problems)


def test_manifest_deterministic(tmp_path):
    root = build_world(tmp_path / "world")
    assert make_manifest(root) == make_manifest(root)
