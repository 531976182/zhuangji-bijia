# -*- coding: utf-8 -*-
"""Add / update one hand-entered price (mainly Xianyu) in public/prices-manual.json.

Xianyu has no public API, so its prices are entered by hand: you saw the
price in the Xianyu App, you type it here. Nothing is scraped, nothing
is invented.

Usage:
    python3 scripts/manual_import.py --part-id i13490f --platform xianyu --price 628
    python3 scripts/manual_import.py --part-id i12400f --platform xianyu --price 600 --url https://example.com/listing --note "散片，店保1年"

Validation:
  - part_id must exist in data/seed-prices.json (43 parts)
  - platform must be one of: xianyu | pdd | jd
  - price must be a positive integer (yuan)
After running, regenerate the public file so the change shows up:
    python3 scripts/fetch_daily.py
Then commit + push public/prices.json and public/prices-manual.json.
No secrets are read or written here.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Shanghai")
except Exception:  # pragma: no cover
    TZ = timezone.utc

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = ("xianyu", "pdd", "jd")


def main() -> int:
    ap = argparse.ArgumentParser(description="Manually add a price (mainly Xianyu)")
    ap.add_argument("--part-id", required=True, help="e.g. i13490f, i12400f, r7500f")
    ap.add_argument("--platform", default="xianyu", choices=PLATFORMS)
    ap.add_argument("--price", required=True, type=int, help="price in yuan, > 0")
    ap.add_argument("--url", default=None, help="listing URL, optional")
    ap.add_argument("--note", default=None, help="condition / warranty note, optional")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()

    if args.price <= 0:
        print("ERROR: --price 必须是大于 0 的整数（元）", file=sys.stderr)
        return 2
    root = Path(args.root)
    seed_path = root / "data" / "seed-prices.json"
    if not seed_path.exists():
        print(f"ERROR: seed file missing: {seed_path}", file=sys.stderr)
        print("Run locally first: python3 scripts/export_prices.py", file=sys.stderr)
        return 2
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    known = {p["id"] for p in seed["parts"]}
    if args.part_id not in known:
        print(f"ERROR: 未知配件 {args.part_id}，可选：{', '.join(sorted(known))}",
              file=sys.stderr)
        return 2

    manual_path = root / "public" / "prices-manual.json"
    manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else []
    row = {
        "part_id": args.part_id,
        "platform": args.platform,
        "price_cny": args.price,
        "fetched_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "source": "manual_import",
        "url": args.url,
        "note": args.note,
    }
    replaced = False
    for i, m in enumerate(manual):
        if m["part_id"] == args.part_id and m["platform"] == args.platform:
            manual[i] = row
            replaced = True
    if not replaced:
        manual.append(row)
    manual_path.parent.mkdir(parents=True, exist_ok=True)
    manual_path.write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"{'updated' if replaced else 'added'}: {args.part_id} / {args.platform} = ¥{args.price}")
    print(f"wrote {manual_path} ({len(manual)} manual rows)")
    print("Next: python3 scripts/fetch_daily.py  # 合并进 public/prices.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
