"""AI Hub contribution CLI (stdlib only).

Commands:
  submit <path>   Package an asset, run the sanitization scan, write it into the registry,
                  and print the PR commands (or open a PR with --pr).
  validate        Validate every manifest in the registry.
  list            List catalogued assets.

The `submit` flow is interactive by default. For automation/testing, pass all metadata as
flags plus --attest --yes.

Examples:
  python hub-cli/hub.py submit ./my-asset
  python hub-cli/hub.py submit ./my-asset --title "PDF Splitter" --slug pdf-splitter \\
      --type skill --category Engineering --team "Engineering" --author "Jane Doe" \\
      --description "Splits PDFs by bookmarks." --tags pdf,automation --tools Python \\
      --attest --yes
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 console output on Windows (cp1252 consoles otherwise crash on symbols).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import (  # noqa: E402
    REGISTRY, ROOT, VALID_CATEGORIES, VALID_TYPES,
    load_client_terms, load_manifests, scan_path, validate_manifest,
)
import json  # noqa: E402


def _git(*args):
    try:
        out = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
        )
        return out.stdout.strip()
    except FileNotFoundError:
        return ""


def _prompt(label, default=None, required=True, choices=None):
    suffix = f" [{default}]" if default else ""
    if choices:
        suffix += f" ({'/'.join(sorted(choices))})"
    while True:
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw and not required:
            return ""
        if not raw:
            print("  (required)")
            continue
        if choices and raw not in choices:
            print(f"  must be one of: {', '.join(sorted(choices))}")
            continue
        return raw


def _slugify(text):
    import re
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def cmd_submit(args):
    src = Path(args.path).resolve()
    if not src.exists():
        print(f"error: path not found: {src}")
        return 1

    interactive = not args.yes
    git_name = _git("config", "user.name")
    git_email = _git("config", "user.email")

    # --- collect metadata ---
    if interactive:
        print("\n== Share an asset with the Deloitte AI Hub ==\n")
        title = args.title or _prompt("Title")
        slug = args.slug or _prompt("Slug (kebab-case)", default=_slugify(title))
        description = args.description or _prompt("Short description")
        atype = args.type or _prompt("Type", choices=VALID_TYPES)
        category = args.category or _prompt("Category", choices=VALID_CATEGORIES)
        team = args.team or _prompt("Team")
        author = args.author or _prompt("Author", default=git_name or None)
        tags = args.tags or _prompt("Tags (comma-separated)", required=False)
        tools = args.tools or _prompt("Tools/tech (comma-separated)", required=False)
    else:
        title = args.title or src.name
        slug = args.slug or _slugify(title)
        description = args.description or f"{title} (submitted via CLI)."
        atype = args.type or "utility"
        category = args.category or "Other"
        team = args.team or (git_name and f"{git_name}'s team") or "Unknown"
        author = args.author or git_name or "Unknown"
        tags = args.tags or ""
        tools = args.tools or ""

    if atype not in VALID_TYPES:
        print(f"error: invalid type '{atype}'"); return 1
    if category not in VALID_CATEGORIES:
        print(f"error: invalid category '{category}'"); return 1

    # --- sanitization scan ---
    print("\n-- Running sanitization scan (secrets + client terms) --")
    findings = scan_path(src, load_client_terms())
    if findings:
        print(f"\n  [BLOCKED] {len(findings)} potential issue(s) found:\n")
        for f, severity, kind, detail in findings:
            print(f"    [{severity}] {kind}: {detail}   ({f})")
        print(
            "\n  Remove/genericize the above before submitting. The Hub never accepts "
            "client-confidential material or secrets. (See CONTRIBUTING.md)"
        )
        return 2
    print("  [OK] No secrets or blocklisted client terms detected.")

    # --- confidentiality attestation ---
    if args.attest:
        attested = True
    elif interactive:
        print(
            "\n  CONFIDENTIALITY ATTESTATION\n"
            "  By continuing you confirm this asset contains NO client-confidential\n"
            "  material, data, code, names, or engagement identifiers, and is safe to\n"
            "  share firm-wide."
        )
        attested = input("  Type 'yes' to attest: ").strip().lower() == "yes"
    else:
        attested = False
    if not attested:
        print("  Attestation not given — aborting.")
        return 3

    # --- build manifest ---
    manifest = {
        "title": title,
        "slug": slug,
        "description": description,
        "type": atype,
        "category": category,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "tools": [t.strip() for t in tools.split(",") if t.strip()],
        "author": author,
        "team": team,
        "created": datetime.date.today().isoformat(),
        "confidentiality_attestation": True,
    }
    errs = validate_manifest(manifest)
    if errs:
        print("error: manifest invalid:\n  - " + "\n  - ".join(errs))
        return 1

    # --- write into registry ---
    dest = REGISTRY / _slugify(team) / slug
    if dest.exists() and not args.force:
        print(f"error: {dest} already exists (use --force to overwrite)")
        return 1
    dest.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        for item in src.iterdir():
            if item.name in {"manifest.json"}:
                continue
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
    else:
        shutil.copy2(src, dest / src.name)

    if not (dest / "README.md").exists():
        (dest / "README.md").write_text(f"# {title}\n\n{description}\n", encoding="utf-8")

    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rel = dest.relative_to(ROOT).as_posix()
    print(f"\n  [OK] Asset written to {rel}")

    # --- PR guidance / execution ---
    branch = f"asset/{_slugify(team)}-{slug}"
    print("\n-- To open a Pull Request to the central Hub, run: --\n")
    for c in [
        f"git checkout -b {branch}",
        f"git add {rel}",
        f'git commit -m "Add asset: {title}"',
        f"git push -u origin {branch}",
        f'gh pr create --fill --title "Add asset: {title}"',
    ]:
        print(f"    {c}")

    if args.pr:
        print("\n-- --pr set: running the above --")
        for c in [
            ["git", "checkout", "-b", branch],
            ["git", "add", rel],
            ["git", "commit", "-m", f"Add asset: {title}"],
            ["git", "push", "-u", "origin", branch],
            ["gh", "pr", "create", "--fill", "--title", f"Add asset: {title}"],
        ]:
            print(f"    $ {' '.join(c)}")
            r = subprocess.run(c, cwd=ROOT)
            if r.returncode != 0:
                print("    (command failed — stopping PR automation)")
                break

    print("\n  Tip: run `python scripts/build_index.py` to see it in the catalog.")
    return 0


def cmd_validate(args):
    manifests = load_manifests()
    if not manifests:
        print("No assets found in registry/assets.")
        return 0
    bad = 0
    for m in manifests:
        errs = validate_manifest(m)
        if errs:
            bad += 1
            print(f"  [FAIL] {m['_path']}\n      - " + "\n      - ".join(errs))
        else:
            print(f"  [OK] {m['_path']}")
    print(f"\n{len(manifests) - bad}/{len(manifests)} valid.")
    return 1 if bad else 0


def cmd_list(args):
    manifests = load_manifests()
    for m in manifests:
        print(f"  [{m.get('type','?'):<13}] {m.get('title','?'):<34} "
              f"{m.get('category','?'):<12} {m.get('team','?')}")
    print(f"\n{len(manifests)} asset(s).")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="hub", description="Deloitte AI Hub contribution CLI")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("submit", help="submit an asset to the Hub")
    s.add_argument("path", help="path to the asset file or folder")
    for flag in ["title", "slug", "description", "type", "category", "team", "author",
                 "tags", "tools"]:
        s.add_argument(f"--{flag}")
    s.add_argument("--attest", action="store_true", help="pre-confirm confidentiality attestation")
    s.add_argument("--yes", action="store_true", help="non-interactive (use flags/defaults)")
    s.add_argument("--pr", action="store_true", help="actually create the git branch + PR")
    s.add_argument("--force", action="store_true", help="overwrite an existing asset folder")
    s.set_defaults(func=cmd_submit)

    sub.add_parser("validate", help="validate all manifests").set_defaults(func=cmd_validate)
    sub.add_parser("list", help="list catalogued assets").set_defaults(func=cmd_list)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
