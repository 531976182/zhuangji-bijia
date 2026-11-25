# -*- coding: utf-8 -*-
"""Export backend SQLite prices to the GitHub-free static files.

Usage (run locally, once, before pushing to GitHub):
    python3 scripts/export_prices.py
    python3 scripts/export_prices.py --db /path/to/prices.db --out-dir .

Reads the backend DB (../backend/prices.db by default):
  parts (43) x prices (129 rows, 3 platforms each)
and writes:
  data/seed-prices.json   - the snapshot rows, source="snapshot" preserved
  public/prices.json      - the file the frontend fetches, with metadata

Every row keeps: part_id, name, category, platform, price_cny,
fetched_at, source, url, is_verified. Snapshot rows are NEVER relabelled
as live prices. No secrets are read or written here.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Shanghai")
except Exception:  # pragma: no cover
    TZ = timezone.utc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT.parent / "backend" / "prices.db"


def load_from_db(db_path: Path) -> dict:
    if not db_path.exists():
        raise FileNotFoundError(f"backend DB not found: {db_path}")
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    parts = {r["id"]: dict(r) for r in db.execute("SELECT * FROM parts")}
    rows = db.execute(
        "SELECT part_id, platform, price_cny, fetched_at, source, url, "
        "is_verified FROM prices ORDER BY part_id, platform"
    ).fetchall()
    prices = []
    for r in rows:
        p = parts.get(r["part_id"], {})
        prices.append({
            "part_id": r["part_id"],
            "name": p.get("name", r["part_id"]),
            "category": p.get("category", ""),
            "category_name": p.get("category_name", ""),
            "spec": p.get("spec", ""),
            "platform": r["platform"],
            "price_cny": int(r["price_cny"]),
            "fetched_at": r["fetched_at"],
            "source": r["source"],
            "url": r["url"],
            "is_verified": bool(r["is_verified"]),
        })
    packages = []
    for r in db.execute("SELECT id, label, name, description, fps_note, sel_json FROM packages"):
        packages.append({
            "id": r["id"], "label": r["label"], "name": r["name"],
            "description": r["description"], "fps_note": r["fps_note"],
            "sel": json.loads(r["sel_json"]),
        })
    return {"parts": list(parts.values()), "prices": prices, "packages": packages}


def build_public(data: dict) -> dict:
    now = datetime.now(TZ).isoformat(timespec="seconds")
    return {
        "generated_at": now,
        "mode": "snapshot",
        "snapshot_date": "2026-11-25",
        "note": "2026-11-25 快照示例价，不是实时价。实时价需在 GitHub Secrets 里配好京东联盟 / 多多进宝 key 后由每日定时任务刷新；闲鱼价靠手动录入。",
        "parts_count": len(data["parts"]),
        "prices_count": len(data["prices"]),
        "packages": data["packages"],
        "prices": data["prices"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Export backend DB prices to static JSON")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="path to backend prices.db")
    ap.add_argument("--out-dir", default=str(ROOT), help="github-free folder root")
    args = ap.parse_args()
    out = Path(args.out_dir)
    data = load_from_db(Path(args.db))
    if len(data["prices"]) != 129:
        print(f"WARNING: expected 129 price rows, got {len(data['prices'])}",
              file=sys.stderr)
    if len(data["parts"]) != 43:
        print(f"WARNING: expected 43 parts, got {len(data['parts'])}",
              file=sys.stderr)
    seed_path = out / "data" / "seed-prices.json"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    public_path = out / "public" / "prices.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(
        json.dumps(build_public(data), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"parts: {len(data['parts'])}, prices: {len(data['prices'])}, "
          f"packages: {len(data['packages'])}")
    print(f"wrote {seed_path}")
    print(f"wrote {public_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
