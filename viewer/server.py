#!/usr/bin/env python3
"""3D Model Review ローカルサーバー（ワークスペース限定配信）。"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

VIEWER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(VIEWER_DIR))
import workspace  # noqa: E402


def _resolve_ws(source_dir: str | None = None):
    env = source_dir or os.environ.get("MODEL_REVIEW_WS")
    if env:
        return workspace.resolve_workspace(env)
    active = workspace.read_active()
    if active:
        root = workspace.WORKSPACES_ROOT / active
        meta = {}
        try:
            meta = json.loads((root / "meta.json").read_text())
        except Exception:
            pass
        return workspace.resolve_workspace(meta.get("source_dir") or str(Path.cwd()))
    return workspace.resolve_workspace(None)


def make_handler(models_dir: Path, ws):
    models_dir = Path(models_dir).resolve()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(VIEWER_DIR), **k)

        def log_message(self, *a):
            pass

        def _json(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def _safe_model(self, rel: str) -> Path | None:
            try:
                target = (models_dir / rel.lstrip("/")).resolve()
                target.relative_to(models_dir)
                return target
            except (ValueError, OSError):
                return None

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/api/models":
                items = []
                if models_dir.is_dir():
                    for p in models_dir.glob("*.stl"):
                        items.append({"name": p.name, "mtime": p.stat().st_mtime})
                items.sort(key=lambda x: x["mtime"], reverse=True)
                return self._json(200, {"ok": True, "models": items})
            if path == "/api/workspace":
                return self._json(200, {
                    "ok": True,
                    "title": ws.title,
                    "source_dir": ws.source_dir,
                    "model_count": len(list(models_dir.glob("*.stl"))),
                })
            if path.startswith("/models/"):
                t = self._safe_model(path[len("/models/"):])
                if t is None:
                    return self._json(400, {"ok": False, "error": "bad path"})
                if not t.exists():
                    return self._json(404, {"ok": False, "error": "not found"})
                st = t.stat()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(st.st_size))
                self.send_header("Last-Modified", self.date_time_string(st.st_mtime))
                self.end_headers()
                self.wfile.write(t.read_bytes())
                return
            return super().do_GET()

        def do_HEAD(self):
            # ビューアは STL の Last-Modified を HEAD で取りに来る。
            # SimpleHTTPRequestHandler の既定実装はビューアディレクトリしか見ないので、
            # /models/ 配下は GET と同じ解決をして 404 にならないようにする。
            path = self.path.split("?")[0]
            if path.startswith("/models/"):
                t = self._safe_model(path[len("/models/"):])
                if t is None or not t.exists():
                    self.send_response(404 if t is not None else 400)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                st = t.stat()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(st.st_size))
                self.send_header("Last-Modified", self.date_time_string(st.st_mtime))
                self.end_headers()
                return
            return super().do_HEAD()

        def _cross_site(self) -> bool:
            """他サイトからの書き込み（CSRF）かどうか。

            ビューア自身のリクエストは Origin が付かないか、自分の origin になる。
            別サイトのページから投げられた場合は必ず別の Origin が付く。
            Content-Type も application/json に限定しておくと、プリフライトが
            必要になる分だけ単純リクエストでの偽装が効かなくなる。
            """
            origin = self.headers.get("Origin")
            if origin:
                host = self.headers.get("Host", "")
                if origin not in (f"http://{host}", f"https://{host}"):
                    return True
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            return ctype != "application/json"

        def do_POST(self):
            if self.path == "/save_picks":
                if self._cross_site():
                    return self._json(403, {"ok": False, "error": "cross-site request rejected"})
                raw_len = self.headers.get("Content-Length", "0")
                try:
                    n = int(raw_len)
                except (TypeError, ValueError):
                    return self._json(400, {"ok": False, "error": "bad content-length"})
                if not (0 <= n <= 8_000_000):
                    return self._json(413, {"ok": False, "error": "bad or too large"})
                try:
                    body = self.rfile.read(n)
                    data = json.loads(body)
                    ws.annotations_path.write_bytes(body)
                    ts = re.sub(r"[^0-9T:.\-]", "", str(data.get("timestamp", ""))).replace(":", "-")[:19]
                    fname = re.sub(r"[^A-Za-z0-9._\-]", "_", str(data.get("file", "model"))).replace(".stl", "")
                    hist = (ws.history_dir / f"{fname}_{ts}.json").resolve()
                    hist.relative_to(ws.history_dir.resolve())  # raises ValueError if escaped
                    hist.write_bytes(body)
                    return self._json(200, {
                        "ok": True,
                        "path": str(ws.annotations_path),
                        "annotation_count": len(data.get("annotations", [])),
                    })
                except Exception as e:
                    return self._json(500, {"ok": False, "error": str(e)})
            return self._json(404, {"ok": False, "error": "not found"})

    return Handler


def build_server(start_port: int, handler) -> HTTPServer:
    if start_port == 0:
        return HTTPServer(("127.0.0.1", 0), handler)
    last = None
    for port in range(start_port, start_port + 25):
        try:
            return HTTPServer(("127.0.0.1", port), handler)
        except OSError as e:
            last = e
    raise RuntimeError(f"no free port {start_port}..+25: {last}")


def main():
    ap = argparse.ArgumentParser(description="3D Model Review ローカルサーバー")
    ap.add_argument("--workspace", "-w", help="表示対象の作業ディレクトリ（既定: $MODEL_REVIEW_WS または CWD）")
    ap.add_argument("--models", "-m", help="STL を直接読むディレクトリ（既定: ワークスペースの models/）")
    ap.add_argument("--port", "-p", type=int, default=8765,
                    help="開始ポート。埋まっていたら +25 まで空きを探す。0 でOS任せ（既定: 8765）")
    args = ap.parse_args()

    ws = _resolve_ws(args.workspace)
    models_dir = Path(args.models).expanduser().resolve() if args.models else ws.models_dir
    handler = make_handler(models_dir, ws)
    httpd = build_server(args.port, handler)
    port = httpd.server_address[1]
    try:
        workspace.PORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        workspace.PORT_FILE.write_text(str(port))
    except Exception:
        pass
    print("🚀 3D Model Review")
    print(f"📁 workspace: {ws.title}  ({ws.source_dir})")
    print(f"📂 models:    {models_dir}")
    print(f"📝 notes:     {ws.annotations_path}")
    print(f"🌐 http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
