# `hub.json` — the code-free oversight file

This is the heart of the **Curated + metadata** model you chose. Each professional's repo
can drop a single small file, `hub.json`, at its root. It describes *what* the person is
working on — **never the code, data, or any client detail**.

The Hub's `org_scan.py` reads **only this file** across the organization. It never reads
source code, so leadership gets a firm-wide map of activity with zero confidentiality risk.

## Format

```json
{
  "team": "Finance Transformation",
  "owner": "Sofia Alvarez",
  "projects": [
    {
      "name": "Close automation experiments",
      "category": "Finance",
      "status": "active",
      "tags": ["close", "automation"],
      "summary": "Trying Claude Code to speed up month-end close prep."
    },
    {
      "name": "Variance commentary helper",
      "category": "Finance",
      "status": "shared",
      "tags": ["variance", "reporting"],
      "summary": "Drafts first-pass variance narratives. Shared to the Hub."
    }
  ]
}
```

## Field rules

| Field | Meaning |
|-------|---------|
| `team` | Practice / team name (matches the taxonomy) |
| `owner` | Display name of the person |
| `projects[].name` | Short, **generic** project name — no client names |
| `projects[].category` | One of the Hub categories (Finance, Audit, Tax, Data, …) |
| `projects[].status` | `active`, `shared`, `paused`, or `archived` |
| `projects[].tags` | Free keywords |
| `projects[].summary` | **One line, no client-identifying information** |

## The golden rule

`hub.json` is *self-reported* and must contain **nothing client-confidential** — no client
names, engagement codes, data, or code. It is a headline, not a deliverable. The same
sanitization scan that guards `/share` also checks `hub.json` in CI.
