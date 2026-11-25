# -*- coding: utf-8 -*-
"""Daily price refresh, designed to run inside GitHub Actions (no server).

Usage:
    python3 scripts/fetch_daily.py
    python3 scripts/fetch_daily.py --root .

What it does, in order:
  1. Loads data/seed-prices.json (the 2026-11-25 snapshot, 43 parts x 3
     platforms = 129 rows) as the fallback base.
  2. Loads public/prices-manual.json (hand-entered prices, mainly Xianyu)
     and lets manual rows override the matching snapshot row.
  3. Tries the JD Union and PDD Duoduo Jinbao official APIs ONLY if the
     corresponding secrets are set as environment variables
     (JD_APP_KEY / JD_APP_SECRET / JD_UNION_ID,
      PDD_CLIENT_ID / PDD_CLIENT_SECRET). The official adapters in the
     main backend are still stubbed (the signed API call is not finished),
     so today this step always reports "skipped: not configured" or
     "skipped: adapter not implemented" and NEVER invents a price.
     When the adapters are completed later, this is the one place to wire
     them in -- the contract is: return a price only when the platform
     actually returned one, otherwise return nothing.
  4. Writes public/prices.json (mode = "live" only if at least one
     official_api row was returned, otherwise "snapshot") and
     public/fetch-log.json (per-platform updated / skipped / failed counts,
     run time, no secrets).

Exit code is always 0 on a clean run, even when everything is skipped:
a skipped platform is an expected state, not a failure. It only exits
non-zero on a real error (missing seed file, corrupt JSON, unwritable out).
"""
from __future__ import annotations

import argparse
import json
import os
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


def _now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def try_official_api(platform: str) -> tuple[str, str]:
    """Return (status, detail). Never returns a price here.

    JD: needs JD_APP_KEY + JD_APP_SECRET + JD_UNION_ID.
    PDD: needs PDD_CLIENT_ID + PDD_CLIENT_SECRET.
    Xianyu: no public API at all -- always manual.
    """
    if platform == "xianyu":
        return "skipped", "闲鱼没有公开 API，价格靠手动录入（public/prices-manual.json）"
    if platform == "jd":
        if not (os.environ.get("JD_APP_KEY") and os.environ.get("JD_APP_SECRET")
                and os.environ.get("JD_UNION_ID")):
            return "skipped", "未配置 GitHub Secrets：JD_APP_KEY / JD_APP_SECRET / JD_UNION_ID"
        return "skipped", "已配 key，但京东联盟适配器尚未接通（jd.union.open.goods.query 签名调用待补全），未返回价格"
    if platform == "pdd":
        if not (os.environ.get("PDD_CLIENT_ID") and os.environ.get("PDD_CLIENT_SECRET")):
            return "skipped", "未配置 GitHub Secrets：PDD_CLIENT_ID / PDD_CLIENT_SECRET"
        return "skipped", "已配 key，但多多进宝适配器尚未接通，未返回价格"
    return "failed", f"未知平台 {platform}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Daily price refresh for GitHub Actions")
    ap.add_argument("--root", default=str(ROOT), help="github-free folder root")
    args = ap.parse_args()
    root = Path(args.root)
    seed_path = root / "data" / "seed-prices.json"
    if not seed_path.exists():
        print(f"ERROR: seed file missing: {seed_path}", file=sys.stderr)
        print("Run locally first: python3 scripts/export_prices.py", file=sys.stderr)
        return 2
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    prices = list(seed["prices"])
    index = {(p["part_id"], p["platform"]): i for i, p in enumerate(prices)}

    # 1. Manual overrides (mainly Xianyu, entered by hand / via manual_import.py)
    manual = _load_json(root / "public" / "prices-manual.json", [])
    manual_updated = 0
    for m in manual:
        key = (m["part_id"], m["platform"])
        if key not in index:
            print(f"WARNING: manual row ignored, unknown part/platform: {key}",
                  file=sys.stderr)
            continue
        row = dict(prices[index[key]])
        row.update({
            "price_cny": int(m["price_cny"]),
            "fetched_at": m.get("fetched_at") or _now(),
            "source": "manual_import",
            "url": m.get("url"),
            "is_verified": True,
        })
        prices[index[key]] = row
        manual_updated += 1

    # 2. Official APIs (today: always skipped, by design -- see docstring)
    per_platform: dict[str, dict] = {}
    live_rows = 0
    for platform in PLATFORMS:
        status, detail = try_official_api(platform)
        per_platform[platform] = {
            "status": status, "updated": 0, "skipped": 43 if status == "skipped" else 0,
            "failed": 0, "detail": detail,
        }
        print(f"[{platform}] {status}: {detail}")

    mode = "live" if live_rows > 0 else "snapshot"
    now = _now()
    public = {
        "generated_at": now,
        "mode": mode,
        "snapshot_date": "2026-11-25",
        "note": ("2026-11-25 快照示例价，不是实时价。"
                 if mode == "snapshot" else
                 "含官方 API 返回的实时价，见每条 source 字段。"),
        "parts_count": len(seed["parts"]),
        "prices_count": len(prices),
        "manual_updated": manual_updated,
        "packages": seed["packages"],
        "prices": prices,
    }
    out_dir = root / "public"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prices.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log = {
        "run_at": now,
        "mode": mode,
        "parts_count": len(seed["parts"]),
        "prices_count": len(prices),
        "manual_updated": manual_updated,
        "per_platform": per_platform,
        "note": "skipped 不是故障：没配 key / 适配器未接通时，平台会明确跳过，绝不编造价格。",
    }
    (out_dir / "fetch-log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"mode={mode}, prices={len(prices)}, manual_updated={manual_updated}")
    print(f"wrote {out_dir / 'prices.json'} and {out_dir / 'fetch-log.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
