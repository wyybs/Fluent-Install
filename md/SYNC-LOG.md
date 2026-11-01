# Fluent-Install 同步日志（append-only，只加不改）

## 已判定不跟（提案前先看这里，避免重复提）

| 上游提交 / 范围 | 内容 | 为什么不跟 |
|---|---|---|
| （暂无） | | |

## 时间线（新→旧）

### 2026-11-01 20:50 新增单实例锁

- 基线：`local` @ e536a61 / `upstream/main` @ d8ccb75
- 结论：原版没有单实例机制，重复点击开始菜单会起第二个进程、两个实例同时写 `config/config.json`。改为「已有实例就把它的窗口拉到前台，本次启动直接退出」。
- 变更：
  - 新增 `app/single_instance.py`：`SingleInstanceGuard`（`QLocalServer` / `QLocalSocket`，Windows 上是命名管道 `FluentInstall-SingleInstance-v1`）+ `activate_window()`（`raise_` / `activateWindow` + Win32 `ShowWindow(SW_RESTORE)` / `SetForegroundWindow` 兜底）
  - `main.py`：`QApplication` 之后、`MainWindow` 之前判定；`sys.exit(0)` 而不是继续
  - `app/fluent_app.py`：同样的接线做在其自己的 `main()` 里，保证 `python app/fluent_app.py` 也受控
  - 自我重启兜底：`fluent_app.py` 里「换语言 → `os.execl` 重开自己」那段先设 `FLUENTINSTALL_SELF_RESTART=1`，新进程走「等旧进程释放管道、重试 5 秒」分支，避免被自己的锁拦死
- 自检：`py_compile` 五个入口文件通过；实测两次启动 —— 第二个实例打印「已有实例在运行，已唤起它的窗口，本次启动退出」退出码 0，第一个实例 stderr 出现「收到重复启动请求，唤起已有窗口」，进程数不变；模拟重启（带 `FLUENTINSTALL_SELF_RESTART=1`）不被拦截
- 观察记录：本机 venv 的 `python.exe` 是 241KB 启动器，**每次都伴生两个同命令行 python.exe**（启动器 + 真解释器），之前误判成「用户开了两个实例」；判断多开要看内存占用的那个
- 回滚点：`e536a61`（上一个 local 提交）

### 2026-11-01 20:35 首次接管：建立 local 分支

- 基线：`local` @ 3bf6e61 / `upstream/main` @ d8ccb75（源码版 3.1.6，Python + PyQt6）
- 结论：仓库此前只有 `main` 一条跟踪 `origin/main` 的分支，工作区有一处未提交改动（`app/fluent_app.py` 封面加载器）。按 skill 建立 `local` 作为二开活分支，把改动提交进去，`main` 保留为 fork 镜像。
- 变更：
  - 新增远端 `upstream` → `zhouchentao666/Fluent-Install`，push URL 置为 `no_push`
  - `local` 分支从 `main`（= `upstream/main`）拉出
  - `local: 统一封面加载器，修复新游戏封面 404 空白`（3bf6e61）：新增 `CoverLoader` 单例，旧 CDN 路径优先、404 回退 `appdetails` 接口取 `header_image`，图片 6 并发 / 接口 2 并发，QPixmap + URL 双层缓存，失败重试 2 次；四个卡片类全部接入。实测封面可用 25/50 → 49/50
  - 新增 `.gitignore`：`config/`、`logs/`、`.venv/`、`__pycache__/`、本地启动 bat 不入库
  - 新增 `.fork-sync.env`、`.fork-sync-baseline`、`md/SYNC-GUIDE.md`、`md/SYNC-LOG.md`
- 自检：`./.venv/Scripts/python.exe -m py_compile main.py app/fluent_app.py backend/cai_backend.py backend/trainer_backend.py` → 通过；`import app.fluent_app` → 通过，`CoverLoader` 可导入
- 巡检：`inspect.sh` 基线 `upstream/main` @ d8ccb75，可快进 0；核心文件 4 个里只有 `app/fluent_app.py` blob 不同（其余 3 个与上游一致）；能力计数 后端函数 116/116、修改器后端 29/29、语言包 7/7、封面加载调用点 0/4（本地多出，属新增能力，非收窄）
- 推送：`local` → `origin/local`（203e623），已设置 tracking；`base-20261101` tag 只在本地，未推送
- 回滚点：`base-20261101`（= d8ccb75，接管前的干净基线）
