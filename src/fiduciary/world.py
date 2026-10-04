"""Load and version the Rookvale synthetic world (data under data/world/)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from fiduciary.schemas import Customer, Policy, Role, World


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ValueError("document has no front-matter")
    _, meta_block, body = text.split("---", 2)
    return yaml.safe_load(meta_block), body.lstrip("\n")


def load_world(root: str | Path = "data/world") -> World:
    root = Path(root)
    org = yaml.safe_load((root / "org.yaml").read_text(encoding="utf-8"))
    roles = {k: Role.model_validate(v) for k, v in org["roles"].items()}

    customers_raw = json.loads((root / "customers.json").read_text(encoding="utf-8"))
    customers = {c["id"]: Customer.model_validate(c) for c in customers_raw}

    policies: dict[str, Policy] = {}
    for path in sorted((root / "policies").glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        policies[meta["id"]] = Policy(
            id=meta["id"], title=meta["title"], version=str(meta["version"]), body=body)

    regulations: dict[str, str] = {}
    for path in sorted((root / "regulations").glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        regulations[meta["id"]] = f"{meta['title']}\n\n{body}"

    return World(
        version=org["version"],
        bank_name=org.get("bank_name", "Rookvale"),
        roles=roles,
        customers=customers,
        policies=policies,
        regulations=regulations,
    )


def _data_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*")
                  if p.is_file() and p.name != "manifest.yaml")


def _hash_file(path: Path) -> str:
    """Hash file bytes with line endings normalized to LF.

    The world is all UTF-8 text; normalizing CRLF -> LF makes the manifest
    reproducible across operating systems and git line-ending settings, so a
    pinned world verifies identically on Windows, macOS, and Linux CI.
    """
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def make_manifest(root: str | Path) -> dict:
    root = Path(root)
    org = yaml.safe_load((root / "org.yaml").read_text(encoding="utf-8"))
    files = {
        p.relative_to(root).as_posix(): _hash_file(p)
        for p in _data_files(root)
    }
    return {"world_version": org["version"], "files": files}


def write_manifest(root: str | Path) -> Path:
    root = Path(root)
    out = root / "manifest.yaml"
    out.write_text(yaml.safe_dump(make_manifest(root), sort_keys=True), encoding="utf-8")
    return out


def verify_manifest(root: str | Path) -> list[str]:
    root = Path(root)
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        return ["manifest.yaml missing — run: fiduciary manifest"]
    recorded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    current = make_manifest(root)
    problems: list[str] = []
    if recorded["world_version"] != current["world_version"]:
        problems.append("world_version mismatch")
    all_keys = set(recorded["files"]) | set(current["files"])
    for key in sorted(all_keys):
        if recorded["files"].get(key) != current["files"].get(key):
            problems.append(f"hash mismatch or missing file: {key}")
    return problems
