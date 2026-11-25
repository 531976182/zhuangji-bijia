# 装机比价网站 · 免费 GitHub 版（不用买云服务器）

> **一句话：** 网站和每天定时刷新价格，都用 GitHub 免费的东西跑 —— GitHub Pages 放网站，GitHub Actions 每天早上 8 点跑一次刷新价格。**0 元，不用买云服务器。**

## 这个文件夹里有什么

| 文件 | 用途 |
|---|---|
| `.github/workflows/daily-prices.yml` | 每天 08:00（北京时间）自动跑一次刷新价格；也可以在 Actions 页面手动点一下立即跑 |
| `scripts/export_prices.py` | 本地用：把后端数据库里的价导出成静态文件（只在第一次准备时跑一次） |
| `scripts/fetch_daily.py` | 每天跑的那个脚本：快照价打底 + 手动价覆盖 + 有 key 才调官方 API，没 key 就明确跳过，绝不编价 |
| `scripts/manual_import.py` | 手动录一个闲鱼价的小工具（见下面第 6 步） |
| `data/seed-prices.json` | 2026-11-25 快照价种子：43 个配件 × 3 个平台 = 129 条，source 都是 `snapshot` |
| `public/prices.json` | **前端真正读的那个文件**：43 个配件的价格 + 4 档套餐，每条都带平台、价格、抓取时间、来源、是否核实 |
| `public/prices-manual.json` | 手动录的价格（主要是闲鱼），现在是空的 `[]` |
| `public/fetch-log.json` | 最近一次刷新跑完的记录：每个平台更新 / 跳过 / 失败了几条 |

## 部署 5 步（都要你自己动手，我替你建不了 GitHub 账号和仓库）

### 第 1 步：注册 GitHub 账号（已有就跳过）
打开 https://github.com ，注册一个账号，记好用户名和密码。**不要把密码发在聊天里。**

### 第 2 步：新建一个仓库（公开仓库才能免费无限用 Pages）
1. 登录后点右上角 `+` → `New repository`。
2. Repository name 填一个名字，比如 `zhuangji-bijia`。
3. 选 **Public**（公开）。选 Private 也能用，但免费额度一样，公开更简单。
4. 勾上 `Add a README file`，点 `Create repository`。

### 第 3 步：把这个文件夹里的文件传上去
两种办法，任选一种：

**办法 A（不用命令行，在网页上点）：**
1. 在仓库页面点 `Add file` → `Upload files`。
2. 把这个文件夹里的全部文件拖进去：`.github/`、`scripts/`、`data/`、`public/` 都要传。注意 `.github` 是隐藏文件夹，拖的时候别漏了。
3. 点 `Commit changes`。

**办法 B（会用 git 的话）：**
```bash
git clone https://github.com/<你的用户名>/zhuangji-bijia.git
cd zhuangji-bijia
# 把本文件夹里的所有文件拷进去
git add .
git commit -m "feat: free GitHub version"
git push
```

### 第 4 步：打开 GitHub Pages（网站就上线了）
1. 仓库页面点 `Settings` → 左边 `Pages`。
2. `Build and deployment` → `Source` 选 `Deploy from a branch`。
3. Branch 选 `main`，文件夹选 `/ (root)`，点 `Save`。
4. 等 1–2 分钟，页面上方会出现你的网址，大概是这样：
   `https://<你的用户名>.github.io/zhuangji-bijia/`
5. 打开 `https://<你的用户名>.github.io/zhuangji-bijia/prices.json`，能看到 129 条价，就说明成功了。

> 注意：这个网址现在只能看到 `prices.json` 这个价格文件。完整的比价网站页面（小黑球装机那个首页）目前还是单独的静态页面文件，等你确认后，我再帮你把那个页面也放进这个仓库，变成同一个网址。

### 第 5 步：打开 Actions（每天自动刷新才生效）
1. 仓库页面点 `Actions` 标签。
2. 如果提示要启用，点 `I understand my workflows, go ahead and enable them`。
3. 左边能看到 `Daily prices`，点进去，点 `Run workflow` 可以立即手动跑一次。
4. 以后每天北京时间 08:00，它会自动跑一次：没 key 就跳过并写日志，有手动价就覆盖，有 key 才调官方接口。

## 第 6 步（以后再做）：申请京东 / 拼多多 key，最后才办

现在不用办。等你想让京东和拼多多的价变实时，再做这两件事：

1. 去 https://union.jd.com 申请京东联盟，拿到 `app_key / app_secret`；去 https://jinbao.pinduoduo.com 申请多多进宝，拿到 `client_id / client_secret`。
2. 在仓库 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`，逐个添加，名字必须完全一致：
   - `JD_APP_KEY`、`JD_APP_SECRET`、`JD_UNION_ID`
   - `PDD_CLIENT_ID`、`PDD_CLIENT_SECRET`
3. **密钥只填在 Secrets 里，绝不写进代码、绝不发在聊天里。** 代码里只读环境变量，日志里也不会打印密钥。

> 还要说明一点：京东 / 拼多多官方接口的签名调用在后端里还是占位（stub），只写了签名函数，没接通真正的 `jd.union.open.goods.query` 调用。配好 key 之后，还要按京东 / 拼多多最新的官方文档把那一次调用补全，才能真的返回实时价。在那之前，定时任务会明确记为 `skipped`，不会给你编一个假价。

## 闲鱼价怎么更新（没有公开接口，只能手动）

闲鱼没有公开 API，所以闲鱼价永远靠手动录：

```bash
# 你在闲鱼 App 里看到一个价，就录一条
python3 scripts/manual_import.py --part-id i13490f --platform xianyu --price 628 --note "散片，店保1年"
python3 scripts/fetch_daily.py   # 合并进 public/prices.json
git add public/prices.json public/prices-manual.json
git commit -m "chore: manual xianyu price"
git push
```

也可以直接在 GitHub 网页上改 `public/prices-manual.json`，格式照着下面抄：

```json
[
  {
    "part_id": "i13490f",
    "platform": "xianyu",
    "price_cny": 628,
    "fetched_at": "2026-11-25T22:00:00+08:00",
    "source": "manual_import",
    "url": null,
    "note": "散片，店保1年"
  }
]
```

`part_id` 必须是 43 个配件里的一个（在 `data/seed-prices.json` 里能查到，比如 `i13490f`、`i12400f`、`r7500f`、`4060`），价格必须是大于 0 的整数。

## 前端要改的一行（不用你改，告诉我一声就行）

现在的静态页面里价格是写死的 2026-11-25 快照。接上这个免费版，只需要改一处：

```js
// 页面加载时先去读 prices.json，读到就用它，读不到就用页面里自带的快照价
fetch('./prices.json').then(r => r.json()).then(data => {
  // 用 data.prices 覆盖页面里的快照价，并按 data.mode 显示“快照价”还是“实时价”
});
```

等你仓库建好、把网址发我，我就帮你把前端改成这样，并把页面文件也放进仓库，变成同一个网址。

## 免费额度与限制（实话实说）

| 项目 | 免费额度 | 这个网站用多少 |
|---|---|---|
| GitHub Pages | 公开仓库免费，无限流量（合理使用） | 一个静态页面 + 一个 `prices.json`，够用 |
| GitHub Actions | 公开仓库免费；私有仓库每月 2000 分钟 | 每天跑 1 次，每次不到 1 分钟，一个月约 30 分钟 |
| 定时任务 | 每天 08:00 跑一次 | GitHub 的定时任务可能晚几分钟到几十分钟，正常 |

**没有的东西（和买服务器的版本比）：**
- **没有 `/admin` 后台界面了。** 后端那个 `/admin` 是要服务器一直开着才能用的；免费版没有服务器，所以改价 = 改 `prices-manual.json` 再 push，或者在本地跑 `manual_import.py` 再 push。能改价，只是没那么顺手。
- **没有“点一下立刻刷新”的按钮。** 刷新靠每天定时任务，或者在 Actions 页面手动点 `Run workflow`。
- **闲鱼没有自动价。** 永远手动录。
- **京东 / 拼多多现在也不是实时价。** 没 key 时是快照价，有 key 还要再补一次官方接口调用（见上面）。

## 安全提醒

- 仓库里**没有任何真实密码、cookie、API key**。`.env` 文件不要传上来。
- 密钥只放在 GitHub Secrets 里，不要写进代码、不要发聊天、不要截图发群里。
- 定时任务提交回仓库时用的只是 GitHub Actions 自带的机器人身份，只能改 `public/prices.json` 和 `public/fetch-log.json` 两个文件。
