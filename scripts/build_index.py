"""Build the catalog + stats from registry/assets into web/data/.

Usage:  python scripts/build_index.py
Outputs: web/data/assets.json, web/data/stats.json
Stdlib only.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from common import WEB_DATA, load_manifests, validate_manifest

PUBLIC_FIELDS = [
    "title", "slug", "description", "type", "category", "tags", "tools",
    "author", "team", "created", "demo_url", "screenshot",
]


def build():
    manifests = load_manifests()
    assets = []
    errors_total = 0

    for m in manifests:
        errs = validate_manifest(m)
        if errs:
            errors_total += 1
            print(f"  ! {m.get('_path', '?')}: {'; '.join(errs)}")
            continue
        asset = {k: m.get(k) for k in PUBLIC_FIELDS if k in m}
        asset["tags"] = m.get("tags", [])
        asset["tools"] = m.get("tools", [])
        asset["path"] = m.get("_path")
        asset["readme"] = m.get("_readme", "")
        assets.append(asset)

    assets.sort(key=lambda a: a.get("created", ""), reverse=True)
    stats = compute_stats(assets)

    WEB_DATA.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    (WEB_DATA / "assets.json").write_text(
        json.dumps({"generated_at": generated_at, "assets": assets}, indent=2),
        encoding="utf-8",
    )
    (WEB_DATA / "stats.json").write_text(
        json.dumps({"generated_at": generated_at, **stats}, indent=2),
        encoding="utf-8",
    )

    print(f"\n  Indexed {len(assets)} asset(s) into {WEB_DATA.as_posix()}")
    if errors_total:
        print(f"  Skipped {errors_total} invalid manifest(s) — see warnings above.")
    return errors_total


def compute_stats(assets):
    by_category = Counter(a["category"] for a in assets)
    by_type = Counter(a["type"] for a in assets)
    by_team = Counter(a["team"] for a in assets)
    by_author = Counter(a["author"] for a in assets)
    by_month = Counter((a.get("created") or "")[:7] for a in assets if a.get("created"))

    tools = Counter()
    tags = Counter()
    for a in assets:
        tools.update(a.get("tools", []))
        tags.update(a.get("tags", []))

    def top(counter, n=None):
        items = counter.most_common(n)
        return [{"name": k, "count": v} for k, v in items]

    return {
        "total": len(assets),
        "by_category": top(by_category),
        "by_type": top(by_type),
        "by_team": top(by_team),
        "by_month": sorted(
            ({"name": k, "count": v} for k, v in by_month.items()),
            key=lambda x: x["name"],
        ),
        "top_contributors": top(by_author, 10),
        "top_tools": top(tools, 12),
        "top_tags": top(tags, 15),
    }


if __name__ == "__main__":
    sys.exit(1 if build() else 0)
