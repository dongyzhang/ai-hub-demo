"""Shared helpers for the Deloitte AI Hub (standard library only).

Loads/validates asset manifests and runs the sanitization (secret + client-term) scan.
Used by scripts/build_index.py, scripts/generate_report.py, and hub-cli/hub.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# --- Paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry" / "assets"
WEB_DATA = ROOT / "web" / "data"
CLIENT_TERMS_FILE = ROOT / "hub-cli" / "client_terms.txt"

# --- Controlled vocabularies (must match manifest.schema.json) -------------
VALID_TYPES = {
    "skill", "agent", "slash-command", "hook", "claude-md",
    "prompt", "app", "training", "utility",
}
VALID_CATEGORIES = {
    "Finance", "Audit", "Tax", "Data", "Engineering",
    "Design", "Productivity", "Risk", "Other",
}
REQUIRED_FIELDS = [
    "title", "slug", "description", "type", "category",
    "author", "team", "created", "confidentiality_attestation",
]

# Text file extensions we scan for secrets / client terms.
SCANNABLE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".yml", ".yaml",
    ".txt", ".sh", ".ps1", ".html", ".css", ".sql", ".env", ".cfg", ".ini",
}

# --- Manifest loading ------------------------------------------------------
def load_manifests():
    """Return a list of manifest dicts, each augmented with _path and _readme."""
    manifests = []
    if not REGISTRY.exists():
        return manifests
    for manifest_path in sorted(REGISTRY.glob("*/*/manifest.json")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"  ! {manifest_path}: invalid JSON ({exc})")
            continue
        rel = manifest_path.parent.relative_to(ROOT).as_posix()
        data["_path"] = rel
        readme = manifest_path.parent / "README.md"
        data["_readme"] = readme.read_text(encoding="utf-8") if readme.exists() else ""
        manifests.append(data)
    return manifests


def validate_manifest(data):
    """Return a list of human-readable validation errors (empty == valid)."""
    errors = []
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if value in (None, "", []):
            errors.append(f"missing required field: {field}")
    if "type" in data and data["type"] not in VALID_TYPES:
        errors.append(
            f"invalid type '{data.get('type')}' (allowed: {', '.join(sorted(VALID_TYPES))})"
        )
    if "category" in data and data["category"] not in VALID_CATEGORIES:
        errors.append(
            f"invalid category '{data.get('category')}' "
            f"(allowed: {', '.join(sorted(VALID_CATEGORIES))})"
        )
    slug = data.get("slug", "")
    if slug and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        errors.append(f"slug '{slug}' must be kebab-case (a-z, 0-9, hyphens)")
    if data.get("confidentiality_attestation") is not True:
        errors.append("confidentiality_attestation must be true")
    return errors


# --- Sanitization scan -----------------------------------------------------
SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}")),
    ("OpenAI-style key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("Generic secret assignment", re.compile(
        r"""(?i)(?:api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['"][^'"]{8,}['"]"""
    )),
    ("Bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9\-\._~\+/]{20,}")),
]


def load_client_terms():
    """Load the configurable client-term blocklist (one term per line, # comments)."""
    terms = []
    if CLIENT_TERMS_FILE.exists():
        for line in CLIENT_TERMS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                terms.append(line)
    return terms


def scan_text(text, client_terms=None):
    """Scan a string. Return list of (severity, kind, detail) findings."""
    findings = []
    for kind, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            snippet = match.group(0)
            masked = snippet[:6] + "..." if len(snippet) > 6 else snippet
            findings.append(("secret", kind, masked))
    if client_terms:
        lowered = text.lower()
        for term in client_terms:
            if term.lower() in lowered:
                findings.append(("client-term", "blocklisted term", term))
    return findings


def scan_path(path, client_terms=None):
    """Scan a file or directory tree. Return list of (file, severity, kind, detail)."""
    path = Path(path)
    results = []
    files = [path] if path.is_file() else [
        p for p in path.rglob("*") if p.is_file()
    ]
    for f in files:
        if f.suffix.lower() not in SCANNABLE_SUFFIXES:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for severity, kind, detail in scan_text(text, client_terms):
            results.append((f.as_posix(), severity, kind, detail))
    return results
