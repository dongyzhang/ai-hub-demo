# Contributing to the Deloitte AI Hub

The Hub exists to share **reusable, genericized assets** built with Claude Code. Read this
before you submit anything.

## ⚠️ Confidentiality — the one rule that matters most

Deloitte work is bound by client confidentiality, independence, and data-residency
obligations. **Never** contribute:

- Client code, client data, deliverables, or anything produced *for* a specific client
- Client names, engagement codes, project code-names, or internal client identifiers
- Secrets: API keys, tokens, passwords, private keys, connection strings, PII
- Raw backups of working directories

**Do** contribute the *generalized capability*, stripped of any engagement specifics:
the skill, the agent, the prompt pattern, the utility, the training material, the demo app.

> Rule of thumb: if removing the client context breaks the asset, it isn't shareable yet —
> genericize it first.

## What you can share

| Type | Examples |
|------|----------|
| `skill` | A Claude Code skill others can drop in |
| `agent` | A subagent definition |
| `slash-command` | A reusable `/command` |
| `hook` | A settings.json hook |
| `claude-md` | A reusable `CLAUDE.md` pattern |
| `prompt` | A high-value prompt / prompt library |
| `app` | A small standalone app/demo built with Claude Code |
| `training` | How-to guides, playbooks, tutorials |
| `utility` | Scripts and helpers |

Categories: `Finance`, `Audit`, `Tax`, `Data`, `Engineering`, `Design`, `Productivity`,
`Risk`, `Other`.

## How to contribute

1. Run `python hub-cli/hub.py submit ./your-asset` (or `/share` in Claude Code).
2. The tool collects metadata, then runs an **automated sanitization scan**
   (secrets + a configurable client-term blocklist). It **blocks** on findings.
3. You must complete the **confidentiality attestation** — confirming the asset contains no
   client-confidential material. This is recorded in the manifest.
4. The tool packages the asset into `registry/assets/<team>/<slug>/` and (when configured)
   opens a Pull Request.
5. A **maintainer reviews the PR** — this human review is the second confidentiality gate —
   and merges. CI re-runs validation + the secret scan on every PR.

## The manifest

Every asset carries a `manifest.json` conforming to [`manifest.schema.json`](manifest.schema.json).
Required fields: `title`, `slug`, `description`, `type`, `category`, `author`, `team`,
`created`, and `confidentiality_attestation: true`.

## The sanitization scan is a safety net, not a guarantee

Automated scanning catches common mistakes; it cannot understand context. **You** are
responsible for the content you submit. When in doubt, don't submit — ask a maintainer.
