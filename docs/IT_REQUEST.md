# Request to GitHub Enterprise admins — AI Hub org

_A one-page ask. Hand this to whoever owns Deloitte's GitHub Enterprise._

## What we're building
An internal **AI Hub**: a place for professionals to share reusable, **genericized**
Claude Code assets (skills, tools, training, small apps) and give leadership a firm-wide
view of what's being built. **No client code or client data is stored or accessed** — the
Hub only holds assets people deliberately submit (after an automated confidentiality scan)
plus a code-free `hub.json` activity summary from each repo.

## What we need provisioned
1. **A GitHub Organization** — proposed name `deloitte-ai-hub` — inside our Enterprise.
2. **SSO + SCIM** connected to Deloitte identity, so employees can join with their normal
   login and be sorted into teams automatically.
3. **Org-wide guardrails on:** Secret Scanning, **Push Protection**, and Dependabot alerts.
4. **A private repo** `registry` in that org, with:
   - Base member permission = **Write** (propose via PR), and a `hub-maintainers` team = **Maintain**.
   - **Branch protection** on `main`: require PR + passing checks + Code Owner review.
   - **GitHub Pages** enabled (source = GitHub Actions) for the internal catalog site.
5. **A read-only GitHub App** ("AI Hub") — permissions limited to **Contents: Read** and
   **Metadata: Read** — installed on all repos, with a token we can store as an Actions secret.
6. **Practice teams**: `finance-leads`, `audit-leads`, `tax-leads`, `data-leads`,
   `engineering-leads`, `consulting-leads`, `hub-maintainers`.

## What we are explicitly NOT asking for
- No write access to anyone's repos.
- No ability for the Hub to read source code (the App is read-only and we only parse `hub.json`).
- No storage of client deliverables, data, or identifiers anywhere in the Hub.

## Security posture
- Every contribution passes an automated secret + client-term scan in CI and a human
  Code Owner review before merge.
- The Hub is internal-only (private repo + internal Pages).
- Contribution is opt-in; nothing syncs automatically.

_Contact: dongyzhang@deloitte.com_
