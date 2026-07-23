"""Publish changes to the live AI Hub.

Commits everything and pushes to main. GitHub Actions then rebuilds the catalog +
super-brain report and redeploys the site automatically — no other step needed.

Usage:  python scripts/publish_site.py ["commit message"]
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
message = sys.argv[1] if len(sys.argv) > 1 else "Update AI Hub content"


def run(cmd, check=True):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if check and r.returncode:
        sys.exit(r.returncode)


def main():
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", message], check=False)  # ok if nothing to commit
    run(["git", "push", "origin", "main"])
    print("\n  Pushed. GitHub Actions is now rebuilding + deploying the site (~1-2 min).")


if __name__ == "__main__":
    main()
