"""Build the catalog + report, then serve the website locally.

Usage:  python serve.py [port]   (default port 8080)
Stdlib only. Open http://localhost:<port> when it starts.
"""
import http.server
import socketserver
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def run(script):
    print(f"\n$ python scripts/{script}")
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)


def main():
    run("build_index.py")
    run("generate_report.py")

    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(WEB), **k)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n  AI Hub is live at http://localhost:{PORT}")
        print("  (Ctrl+C to stop)\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Stopped.")


if __name__ == "__main__":
    main()
