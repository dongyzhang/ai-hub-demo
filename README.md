# Deloitte AI Hub

A central place where Deloitte professionals **share the reusable things they build with
Claude Code** — skills, agents, slash commands, hooks, `CLAUDE.md` configs, prompts,
utilities, small apps, and training content — so the whole firm can discover, reuse, and
learn from them.

The hub connects individual Claude Code users into one "cluster," and runs analytics over
everything contributed to produce a firm-wide **"super brain"** view: what's being built,
where effort is duplicated, and where the gaps are.

> **Confidentiality first.** We share **reusable, genericized assets — never raw client
> code or client data.** Contribution is curated and opt-in, with an automated
> sanitization scan and a human review gate. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## How it works

```
Individual's Claude Code            Central Hub (this repo / a GitHub org)      Everyone
┌────────────────────┐   PR/merge   ┌───────────────────────────────┐  build  ┌───────────┐
│ /share  (slash cmd)│ ───────────▶ │ registry/assets/<team>/<slug>/│ ──────▶ │ Catalog   │
│ python hub-cli     │              │   manifest.json + README.md   │  index  │ website   │
│  • collect metadata│              │                               │         │ browse    │
│  • sanitize / scan │              │ scripts/build_index.py        │         │ products  │
│  • package + PR    │              │ scripts/generate_report.py    │         │ training  │
└────────────────────┘              └───────────────────────────────┘         │ analytics │
                                                                               └───────────┘
```

**Key idea:** the git repo *is* the database. Each asset is a folder with a `manifest.json`.
No server, no DB. PR review doubles as the confidentiality gate.

---

## Repo layout

| Path | What it is |
|------|-----------|
| `registry/assets/<team>/<slug>/` | One shared asset: `manifest.json` + `README.md` + files |
| `manifest.schema.json` | The manifest contract (fields, allowed types & categories) |
| `scripts/build_index.py` | Reads all manifests → generates `web/data/assets.json` + `stats.json` |
| `scripts/generate_report.py` | Claude-generated "super brain" narrative → `web/data/report.md` |
| `hub-cli/hub.py` | Contribution tool: `submit`, `validate`, `list` |
| `web/` | The catalog website (static HTML/CSS/JS, no build step) |
| `.claude/commands/share.md` | The `/share` Claude Code slash command |
| `.github/workflows/` | CI validation, Pages deploy, weekly report |
| `.github/CODEOWNERS` | Routes each PR to the right practice lead for review |
| `scripts/org_scan.py` | Metadata-only oversight: aggregates each repo's `hub.json` |
| `docs/GITHUB_SETUP.md` | How to get everyone on one GitHub + manage uploads |
| `docs/IT_REQUEST.md` | One-page ask for your GitHub Enterprise admins |
| `docs/HUB_METADATA_SPEC.md` | The code-free `hub.json` oversight file spec |

---

## Quick start (no installs required — Python 3 only)

```bash
python scripts/build_index.py          # generate the catalog + stats from registry/
python scripts/generate_report.py      # generate the analytics narrative (offline fallback if no API key)
python serve.py                        # build + serve the website at http://localhost:8080
```

Then open **http://localhost:8080**.

### Share an asset

Interactive:

```bash
python hub-cli/hub.py submit ./path/to/my-asset
```

Or from Claude Code, just run **`/share`**.

---

## Status

MVP / demo. See the plan and the "Open items" (GitHub org ownership, security sign-off on
what counts as "shareable", API vs internal gateway for the report) before firm-wide rollout.
