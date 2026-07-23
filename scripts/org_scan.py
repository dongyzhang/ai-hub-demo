"""Metadata-only org oversight (the safe slice of "the Hub sees everyone").

Reads ONLY each repo's root `hub.json` across a GitHub organization — never source code,
never client material — and aggregates them into web/data/org_map.json for a firm-wide map.

Usage:
  GITHUB_TOKEN=<token> python scripts/org_scan.py <org>

The token needs read-only access to repo metadata + contents. In CI this is the
"AI Hub" GitHub App token stored as the HUB_APP_TOKEN secret.

Stdlib only (urllib).
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

API = "https://api.github.com"
WEB_DATA = Path(__file__).resolve().parent.parent / "web" / "data"


def gh(path, token):
    req = urllib.request.Request(
        API + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-hub-org-scan",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def list_repos(org, token):
    repos, page = [], 1
    while True:
        batch = gh(f"/orgs/{org}/repos?per_page=100&page={page}&type=all", token)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def get_hub_json(full_name, token):
    """Fetch and parse root hub.json for owner/repo. Returns dict or None (404)."""
    try:
        meta = gh(f"/repos/{full_name}/contents/hub.json", token)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    try:
        raw = base64.b64decode(meta.get("content", "")).decode("utf-8", "ignore")
        return json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        print(f"  ! {full_name}: hub.json is not valid JSON — skipping.")
        return None


def main():
    if len(sys.argv) < 2:
        print("usage: GITHUB_TOKEN=<token> python scripts/org_scan.py <org>")
        return 1
    org = sys.argv[1]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("HUB_APP_TOKEN")
    if not token:
        print(
            "GITHUB_TOKEN not set. This step aggregates each repo's code-free hub.json\n"
            "across the org for firm-wide oversight. Set a read-only token and re-run:\n"
            "  GITHUB_TOKEN=ghp_xxx python scripts/org_scan.py <org>"
        )
        return 1

    print(f"  Scanning org '{org}' for hub.json files (metadata only)…")
    repos = list_repos(org, token)
    entries, projects = [], 0
    for repo in repos:
        hub = get_hub_json(repo["full_name"], token)
        if not hub:
            continue
        proj = hub.get("projects", [])
        projects += len(proj)
        entries.append({
            "repo": repo["full_name"],
            "team": hub.get("team", "Unknown"),
            "owner": hub.get("owner", "Unknown"),
            "updated": repo.get("pushed_at"),
            "projects": proj,
        })
        print(f"    + {repo['full_name']}: {len(proj)} project(s)")

    WEB_DATA.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "org": org,
        "repos_scanned": len(repos),
        "repos_reporting": len(entries),
        "projects": projects,
        "entries": entries,
    }
    (WEB_DATA / "org_map.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(
        f"\n  Wrote {(WEB_DATA / 'org_map.json').as_posix()}\n"
        f"  {len(entries)}/{len(repos)} repos report hub.json · {projects} project(s) mapped."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
