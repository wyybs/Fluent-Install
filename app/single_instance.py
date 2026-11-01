"""单实例锁。

重复启动时不再开第二个进程，而是通过本地套接字通知已经运行的实例把窗口拉到前台。
实现用 QLocalServer / QLocalSocket（Windows 上是命名管道），不需要额外依赖。

用法（必须在 QApplication 创建之后、主窗口创建之前调用）::

    guard = SingleInstanceGuard()
    if not guard.try_acquire():
        sys.exit(0)                      # 已有实例，本次启动直接退出
    window = MainWindow()
    guard.activateRequested.connect(lambda: activate_window(window))
    window.show()
"""

from __future__ import annotations

import os
import sys
import time

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QWidget

# 服务名带版本号，避免和旧版（没有锁的版本）残留的管道名冲突
DEFAULT_KEY = "FluentInstall-SingleInstance-v1"

# 自我重启标记：程序内 os.execl 重开自己时，新进程要跳过「已有实例」判定，
# 否则旧进程还没退干净，新进程会被自己拦掉，表现为「换语言后程序直接消失」
RESTART_ENV = "FLUENTINSTALL_SELF_RESTART"


class SingleInstanceGuard(QObject):
    """占坑成功返回 True；发现已有实例返回 False 并负责通知对方显示窗口。"""

    activateRequested = pyqtSignal()

    def __init__(self, key: str = DEFAULT_KEY, parent: QObject | None = None):
        super().__init__(parent)
        self._key = key
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)

    def try_acquire(self) -> bool:
        # 自我重启：旧进程正在退出，等它释放管道，不要误判成「已有实例」
        if os.environ.pop(RESTART_ENV, None) == "1":
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                QLocalServer.removeServer(self._key)
                if self._server.listen(self._key):
                    return True
                time.sleep(0.15)
            print("[single-instance] 重启后未拿到实例锁，继续启动", file=sys.stderr)
            return True

        if self._notify_existing():
            return False
        # 上一次崩溃可能留下同名管道，先清掉再监听
        QLocalServer.removeServer(self._key)
        if not self._server.listen(self._key):
            # 拿不到锁也不能把程序卡死，退化为允许多开（行为与旧版一致）
            print(f"[single-instance] 监听失败，退化为多开: {self._server.errorString()}", file=sys.stderr)
        return True

    def _notify_existing(self) -> bool:
        """连得上说明已有实例在跑，发一条 activate 后返回 True。"""
        sock = QLocalSocket()
        sock.connectToServer(self._key)
        if not sock.waitForConnected(300):
            return False
        sock.write(b"activate")
        sock.waitForBytesWritten(300)
        sock.disconnectFromServer()
        return True

    def _on_new_connection(self):
        while self._server.hasPendingConnections():
            conn = self._server.nextPendingConnection()
            if conn is not None:
                conn.readAll()
                conn.disconnectFromServer()
                conn.deleteLater()
            print("[single-instance] 收到重复启动请求，唤起已有窗口", file=sys.stderr)
            self.activateRequested.emit()


def activate_window(window: QWidget | None) -> None:
    """把已存在的窗口从最小化 / 后台状态恢复到前台。"""
    if window is None:
        return

    state = window.windowState()
    if state & Qt.WindowState.WindowMinimized:
        window.setWindowState(state & ~Qt.WindowState.WindowMinimized)
    if not window.isVisible():
        window.show()
    window.raise_()
    window.activateWindow()

    if sys.platform == "win32":
        # Qt 的 activateWindow 在 Windows 前台锁下可能被忽略，直接调 Win32 兜底
        try:
            import ctypes

            hwnd = int(window.winId())
            ctypes.windll.user32.ShowWindow(hwnd, 9)          # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except Exception:
            pass
