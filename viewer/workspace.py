"""3D Model Review のワークスペース・スコープ決定（唯一の真実）。

作業ディレクトリ → 決定的 slug → ~/.model-review/workspaces/<slug>/
サーバーもモデル投入もこのモジュールだけを使う。

環境変数:
  MODEL_REVIEW_HOME  データ置き場のルート（既定: ~/.model-review）
  MODEL_REVIEW_WS    表示対象の作業ディレクトリ（既定: カレントディレクトリ）
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

HOME_DIR = Path(os.environ.get("MODEL_REVIEW_HOME") or (Path.home() / ".model-review")).expanduser()
WORKSPACES_ROOT = HOME_DIR / "workspaces"
ACTIVE_FILE = WORKSPACES_ROOT / ".active"
PORT_FILE = HOME_DIR / "port"


def _safe(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-") or "ws"


def slug_for(source_dir: str) -> str:
    p = Path(source_dir).expanduser().resolve()
    base = _safe(p.name)[:32]
    digest = hashlib.sha1(str(p).encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}"


@dataclass(frozen=True)
class WorkspacePaths:
    slug: str
    root: Path
    models_dir: Path
    annotations_path: Path
    history_dir: Path
    meta_path: Path
    title: str
    source_dir: str


def resolve_workspace(source_dir: str | None = None) -> WorkspacePaths:
    src = Path(source_dir).expanduser().resolve() if source_dir else Path.cwd()
    slug = slug_for(str(src))
    root = WORKSPACES_ROOT / slug
    models_dir = root / "models"
    history_dir = root / "annotations_history"
    models_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)
    meta_path = root / "meta.json"
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            meta = {}
    meta.setdefault("created_at", now)
    meta["source_dir"] = str(src)
    meta["title"] = src.name
    meta["last_opened_at"] = now
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return WorkspacePaths(
        slug=slug,
        root=root,
        models_dir=models_dir,
        annotations_path=root / "annotations.json",
        history_dir=history_dir,
        meta_path=meta_path,
        title=src.name,
        source_dir=str(src),
    )


def set_active(slug: str) -> None:
    WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(slug.strip())


def read_active() -> str | None:
    try:
        s = ACTIVE_FILE.read_text().strip()
        return s or None
    except FileNotFoundError:
        return None
