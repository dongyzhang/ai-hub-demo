"""One command to update the live site.

Rebuilds the catalog + super-brain report, commits, and publishes the web/ folder to the
gh-pages branch (the GitHub Pages source). GitHub Pages then redeploys automatically.

Usage:  python scripts/publish_site.py

Note: this is the "no workflow-scope needed" auto-update path. If your token later gains
the `workflow` scope, push .github/workflows/ instead and this becomes fully automatic in
the cloud (push to main -> Actions rebuild + deploy).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, check=True):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if check and r.returncode:
        sys.exit(r.returncode)
    return r.returncode


def main():
    run([sys.executable, "scripts/build_index.py"], check=False)
    run([sys.executable, "scripts/generate_report.py"])
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", "build: refresh site data"], check=False)
    run(["git", "push", "origin", "main"], check=False)
    # Rebuild the gh-pages branch from the web/ subtree and publish it.
    run(["git", "branch", "-D", "gh-pages"], check=False)
    run(["git", "subtree", "split", "--prefix", "web", "-b", "gh-pages"])
    run(["git", "push", "-f", "origin", "gh-pages"])
    print("\n  Published. The live site redeploys in ~1 minute.")


if __name__ == "__main__":
    main()
