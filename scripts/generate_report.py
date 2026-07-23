"""Generate the "super brain" narrative report over all contributed assets.

If ANTHROPIC_API_KEY is set, calls the Claude API (claude-opus-4-8) via stdlib urllib.
Otherwise writes a deterministic offline report so the demo always works.

Usage:  python scripts/generate_report.py
Output: web/data/report.md
Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from common import VALID_CATEGORIES, WEB_DATA, load_manifests, validate_manifest

MODEL = "claude-opus-4-8"
API_URL = "https://api.anthropic.com/v1/messages"


def valid_assets():
    return [m for m in load_manifests() if not validate_manifest(m)]


def build_prompt(assets):
    lines = [
        "You are the analytics engine for Deloitte's internal AI Hub, where professionals "
        "share reusable Claude Code assets (skills, agents, apps, training, utilities).",
        "Below is the full catalog. Write a concise firm-wide intelligence report in Markdown with these sections:",
        "1. **Executive summary** (3-4 sentences).",
        "2. **Themes** — what people are building and why it matters.",
        "3. **Duplicate / overlapping effort** — assets that look similar across teams, with a consolidation recommendation.",
        "4. **Coverage gaps** — categories or needs that look under-served.",
        "5. **Recommendations** — 3-5 concrete next actions for firm leadership.",
        "Be specific, reference asset titles and teams. Do not invent assets not listed.",
        "",
        "CATALOG:",
    ]
    for a in assets:
        lines.append(
            f"- [{a['type']} | {a['category']} | team {a['team']}] "
            f"\"{a['title']}\" — {a['description']} "
            f"(tags: {', '.join(a.get('tags', [])) or 'none'}; "
            f"tools: {', '.join(a.get('tools', [])) or 'none'})"
        )
    return "\n".join(lines)


def call_claude(prompt, api_key):
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return "".join(
        block.get("text", "") for block in body.get("content", [])
        if block.get("type") == "text"
    ).strip()


def offline_report(assets):
    """Deterministic fallback: real analysis, computed locally (no LLM)."""
    total = len(assets)
    by_cat = Counter(a["category"] for a in assets)
    by_team = Counter(a["team"] for a in assets)
    by_type = Counter(a["type"] for a in assets)

    # Overlap heuristic: assets sharing >=1 tag AND from different teams.
    tag_index = defaultdict(list)
    for a in assets:
        for t in a.get("tags", []):
            tag_index[t.lower()].append(a)
    overlaps = []
    seen_pairs = set()
    for tag, group in tag_index.items():
        teams = {a["team"] for a in group}
        if len(group) >= 2 and len(teams) >= 2:
            titles = sorted({a["title"] for a in group})
            key = tuple(titles)
            if key not in seen_pairs:
                seen_pairs.add(key)
                overlaps.append((tag, titles, sorted(teams)))

    gaps = sorted(VALID_CATEGORIES - set(by_cat))

    md = []
    md.append("## Executive summary")
    md.append(
        f"The Hub currently holds **{total} shared asset(s)** across "
        f"**{len(by_cat)} categor{'y' if len(by_cat)==1 else 'ies'}** and "
        f"**{len(by_team)} team(s)**. The most active category is "
        f"**{by_cat.most_common(1)[0][0]}** and the most common asset type is "
        f"**{by_type.most_common(1)[0][0]}**. "
        "This is a deterministic offline summary — set `ANTHROPIC_API_KEY` to generate the "
        "richer Claude-authored narrative."
    )
    md.append("\n## Themes")
    for cat, n in by_cat.most_common():
        exemplars = ", ".join(f"“{a['title']}”" for a in assets if a["category"] == cat)
        md.append(f"- **{cat}** ({n}): {exemplars}")

    md.append("\n## Duplicate / overlapping effort")
    if overlaps:
        for tag, titles, teams in overlaps:
            md.append(
                f"- Shared theme **`{tag}`** appears in {', '.join(titles)} "
                f"across teams {', '.join(teams)} — **review for consolidation** into one "
                "canonical asset."
            )
    else:
        md.append("- No cross-team overlaps detected yet.")

    md.append("\n## Coverage gaps")
    if gaps:
        md.append(
            "- Categories with **no** contributions yet: "
            + ", ".join(f"**{g}**" for g in gaps)
            + ". Consider commissioning assets here."
        )
    else:
        md.append("- Every category has at least one asset.")

    md.append("\n## Recommendations")
    md.append("1. Consolidate the overlapping assets above to avoid duplicated maintenance.")
    md.append("2. Commission contributions for the empty categories.")
    md.append("3. Recognize top contributors to sustain momentum.")
    md.append("4. Re-run this report weekly (a GitHub Action does this automatically).")
    return "\n".join(md)


def main():
    assets = valid_assets()
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not assets:
        body = "_No valid assets to report on yet._"
        source = "empty"
    elif api_key:
        try:
            print(f"  Calling Claude ({MODEL}) over {len(assets)} asset(s)…")
            body = call_claude(build_prompt(assets), api_key)
            source = f"Claude {MODEL}"
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            print(f"  ! Claude API call failed ({exc}); using offline fallback.")
            body = offline_report(assets)
            source = "offline fallback (API error)"
    else:
        print("  ANTHROPIC_API_KEY not set — using deterministic offline report.")
        body = offline_report(assets)
        source = "offline fallback"

    header = (
        f"# AI Hub — Super Brain Report\n\n"
        f"_Generated {generated_at} · source: {source} · {len(assets)} asset(s)_\n\n"
    )
    (WEB_DATA / "report.md").write_text(header + body + "\n", encoding="utf-8")
    print(f"  Wrote {(WEB_DATA / 'report.md').as_posix()} ({source}).")


if __name__ == "__main__":
    main()
