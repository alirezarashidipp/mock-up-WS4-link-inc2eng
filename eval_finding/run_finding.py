"""Serve the local, in-memory Finding evaluator."""

import argparse
import csv
import io
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen

# Read the project modules without creating bytecode files in the repository.
sys.dont_write_bytecode = True
EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))

import finding
from eval_finding.search import search_supplier

APP_ID = "ws4-finding-evaluator"


def default_reference(explicit_path):
    if explicit_path is not None:
        return explicit_path
    primary = finding.INPUT / "ENG_ALL.csv"
    alternative = finding.INPUT / "ALL_ENG.csv"
    return alternative if not primary.is_file() and alternative.is_file() else primary


def reference_label(path):
    if path.parent == finding.INPUT:
        return f"data/input/{path.name}"
    return path.name


class EvaluatorHandler(BaseHTTPRequestHandler):
    def log_message(self, message, *args):
        if sys.stderr is not None:
            super().log_message(message, *args)

    def reply(self, status, payload=b"", content_type="application/json; charset=utf-8"):
        if isinstance(payload, dict):
            payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # The browser can cancel an in-flight search when the input changes.

    def local_request(self):
        port = self.server.server_port
        local_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if port == 80:
            local_hosts.update(("127.0.0.1", "localhost"))
        host = self.headers.get("Host", "").lower()
        origin = self.headers.get("Origin")
        if host in local_hosts and (origin is None or origin == "http://" + host):
            return True
        self.reply(403, {"error": "Open the evaluator from its local server address."})
        return False

    def do_GET(self):
        if not self.local_request():
            return
        if self.path in ("/", "/index.html"):
            self.reply(200, (EVAL_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/reference":
            path = default_reference(self.server.reference_path)
            self.reply(200, {"app": APP_ID, "available": path.is_file(), "filename": path.name,
                             "location": reference_label(path)})
        elif self.path == "/favicon.ico":
            self.reply(204)
        else:
            self.reply(404, {"error": "Page not found."})

    def do_POST(self):
        if not self.local_request():
            return
        if self.path != "/api/search":
            self.reply(404, {"error": "Page not found."})
            return
        try:
            raw_name = self.headers.get("X-Supplier-Name")
            if raw_name is None:
                raise ValueError("Enter a supplier name.")
            supplier = unquote(raw_name, errors="strict")
            filename = self.headers.get("X-Reference-Name")
            if filename is None:
                path = default_reference(self.server.reference_path)
                if not path.is_file():
                    raise ValueError(f"Cannot find {reference_label(path)}. Check the file location and press Enter again.")
                with path.open(encoding="utf-8-sig", newline="") as source:
                    result = search_supplier(supplier, source, path.name)
            else:
                # The uploaded name is only a display label; never resolve it on the server.
                label = Path(unquote(filename, errors="strict")).name
                if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length") is None:
                    raise ValueError("The selected CSV must have a known size.")
                length = int(self.headers["Content-Length"])
                if length < 0 or Path(label).suffix.lower() != ".csv":
                    raise ValueError("Select a CSV engagement file.")
                data = self.rfile.read(length)
                if len(data) != length:
                    raise ValueError("The CSV upload was interrupted.")
                with io.TextIOWrapper(io.BytesIO(data), encoding="utf-8-sig", newline="") as source:
                    result = search_supplier(supplier, source, label)
        except UnicodeError:
            self.reply(400, {"error": "Use a UTF-8 encoded CSV."})
            return
        except (ValueError, csv.Error, OSError) as error:
            self.reply(400, {"error": str(error)})
            return
        self.reply(200, result)


def evaluator_is_running(address):
    try:
        with urlopen(address + "api/reference", timeout=2) as response:
            info = json.load(response)
        return isinstance(info, dict) and info.get("app") == APP_ID
    except (OSError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eng-all", type=Path, help="Default engagement CSV path.")
    parser.add_argument("--port", type=int, default=8765, help="Local HTTP port (default: 8765).")
    parser.add_argument("--no-browser", action="store_true", help="Print the address without opening a tab.")
    args = parser.parse_args()
    address = f"http://127.0.0.1:{args.port}/"
    if args.port and not args.eng_all and not args.no_browser and evaluator_is_running(address):
        webbrowser.open(address)
        return
    with ThreadingHTTPServer(("127.0.0.1", args.port), EvaluatorHandler) as server:
        server.reference_path = args.eng_all.resolve() if args.eng_all else None
        address = f"http://127.0.0.1:{server.server_port}/"
        if sys.stdout is not None:
            print(f"Finding evaluator: {address}", flush=True)
        if not args.no_browser:
            webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
