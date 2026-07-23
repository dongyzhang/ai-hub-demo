---
description: Share a reusable asset with the Deloitte AI Hub (packages it, scans for secrets/client terms, writes it into the registry, and prepares a PR).
---

The user wants to share an asset with the Deloitte AI Hub.

Steps:

1. Ask the user which folder or file is the asset they want to share (if `$ARGUMENTS`
   already contains a path, use that).

2. Before packaging, **read the asset's files yourself** and sanity-check for anything
   client-confidential (client names, engagement codes, secrets, PII). If you see anything
   concerning, stop and tell the user to genericize it first — cite `CONTRIBUTING.md`.

3. Help the user fill in the metadata: title, slug (kebab-case), one-line description,
   `type` (skill/agent/slash-command/hook/claude-md/prompt/app/training/utility),
   `category` (Finance/Audit/Tax/Data/Engineering/Design/Productivity/Risk/Other),
   team, author, tags, tools. Suggest sensible values from the asset's README.

4. Run the contribution CLI (it re-runs the automated secret + client-term scan and
   requires the confidentiality attestation):

   ```bash
   python hub-cli/hub.py submit "<PATH>" --title "<TITLE>" --slug <SLUG> \
     --type <TYPE> --category <CATEGORY> --team "<TEAM>" --author "<AUTHOR>" \
     --description "<DESCRIPTION>" --tags <t1,t2> --tools <t1,t2> --attest --yes
   ```

   If the scan blocks the submission, show the findings to the user and help them fix the
   source before retrying. Do **not** bypass the scan.

5. After it succeeds, run `python scripts/build_index.py` so the asset appears in the
   catalog, and show the user the PR commands the CLI printed (or offer to run them with
   `--pr` if they want to open the Pull Request now).
