# 按鍵精靈 — 跨平台鍵盤自動化工具

[![GitHub](https://img.shields.io/badge/GitHub-leeyihua%2Fkeyboard__auto-blue?logo=github)](https://github.com/leeyihua/keyboard_auto)

以 Python + customtkinter 打造的視覺化鍵盤/滑鼠自動化工具，支援 macOS、Windows、Linux，可設定多種步驟組合成腳本並循環執行。

---

## 功能特色

- **6 種步驟類型**：等待、按鍵、連按（支援隨機間隔）、組合鍵、輸入文字、滑鼠點擊
- **腳本管理**：新增 / 開啟 / 儲存 / 另存 JSON 腳本檔
- **步驟操作**：新增、編輯、複製、刪除、上移、下移
- **執行控制**：設定循環次數（0 = 無限）、開始延遲、執行前自動切換英文輸入
- **全域熱鍵**：F9 執行 / F10 停止，即使視窗未在前景也有效
- **緊急停止**：pyautogui FailSafe — 將滑鼠移至螢幕左上角立即中止

---

## 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.12 以上 |
| 套件管理 | [uv](https://docs.astral.sh/uv/)（推薦）或 pip |
| macOS | 需授予「輔助功能」權限 |
| Windows | 無特殊需求 |
| Linux | 需安裝 `xdotool`，並在 X11 環境下執行 |

---

## 安裝與執行

### macOS / Linux

```bash
# 使用 uv（推薦）
uv sync
uv run python main.py

# 使用 pip
pip install customtkinter pillow pyautogui pynput pyperclip
python main.py
```

### Windows

**1. 安裝 Python 3.12+**

前往 [python.org](https://www.python.org/downloads/) 下載安裝，**務必勾選「Add Python to PATH」**。

**2. 安裝套件並執行**

```powershell
# 使用 uv（推薦）
winget install astral-sh.uv
uv sync
uv run python main.py

# 使用 pip
pip install customtkinter pillow pyautogui pynput pyperclip
python main.py
```

---

## macOS 輔助功能設定

首次執行時，程式會檢查輔助功能權限。若尚未授權，請依下列步驟操作：

1. 前往「系統設定」→「隱私權與安全性」→「輔助功能」
2. 點擊「＋」，加入「終端機」（或你所使用的終端 app）
3. 重新啟動程式

> 若使用 VS Code 或其他 IDE 執行，需將對應的 app 加入允許清單。

---

## 打包成 Windows 執行檔（.exe）

若要在沒有安裝 Python 的 Windows 電腦上執行，可用 PyInstaller 打包。

### 安裝 PyInstaller

```powershell
pip install pyinstaller
```

### 打包指令

```powershell
pyinstaller --onefile --windowed --name 按鍵精靈 --collect-all customtkinter main.py
```

| 參數 | 說明 |
|------|------|
| `--onefile` | 輸出為單一 `.exe` 檔案 |
| `--windowed` | 執行時不顯示命令提示字元視窗 |
| `--name 按鍵精靈` | 指定輸出檔名 |
| `--collect-all customtkinter` | 打包 customtkinter 所有主題與資源檔 |

打包完成後，執行檔位於 `dist/按鍵精靈.exe`。

### 加入自訂圖示（選用）

準備一個 `.ico` 格式的圖示檔，加上 `--icon` 參數：

```powershell
pyinstaller --onefile --windowed --name 按鍵精靈 --collect-all customtkinter --icon icon.ico main.py
```

### 注意事項

- 打包須在 **Windows 環境**下執行（無法在 macOS 打包 Windows 執行檔）
- 首次打包時間較長（需封裝 Python runtime），約 1～3 分鐘
- 部分防毒軟體可能誤報 PyInstaller 打包的執行檔，可提交白名單排除
- `profiles/` 腳本目錄會自動建立於執行檔同層目錄

### 平台差異對照

| 項目 | macOS | Windows |
|------|-------|---------|
| 輔助功能授權 | 需手動開啟 | 不需要 |
| 英文輸入切換 | AppleScript | ctypes（已內建）|
| `command` 鍵 | Mac Cmd 鍵 | 不適用，改用 `win` |
| 全域熱鍵 F9/F10 | 正常運作 | 正常運作 |

---

## 快捷鍵

| 快捷鍵 | 功能 |
|--------|------|
| `F9` | 執行腳本（全域） |
| `F10` | 停止執行（全域） |
| `Ctrl+N` | 新增腳本 |
| `Ctrl+O` | 開啟腳本 |
| `Ctrl+S` | 儲存 |
| `Ctrl+Shift+S` | 另存新檔 |
| `Ctrl+D` | 複製選取步驟 |
| `Ctrl+↑` | 步驟上移 |
| `Ctrl+↓` | 步驟下移 |
| `Delete` | 刪除選取步驟 |
| 步驟列雙擊 | 編輯步驟 |

---

## 腳本格式（JSON）

腳本儲存於 `profiles/` 目錄，格式如下：

```json
{
  "name": "範例腳本",
  "loop_count": 3,
  "start_delay": 3,
  "ensure_english": true,
  "steps": [
    { "type": "wait", "seconds": 1.0 },
    { "type": "key_press", "key": "f5" },
    {
      "type": "key_repeat",
      "key": "space",
      "count": 5,
      "interval": 1.0,
      "delay_min": 0.8,
      "delay_max": 1.2
    },
    { "type": "key_hotkey", "keys": ["ctrl", "a"] },
    { "type": "type_text", "text": "Hello, World!", "use_clipboard": true },
    { "type": "mouse_click", "x": 100, "y": 200, "button": "left" }
  ]
}
```

### 步驟類型說明

| type | 欄位 | 說明 |
|------|------|------|
| `wait` | `seconds` | 等待指定秒數 |
| `key_press` | `key` | 按下單一按鍵（如 `f5`、`enter`） |
| `key_repeat` | `key`, `count`, `interval`, `delay_min`, `delay_max` | 連按指定次數，可設定固定或隨機間隔 |
| `key_hotkey` | `keys` | 按下組合鍵（如 `["ctrl", "c"]`） |
| `type_text` | `text`, `use_clipboard` | 輸入文字，建議開啟 `use_clipboard` 以支援中文 |
| `mouse_click` | `x`, `y`, `button` | 點擊指定座標（`button`: `left`/`right`/`middle`） |

---

## 專案結構

```
keyboard_auto/
├── main.py              # 程式入口
├── engine.py            # 執行引擎
├── gui/
│   ├── main_window.py   # 主視窗
│   └── step_editor.py   # 步驟編輯對話框
├── config/
│   └── loader.py        # JSON 設定檔讀寫
├── profiles/            # 腳本存放目錄
│   └── example.json     # 範例腳本
└── pyproject.toml       # 套件設定
```

---

## 相依套件

| 套件 | 用途 |
|------|------|
| `customtkinter` | 現代化 GUI 框架 |
| `pyautogui` | 鍵盤 / 滑鼠模擬 |
| `pynput` | 全域熱鍵監聽 |
| `pyperclip` | 剪貼板操作（中文輸入支援） |
| `pillow` | customtkinter 圖片支援 |
