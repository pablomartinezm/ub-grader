import json
import pathlib
import tempfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from ub_grader import load_spec


class _Handler(SimpleHTTPRequestHandler):
    pass


def _serve_content(content: str, port: int):
    tmpdir = tempfile.TemporaryDirectory()
    path = pathlib.Path(tmpdir.name) / "spec.json"
    path.write_text(content, encoding="utf-8")

    class LocalHandler(_Handler):
        def do_GET(self):  # noqa: N802
            if self.path == "/spec.json":
                data = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)

    httpd = HTTPServer(("127.0.0.1", port), LocalHandler)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    return tmpdir, httpd, th


def test_load_spec_basic():
    spec_dict = {
        "version": "1.0.0",
        "assignment_id": "p1",
        "tests": [
            {
                "id": "t1",
                "input": {"args": [1, 2], "kwargs": {}},
                "expected": 3,
                "weight": 1,
            }
        ],
        "scoring": {
            "mode": "weighted_sum_with_penalties",
            "rounding": 2,
            "penalties": {},
            "max_score": 10,
        },
        "integrity": {},
    }
    content = json.dumps(spec_dict)
    tmp, httpd, _th = _serve_content(content, 8765)
    try:
        spec = load_spec("http://127.0.0.1:8765/spec.json")
        assert spec.assignment_id == "p1"
        assert len(spec.tests) == 1
    finally:
        httpd.shutdown()
        tmp.cleanup()
