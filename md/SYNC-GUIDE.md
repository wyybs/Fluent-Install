# Fluent-Install 同步执行契约

> 跟随基线：`upstream/main`（起始 2026-11-01，原因：初始跟随）

## 0. 触发

- 「巡检 / 上游有没有更新 / 读下这份文档」= 直接跑 skill §2 六步巡检，跑完再汇报。
- 「上游没了 / 分支没了」= 跑 §4 建新基线。

## 1. 分支

| 分支 | 角色 |
|---|---|
| `local` | 二开活分支，只向前提交，不 merge、不 rebase |
| `main` | fork 上的 ff 镜像，跟 `origin/main`（`wyybs/Fluent-Install`）一致，只作参照 |
| `upstream/main` | 只读对齐基线（`zhouchentao666/Fluent-Install`） |

- `upstream` 远端 push URL 已设为 `no_push`，防止误推上游。
- 本仓库 git 已绑定 7890 代理（`http.proxy` / `https.proxy`），上游 fetch 直连即可。

## 2. 能力基线（判收窄的度量尺）

| 能力 | 基线值 | 怎么量 |
|---|---|---|
| 后端函数数 | 见 `.fork-sync-baseline` | `bash ~/.workbuddy/skills/wyybs-fork-upstream-sync/scripts/inspect.sh .` 第 6 段 |
| 修改器后端函数数 | 同上 | 同上 |
| 语言包数（`about_text`） | 7（中/英/法/俄/德/日/…） | 同上 |
| 封面加载调用点（CoverLoader） | local=4 / upstream=0 | 同上；**此项本地必然高于上游，属本项目新增能力，不是收窄** |

- 硬编码上游地址检查：`git grep -n "zhouchentao666" -- '*.py' '*.json'`。命中只可能出现在 `app/fluent_app.py` 的多语言 `about_text` / `thanks_text` 署名里，属于正常归属；如果出现在网络请求或路径拼接里，必须改。

## 3. 装机与自检

- 装机：无。源码直接在仓库根用 `.venv` 运行，**改完只要重启程序就生效**。
- 启动：`D:\Program Files\FluentInstall\.venv\Scripts\pythonw.exe D:\Program Files\FluentInstall\main.py`
- 开始菜单入口：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\FluentInstall-源码版.lnk`（pywin32 生成，指向上面那条命令）
- 自检：`./.venv/Scripts/python.exe -m py_compile main.py app/fluent_app.py backend/cai_backend.py backend/trainer_backend.py`
- 界面改动要真跑一遍：`python main.py` 起窗口，搜一个游戏确认封面/按钮正常，再 `git status` 看有没有误提交 `config/`、`logs/`。

## 4. 禁区

照抄 skill §9，另加本项目三条：

1. 不许改 `config/config.json` 的语义当同步手段——它是运行时状态文件（已 gitignore）。
2. 不许把上游 release 里的外链（迅雷网盘补丁、TG/Q 群）搬进代码或文档，署名区除外。
3. 不许改 `Resource.json` 的上游资源地址为本地路径——那是远程拉取的清单/补丁库索引。
4. 本仓库无 LICENSE 文件，二开对外发布前先把许可证补齐。

## 5. 记录去哪看

历史（每次巡检结论、移植明细、已判定不跟项、事故复盘）全部在 `md/SYNC-LOG.md`。
