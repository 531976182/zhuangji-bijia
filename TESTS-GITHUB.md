# 免费 GitHub 版 · 测试记录

测试时间：2026-11-25 22:35 CST（北京时间）
测试环境：本地 Python 3.12，源数据为后端 `prices.db`（43 个配件、129 条价、4 档套餐）

## 1. 导出快照（export_prices.py）

命令：
```bash
python3 scripts/export_prices.py
```

结果：通过。
- `parts: 43, prices: 129, packages: 4`
- 写出 `data/seed-prices.json`（60 KB）和 `public/prices.json`（48 KB）。
- `public/prices.json` 校验：`mode=snapshot`，`parts_count=43`，`prices_count=129`；按 `(source, platform)` 计数：`snapshot × jd = 43`、`snapshot × pdd = 43`、`snapshot × xianyu = 43`，没有一条被标成实时价。

## 2. 每日刷新（fetch_daily.py，无 key 状态）

命令：
```bash
python3 scripts/fetch_daily.py
```

结果：通过，退出码 0。
- xianyu：`skipped` —— 闲鱼没有公开 API，靠手动录入。
- pdd：`skipped` —— 未配置 GitHub Secrets `PDD_CLIENT_ID / PDD_CLIENT_SECRET`。
- jd：`skipped` —— 未配置 GitHub Secrets `JD_APP_KEY / JD_APP_SECRET / JD_UNION_ID`。
- 写出 `public/prices.json`（mode 仍为 snapshot）和 `public/fetch-log.json`。
- **没有编造任何价格**：三个平台各 43 条 skipped，0 条 updated。

## 3. 手动录入（manual_import.py，测试后已还原）

命令：
```bash
python3 scripts/manual_import.py --part-id i13490f --platform xianyu --price 628 --note "散片，店保1年（测试）"
python3 scripts/fetch_daily.py
```

结果：通过。
- `public/prices-manual.json` 写入 1 条；重新合并后，`i13490f / xianyu` 变为 ¥628，`source=manual_import`，`is_verified=true`，同配件的京东 / 拼多多仍为快照价。
- 测试后已还原：`public/prices-manual.json` 清空回 `[]`，重新跑 `fetch_daily.py`，`public/prices.json` 恢复为 129 条全 snapshot，无测试价格残留。

## 4. 工作流 YAML 校验

命令：
```bash
python3 -c "import yaml; print(yaml.safe_load(open('.github/workflows/daily-prices.yml'))['name'])"
```

结果：通过，输出 `Daily prices`。
- 定时为 `cron: "0 0 * * *"`（UTC 00:00 = 北京时间 08:00），另有 `workflow_dispatch` 可手动触发。
- 权限只有 `contents: write`，提交时只 `git add public/prices.json public/fetch-log.json`，无变化时不产生空提交。

## 5. 代码与 JSON 校验

- `python3 -m py_compile scripts/export_prices.py scripts/fetch_daily.py scripts/manual_import.py`：通过。
- `public/prices.json`、`data/seed-prices.json`、`public/fetch-log.json`、`public/prices-manual.json` 全部是合法 JSON。
- 密钥扫描：仓库文件里没有任何真实 token、密码、cookie 或 API key；密钥只以环境变量名（`JD_APP_KEY` 等）和 `${{ secrets.XXX }}` 的形式出现在代码和工作流里。

## 未测 / 已知限制

- 没有在真实 GitHub 仓库里跑过 Actions（需要用户自己建仓库、传文件、开 Pages 和 Actions 才能验证）；本地跑的是同一个脚本和同一份 YAML。
- 京东 / 拼多多官方接口调用仍是占位：即使配了 key，当前适配器也会明确记为 skipped，不会返回实时价，需按官方最新文档补全签名调用（见 README-GITHUB.md）。
- 前端页面尚未改成读 `prices.json`（按任务要求，本次不改 artifact，改法已写在 README-GITHUB.md 里）。
