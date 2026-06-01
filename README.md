# 按鍵精靈 — 跨平台鍵盤自動化工具

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

### 使用 uv（推薦）

```bash
# 安裝相依套件
uv sync

# 啟動程式
uv run python main.py
```

### 使用 pip

```bash
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
