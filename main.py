import sys
import os
import platform

# 確保根目錄在 sys.path 中
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import customtkinter as ctk


def check_mac_accessibility():
    """Mac 上嘗試確認輔助功能權限是否已授予"""
    import subprocess
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of first process'],
            capture_output=True, timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False


def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    from gui.main_window import MainWindow
    app = MainWindow()

    # Mac 輔助功能提示（僅首次啟動時）
    if platform.system() == "Darwin":
        if not check_mac_accessibility():
            from tkinter import messagebox
            messagebox.showwarning(
                "需要輔助功能權限",
                "模擬鍵盤輸入需要輔助功能權限。\n\n"
                "請前往：\n"
                "系統設定 → 隱私權與安全性 → 輔助功能\n\n"
                "將「終端機」或此應用程式加入允許清單，\n"
                "然後重新啟動程式。",
                parent=app,
            )

    app.mainloop()


if __name__ == "__main__":
    main()
