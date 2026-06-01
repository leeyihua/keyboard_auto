import copy
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

# 確保根目錄在 sys.path 中
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.loader import load, new_config, save
from engine import ExecutionEngine
from gui.step_editor import StepEditorDialog, STEP_TYPES

STEP_TYPE_LABELS = {k: v for k, v in STEP_TYPES}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("按鍵精靈")
        self.geometry("760x560")
        self.minsize(640, 460)

        self.config_data = new_config()
        self.current_file = None
        self.selected_index = None

        self.engine = ExecutionEngine()

        self._build_ui()
        self._setup_global_hotkeys()
        self._bind_keys()
        self._refresh_list()

    # ── UI 建構 ───────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_toolbar()
        self._build_options_bar()
        self._build_content()
        self._build_statusbar()

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, height=46, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(5, weight=1)

        btn_kw = dict(width=64, height=30)
        ctk.CTkButton(bar, text="新增", **btn_kw, command=self._new).grid(
            row=0, column=0, padx=(10, 3), pady=8)
        ctk.CTkButton(bar, text="開啟", **btn_kw, command=self._open).grid(
            row=0, column=1, padx=3, pady=8)
        ctk.CTkButton(bar, text="儲存", **btn_kw, command=self._save).grid(
            row=0, column=2, padx=3, pady=8)
        ctk.CTkButton(bar, text="另存", **btn_kw, fg_color="gray50",
                      command=self._save_as).grid(row=0, column=3, padx=3, pady=8)

        # 分隔
        ctk.CTkFrame(bar, width=2, height=30, fg_color="gray60").grid(
            row=0, column=4, padx=10)

        ctk.CTkLabel(bar, text="腳本名稱：").grid(row=0, column=5, padx=(0, 4), sticky="e")
        self.name_var = tk.StringVar(value=self.config_data.get("name", ""))
        ctk.CTkEntry(bar, textvariable=self.name_var, width=180).grid(
            row=0, column=6, padx=(0, 10), pady=8)

    def _build_options_bar(self):
        bar = ctk.CTkFrame(self, height=38, corner_radius=0,
                           fg_color=("gray90", "gray20"))
        bar.grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(bar, text="執行次數：").pack(side="left", padx=(12, 3))
        self.loop_var = tk.StringVar(value=str(self.config_data.get("loop_count", 1)))
        ctk.CTkEntry(bar, textvariable=self.loop_var, width=52).pack(side="left")
        ctk.CTkLabel(bar, text="（0 = 無限）", text_color="gray").pack(
            side="left", padx=(3, 16))

        ctk.CTkLabel(bar, text="開始延遲（秒）：").pack(side="left", padx=(0, 3))
        self.delay_var = tk.StringVar(value=str(self.config_data.get("start_delay", 3)))
        ctk.CTkEntry(bar, textvariable=self.delay_var, width=46).pack(side="left")

        self.eng_var = tk.BooleanVar(value=self.config_data.get("ensure_english", True))
        ctk.CTkCheckBox(bar, text="執行前切換英文輸入",
                        variable=self.eng_var).pack(side="left", padx=16)

    def _build_content(self):
        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # ── 步驟列表 ──────────────────────────────────────────────
        list_outer = ctk.CTkFrame(content)
        list_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        list_outer.grid_rowconfigure(1, weight=1)
        list_outer.grid_columnconfigure(0, weight=1)

        # 表頭
        header = ctk.CTkFrame(list_outer, height=28, fg_color=("gray75", "gray30"),
                              corner_radius=4)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(header, text="#", width=36, font=("", 11, "bold")).grid(
            row=0, column=0, padx=6)
        ctk.CTkLabel(header, text="步驟類型", width=80, font=("", 11, "bold")).grid(
            row=0, column=1, padx=4)
        ctk.CTkLabel(header, text="參數", font=("", 11, "bold"), anchor="w").grid(
            row=0, column=2, padx=6, sticky="w")

        self.step_scroll = ctk.CTkScrollableFrame(list_outer, corner_radius=4)
        self.step_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self.step_scroll.grid_columnconfigure(0, weight=1)
        self.step_rows = []

        self.empty_label = ctk.CTkLabel(
            self.step_scroll,
            text="尚無步驟 — 點擊右側「新增步驟」開始",
            text_color="gray",
            font=("", 12),
        )

        # ── 側邊操作欄 ────────────────────────────────────────────
        sidebar = ctk.CTkFrame(content, width=124, fg_color="transparent")
        sidebar.grid(row=0, column=1, sticky="ns")

        kw = dict(width=116, height=32)
        ctk.CTkButton(sidebar, text="＋ 新增步驟", **kw,
                      command=self._add_step).pack(pady=3)
        ctk.CTkButton(sidebar, text="✎  編輯步驟", **kw,
                      command=self._edit_step).pack(pady=3)
        ctk.CTkButton(sidebar, text="⧉  複製步驟", **kw,
                      command=self._dup_step).pack(pady=3)
        ctk.CTkButton(sidebar, text="✕  刪除步驟", **kw,
                      fg_color=("red3", "red4"), hover_color=("red4", "red3"),
                      command=self._del_step).pack(pady=3)

        ctk.CTkFrame(sidebar, height=14, fg_color="transparent").pack()
        ctk.CTkButton(sidebar, text="▲  上移", **kw,
                      command=self._move_up).pack(pady=3)
        ctk.CTkButton(sidebar, text="▼  下移", **kw,
                      command=self._move_down).pack(pady=3)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=44, corner_radius=0)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(bar, text="就緒　│　按 F9 執行 / F10 停止",
                                         anchor="w", font=("", 12))
        self.status_label.grid(row=0, column=0, padx=12, sticky="ew")

        self.run_btn = ctk.CTkButton(
            bar, text="▶  執行 (F9)", width=128, height=32,
            fg_color=("green4", "green3"), hover_color=("green3", "green2"),
            command=self._start,
        )
        self.run_btn.grid(row=0, column=1, padx=5, pady=6)

        self.stop_btn = ctk.CTkButton(
            bar, text="■  停止 (F10)", width=128, height=32,
            fg_color="gray50", state="disabled",
            command=self._stop,
        )
        self.stop_btn.grid(row=0, column=2, padx=(0, 10), pady=6)

    # ── 步驟列表渲染 ──────────────────────────────────────────────

    def _refresh_list(self):
        for row in self.step_rows:
            row.destroy()
        self.step_rows.clear()

        steps = self.config_data.get("steps", [])
        if not steps:
            self.empty_label.pack(pady=30)
        else:
            self.empty_label.pack_forget()
            for i, step in enumerate(steps):
                row = self._make_row(i, step)
                row.grid(row=i, column=0, sticky="ew", pady=1)
                self.step_rows.append(row)

        self._apply_row_colors()

    def _make_row(self, idx, step):
        row = ctk.CTkFrame(self.step_scroll, height=30, corner_radius=3)
        row.grid_columnconfigure(2, weight=1)

        num = ctk.CTkLabel(row, text=str(idx + 1), width=36, font=("", 11))
        num.grid(row=0, column=0, padx=6)

        type_lbl = ctk.CTkLabel(
            row, text=STEP_TYPE_LABELS.get(step.get("type", ""), step.get("type", "")),
            width=80, font=("", 11),
        )
        type_lbl.grid(row=0, column=1, padx=4)

        desc = ctk.CTkLabel(row, text=self._step_desc(step), font=("", 11), anchor="w")
        desc.grid(row=0, column=2, padx=6, sticky="ew")

        def _click(e, i=idx):
            self.selected_index = i
            self._apply_row_colors()

        def _dbl(e, i=idx):
            self.selected_index = i
            self._edit_step()

        for w in (row, num, type_lbl, desc):
            w.bind("<Button-1>", _click)
            w.bind("<Double-Button-1>", _dbl)

        return row

    def _apply_row_colors(self):
        for i, row in enumerate(self.step_rows):
            selected = (i == self.selected_index)
            fg = ("dodgerblue2", "royalblue4") if selected else ("gray85", "gray22")
            tc = "white" if selected else None
            row.configure(fg_color=fg)
            for w in row.winfo_children():
                try:
                    kw = {"text_color": tc} if tc else {"text_color": ("gray10", "gray90")}
                    w.configure(**kw)
                except Exception:
                    pass

    def _step_desc(self, step):
        t = step.get("type", "")
        if t == "wait":
            return f"{step.get('seconds', 1)} 秒"
        if t == "key_press":
            return f"[{step.get('key', '')}]"
        if t == "key_repeat":
            d_min = step.get("delay_min", step.get("interval", 0.5))
            d_max = step.get("delay_max", step.get("interval", 0.5))
            iv = f"{d_min}～{d_max}" if d_min != d_max else str(step.get("interval", 0.5))
            return f"[{step.get('key','')}] × {step.get('count',1)} 次，間隔 {iv} 秒"
        if t == "key_hotkey":
            return f"[{' + '.join(step.get('keys', []))}]"
        if t == "type_text":
            txt = step.get("text", "")
            return f"\"{txt[:28]}{'...' if len(txt) > 28 else ''}\""
        if t == "mouse_click":
            bm = {"left": "左鍵", "right": "右鍵", "middle": "中鍵"}
            return (f"{bm.get(step.get('button','left'),'左鍵')} "
                    f"({step.get('x',0)}, {step.get('y',0)})")
        return ""

    # ── 步驟操作 ──────────────────────────────────────────────────

    def _add_step(self):
        dlg = StepEditorDialog(self, title="新增步驟")
        self.wait_window(dlg)
        if dlg.result:
            steps = self.config_data.setdefault("steps", [])
            pos = len(steps) if self.selected_index is None else self.selected_index + 1
            steps.insert(pos, dlg.result)
            self.selected_index = pos
            self._refresh_list()

    def _edit_step(self):
        if not self._check_selection():
            return
        steps = self.config_data.get("steps", [])
        dlg = StepEditorDialog(self, title="編輯步驟", step=steps[self.selected_index])
        self.wait_window(dlg)
        if dlg.result:
            steps[self.selected_index] = dlg.result
            self._refresh_list()

    def _del_step(self):
        if not self._check_selection():
            return
        steps = self.config_data.get("steps", [])
        if messagebox.askyesno("確認刪除", f"確定要刪除步驟 {self.selected_index + 1}？"):
            steps.pop(self.selected_index)
            if self.selected_index >= len(steps):
                self.selected_index = len(steps) - 1 if steps else None
            self._refresh_list()

    def _dup_step(self):
        if not self._check_selection():
            return
        steps = self.config_data.get("steps", [])
        steps.insert(self.selected_index + 1, copy.deepcopy(steps[self.selected_index]))
        self.selected_index += 1
        self._refresh_list()

    def _move_up(self):
        if self.selected_index is None or self.selected_index == 0:
            return
        steps = self.config_data.get("steps", [])
        i = self.selected_index
        steps[i], steps[i - 1] = steps[i - 1], steps[i]
        self.selected_index -= 1
        self._refresh_list()

    def _move_down(self):
        if self.selected_index is None:
            return
        steps = self.config_data.get("steps", [])
        i = self.selected_index
        if i >= len(steps) - 1:
            return
        steps[i], steps[i + 1] = steps[i + 1], steps[i]
        self.selected_index += 1
        self._refresh_list()

    def _check_selection(self):
        if self.selected_index is None:
            messagebox.showwarning("提示", "請先點選一個步驟")
            return False
        steps = self.config_data.get("steps", [])
        if self.selected_index >= len(steps):
            self.selected_index = None
            return False
        return True

    # ── 檔案操作 ──────────────────────────────────────────────────

    def _new(self):
        if messagebox.askyesno("新增腳本", "建立新腳本？未儲存的內容將會遺失。"):
            self.config_data = new_config()
            self.current_file = None
            self.selected_index = None
            self.name_var.set(self.config_data["name"])
            self.loop_var.set(str(self.config_data["loop_count"]))
            self.delay_var.set(str(self.config_data["start_delay"]))
            self.eng_var.set(self.config_data["ensure_english"])
            self.title("按鍵精靈")
            self._refresh_list()

    def _open(self):
        path = filedialog.askopenfilename(
            title="開啟腳本",
            filetypes=[("JSON 設定檔", "*.json"), ("所有檔案", "*.*")],
            initialdir=self._profiles_dir(),
        )
        if not path:
            return
        try:
            data = load(path)
            self.config_data = data
            self.current_file = path
            self.selected_index = None
            self.name_var.set(data.get("name", ""))
            self.loop_var.set(str(data.get("loop_count", 1)))
            self.delay_var.set(str(data.get("start_delay", 3)))
            self.eng_var.set(data.get("ensure_english", True))
            script_name = data.get("name", "") or os.path.basename(path)
            self.title(f"按鍵精靈 — {script_name}")
            self._refresh_list()
        except Exception as e:
            messagebox.showerror("開啟失敗", str(e))

    def _save(self):
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self._save_as()

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            title="儲存腳本",
            filetypes=[("JSON 設定檔", "*.json"), ("所有檔案", "*.*")],
            defaultextension=".json",
            initialdir=self._profiles_dir(),
            initialfile=(self.name_var.get() or "腳本") + ".json",
        )
        if path:
            self._do_save(path)

    def _do_save(self, path):
        self._sync_ui_to_config()
        try:
            save(path, self.config_data)
            self.current_file = path
            script_name = self.config_data.get("name", "") or os.path.basename(path)
            self.title(f"按鍵精靈 — {script_name}")
        except Exception as e:
            messagebox.showerror("儲存失敗", str(e))

    def _profiles_dir(self):
        d = ROOT / "profiles"
        d.mkdir(exist_ok=True)
        return str(d)

    def _sync_ui_to_config(self):
        self.config_data["name"] = self.name_var.get()
        try:
            self.config_data["loop_count"] = int(self.loop_var.get())
        except ValueError:
            self.config_data["loop_count"] = 1
        try:
            self.config_data["start_delay"] = int(self.delay_var.get())
        except ValueError:
            self.config_data["start_delay"] = 3
        self.config_data["ensure_english"] = self.eng_var.get()

    # ── 執行控制 ──────────────────────────────────────────────────

    def _start(self):
        if self.engine.is_running():
            return
        self._sync_ui_to_config()
        if not self.config_data.get("steps"):
            messagebox.showwarning("提示", "腳本中沒有步驟，請先新增步驟。")
            return
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal", fg_color=("red3", "red4"))
        self.engine.start(self.config_data)
        self.after(100, self._monitor_engine)

    def _stop(self):
        self.engine.stop()

    def _monitor_engine(self):
        if self.engine.status_text:
            self.status_label.configure(text=self.engine.status_text)
        if self.engine.is_running():
            self.after(100, self._monitor_engine)
        else:
            self.run_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled", fg_color="gray50")

    # ── 熱鍵 ──────────────────────────────────────────────────────

    def _setup_global_hotkeys(self):
        try:
            from pynput import keyboard

            def on_f9():
                if not self.engine.is_running():
                    self.after(0, self._start)

            def on_f10():
                if self.engine.is_running():
                    self.after(0, self._stop)

            self._hotkey_listener = keyboard.GlobalHotKeys(
                {"<f9>": on_f9, "<f10>": on_f10}
            )
            self._hotkey_listener.start()
        except Exception:
            pass

    def _bind_keys(self):
        self.bind("<Control-n>", lambda e: self._new())
        self.bind("<Control-o>", lambda e: self._open())
        self.bind("<Control-s>", lambda e: self._save())
        self.bind("<Control-S>", lambda e: self._save_as())
        self.bind("<F9>",        lambda e: self._start())
        self.bind("<F10>",       lambda e: self._stop())
        self.bind("<Delete>",    lambda e: self._del_step())
        self.bind("<Control-d>", lambda e: self._dup_step())
        self.bind("<Control-Up>",   lambda e: self._move_up())
        self.bind("<Control-Down>", lambda e: self._move_down())

    # ── 關閉清理 ──────────────────────────────────────────────────

    def destroy(self):
        try:
            if hasattr(self, "_hotkey_listener"):
                self._hotkey_listener.stop()
        except Exception:
            pass
        self.engine.stop()
        super().destroy()
