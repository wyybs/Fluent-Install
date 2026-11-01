#!/usr/bin/env python3
"""
Cai Install - Fluent Design 版本入口
"""
import sys
import os
import json
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.fluent_app import MainWindow, load_theme_config
from app.single_instance import SingleInstanceGuard, activate_window
from qfluentwidgets import setTheme, Theme, setThemeColor

def main():
    """主入口函数"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    # 启用高 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)

    app = QApplication(sys.argv)

    # 单实例锁：已经有实例在跑就通知它显示窗口，本次启动直接退出
    guard = SingleInstanceGuard()
    if not guard.try_acquire():
        print("[single-instance] 已有实例在运行，已唤起它的窗口，本次启动退出")
        sys.exit(0)

    # 加载主题配置
    theme_config = load_theme_config()
    
    # 应用主题设置
    theme_mode = theme_config["theme_mode"]
    if theme_mode == "light":
        setTheme(Theme.LIGHT)
    elif theme_mode == "dark":
        setTheme(Theme.DARK)
    else:
        setTheme(Theme.AUTO)
    
    # 应用主题色
    setThemeColor(theme_config["theme_color"])

    window = MainWindow()
    guard.activateRequested.connect(lambda: activate_window(window))
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
