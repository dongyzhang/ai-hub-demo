# GitHub setup & management guide

How to put everyone on one GitHub and keep uploads managed. Two audiences:
**(A)** what your GitHub Enterprise **admin/IT** does once, and **(B)** what **you** (the Hub
owner) do in the `registry` repo. Written for the **Curated + metadata** oversight model.

---

## Part 1 — Getting everyone onto one GitHub

You do **not** invite people one at a time. The structure is:

```
Deloitte GitHub Enterprise   (owned by IT)
        └── Organization: deloitte-ai-hub
                ├── Teams:  finance-leads, audit-leads, tax-leads, data-leads,
                │            engineering-leads, consulting-leads, hub-maintainers
                └── Repos:  registry  (the Hub)  +  each person's / team's repos
```

### What IT / the Enterprise admin sets up (one-time)
1. **Create the Organization** `deloitte-ai-hub` inside Deloitte's GitHub Enterprise.
2. **Connect SSO** — link the org to Deloitte's identity provider (SAML/Entra). This is the
   "add everyone" step: once SSO is on, any Deloitte employee can join with their normal
   login, and (with SCIM) can be auto-provisioned. No manual invites at scale.
3. **Enable org-wide guardrails**: Secret Scanning + **Push Protection** (blocks commits that
   contain secrets before they ever land) and Private Vulnerability Reporting.
4. **Create Teams** (per practice) and map them to your SSO groups so membership stays in sync.

> This is a request you make to whoever owns Deloitte's GitHub Enterprise. Use the
> one-page ask in [`docs/IT_REQUEST.md`](IT_REQUEST.md).

### What each professional does (self-serve, ~2 min)
```bash
gh auth login          # sign in once with their Deloitte GitHub
```
That's it. To share something they run `/share` in Claude Code (or `python hub-cli/hub.py submit`).

---

## Part 2 — How uploads are managed (the anti-chaos rules)

The whole model rests on one principle: **nobody writes directly to the Hub's `main`
branch. Every upload is a reviewed Pull Request.**

### Permissions (who can do what)
| Role | GitHub permission on `registry` | Can they… |
|------|--------------------------------|-----------|
| Every member | **Write** | Create branches + open PRs. **Cannot** merge to `main`. |
| Practice leads | via CODEOWNERS | Required reviewer for their category's PRs. |
| `hub-maintainers` | **Maintain** | Merge PRs, manage settings. |

Set the base member permission on the repo to *Write*, and grant `hub-maintainers`
*Maintain*. Branch protection (below) is what actually stops members merging to `main`.

### The upload lifecycle
```
person runs /share
   → new branch  asset/<team>-<slug>
   → Pull Request opened into registry:main
   → CI runs automatically:  manifest validation + secret/client-term scan
   → CODEOWNERS auto-requests the practice lead's review
   → lead approves  →  maintainer merges
   → Actions rebuild catalog + report  →  GitHub Pages redeploys
```
If CI finds a secret or a blocklisted client term, the PR **cannot be merged** until it's fixed.

### Why it stays tidy
- Assets always land in `registry/assets/<team>/<slug>/` — **namespaced per team**, so two
  people can't collide, and the folder tree mirrors the org.
- `manifest.json` on every asset keeps naming/metadata consistent (enforced by CI).
- `CODEOWNERS` distributes review load to the right people instead of one bottleneck.

### Turn on branch protection (you, once the repo exists)
Requires PR, passing CI, and a Code Owner review before anyone can merge to `main`:
```bash
gh api -X PUT repos/deloitte-ai-hub/registry/branches/main/protection \
  -F required_pull_request_reviews.required_approving_review_count=1 \
  -F required_pull_request_reviews.require_code_owner_reviews=true \
  -F "required_status_checks.contexts[]=validate" \
  -F required_status_checks.strict=true \
  -F enforce_admins=true \
  -F restrictions=null
```

---

## Part 3 — The metadata oversight (Curated + metadata)

Beyond what people actively share, the Hub gets a **firm-wide map** without reading anyone's
code:
1. Each repo drops a code-free **`hub.json`** at its root (see
   [`HUB_METADATA_SPEC.md`](HUB_METADATA_SPEC.md)).
2. The **"AI Hub" GitHub App** (read-only, installed org-wide) provides a token.
3. `scripts/org_scan.py` reads only those `hub.json` files and builds `web/data/org_map.json`:
   ```bash
   GITHUB_TOKEN=<app-token> python scripts/org_scan.py deloitte-ai-hub
   ```
This is the safe half of "one Hub oversees everyone" — full visibility of *activity*,
zero access to *content*.

### Creating the GitHub App (admin, one-time)
- Org **Settings → Developer settings → GitHub Apps → New**.
- Permissions: **Repository → Contents: Read-only**, **Metadata: Read-only**. Nothing else.
- Install it on **All repositories** in the org.
- Generate a token and store it as the Actions secret `HUB_APP_TOKEN` on `registry`.

---

## One-time checklist

**Admin / IT**
- [ ] Create org `deloitte-ai-hub`; enable SSO (+ SCIM).
- [ ] Enable Secret Scanning + Push Protection org-wide.
- [ ] Create practice Teams; map to SSO groups.
- [ ] Create the `registry` repo; set base permission = Write; grant `hub-maintainers` = Maintain.
- [ ] Create + install the read-only "AI Hub" App; save `HUB_APP_TOKEN`.
- [ ] Add `ANTHROPIC_API_KEY` secret (for the report).
- [ ] Enable GitHub Pages (source = GitHub Actions).

**You (Hub owner)**
- [ ] Push this project into the `registry` repo.
- [ ] Turn on branch protection (command above).
- [ ] Edit `.github/CODEOWNERS` with your real team handles.
- [ ] Announce `/share` to the pilot group.
