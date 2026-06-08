import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

# tkinter keysym → pynput 按鍵名稱對應
_KEYSYM_MAP = {
    "Return": "enter", "BackSpace": "backspace", "Delete": "delete",
    "Escape": "escape", "Tab": "tab", "Insert": "insert",
    "Home": "home", "End": "end", "Prior": "pageup", "Next": "pagedown",
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Caps_Lock": "capslock", "Num_Lock": "numlock", "Scroll_Lock": "scrolllock",
    "Pause": "pause", "Print": "printscreen", "space": "space",
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4",
    "F5": "f5", "F6": "f6", "F7": "f7", "F8": "f8",
    "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
}

COMMON_KEYS = [
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "enter", "space", "tab", "backspace", "delete", "escape", "insert",
    "home", "end", "pageup", "pagedown",
    "up", "down", "left", "right",
    "capslock", "numlock", "scrolllock", "pause", "printscreen",
    "volumeup", "volumedown", "volumemute",
]

STEP_TYPES = [
    ("wait",        "等待"),
    ("key_press",   "按鍵"),
    ("key_hold",    "按住"),
    ("key_repeat",  "連按"),
    ("key_hotkey",  "組合鍵"),
    ("type_text",   "輸入文字"),
    ("mouse_click", "滑鼠點擊"),
]

# 各步驟類型對應的對話框高度
TYPE_HEIGHTS = {
    "wait":        200,
    "key_press":   200,
    "key_hold":    220,
    "key_repeat":  310,
    "key_hotkey":  250,
    "type_text":   330,
    "mouse_click": 270,
}


class StepEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="步驟編輯", step=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._field_widgets = {}
        self.grab_set()
        self.transient(parent)

        self._build_ui()

        if step:
            self._load_step(step)
        else:
            self._on_type_change(self.type_var.get())

        self.focus()
        self.bind("<Escape>", lambda e: self.destroy())

    # ── UI 建構 ───────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 步驟類型選擇列
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="ew")

        ctk.CTkLabel(top, text="步驟類型：", font=("", 13, "bold")).pack(side="left", padx=(0, 8))
        type_labels = [label for _, label in STEP_TYPES]
        self.type_var = tk.StringVar(value=type_labels[0])
        ctk.CTkOptionMenu(
            top, values=type_labels, variable=self.type_var,
            width=140, command=self._on_type_change,
        ).pack(side="left")

        # 欄位區域
        self.fields_frame = ctk.CTkFrame(self)
        self.fields_frame.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        self.fields_frame.grid_columnconfigure(1, weight=1)

        # 按鈕列
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=2, column=0, padx=15, pady=(5, 12), sticky="e")
        ctk.CTkButton(btn_row, text="取消", width=80, fg_color="gray50",
                      command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_row, text="確定", width=80,
                      command=self._on_ok).pack(side="right", padx=5)

    def _clear_fields(self):
        for w in self.fields_frame.winfo_children():
            w.destroy()
        self._field_widgets.clear()

    def _row(self, row, label_text, widget, key):
        """在 fields_frame 加入一列 label + widget"""
        ctk.CTkLabel(self.fields_frame, text=label_text, anchor="e", width=100).grid(
            row=row, column=0, padx=(10, 6), pady=7, sticky="e"
        )
        widget.grid(row=row, column=1, padx=(0, 12), pady=7, sticky="ew")
        self._field_widgets[key] = widget

    def _key_row(self, row, label_text, key):
        """加入按鍵選擇列：含滾輪支援 + 直接按鍵擷取按鈕"""
        ctk.CTkLabel(self.fields_frame, text=label_text, anchor="e", width=100).grid(
            row=row, column=0, padx=(10, 6), pady=7, sticky="e"
        )
        inner = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
        inner.grid(row=row, column=1, padx=(0, 12), pady=7, sticky="ew")
        inner.grid_columnconfigure(0, weight=1)

        combo = ctk.CTkComboBox(inner, values=COMMON_KEYS, width=160)
        combo.grid(row=0, column=0, sticky="ew")

        def _scroll(event, c=combo):
            cur = c.get()
            try:
                idx = COMMON_KEYS.index(cur)
            except ValueError:
                idx = 0
            delta = -1 if (event.delta > 0 or event.num == 4) else 1
            c.set(COMMON_KEYS[(idx + delta) % len(COMMON_KEYS)])

        combo.bind("<MouseWheel>", _scroll)
        combo.bind("<Button-4>", _scroll)
        combo.bind("<Button-5>", _scroll)
        try:
            combo._entry.bind("<MouseWheel>", _scroll)
            combo._entry.bind("<Button-4>", _scroll)
            combo._entry.bind("<Button-5>", _scroll)
        except AttributeError:
            pass

        btn = ctk.CTkButton(inner, text="按鍵", width=55,
                            command=lambda: self._start_key_capture(combo, btn))
        btn.grid(row=0, column=1, padx=(6, 0))

        self._field_widgets[key] = combo

    def _start_key_capture(self, combo, btn):
        """進入按鍵擷取模式：下一個按鍵將被設定為選取值"""
        btn.configure(text="請按鍵...", state="disabled")
        self.unbind("<Escape>")

        def _on_key(event):
            self.unbind("<KeyPress>")
            self.bind("<Escape>", lambda e: self.destroy())
            btn.configure(text="按鍵", state="normal")
            key_name = _KEYSYM_MAP.get(event.keysym, event.keysym.lower())
            combo.set(key_name)
            return "break"

        self.bind("<KeyPress>", _on_key)
        self.focus_set()

    # ── 類型切換 ──────────────────────────────────────────────────

    def _on_type_change(self, type_label):
        self._clear_fields()
        type_key = next((k for k, v in STEP_TYPES if v == type_label), "wait")
        self.geometry(f"450x{TYPE_HEIGHTS[type_key]}")

        if type_key == "wait":
            e = ctk.CTkEntry(self.fields_frame, placeholder_text="1.0")
            self._row(0, "等待時間（秒）：", e, "seconds")

        elif type_key == "key_press":
            self._key_row(0, "按鍵：", "key")

        elif type_key == "key_hold":
            self._key_row(0, "按鍵：", "key")
            self._row(1, "按住時間（秒）：",
                      ctk.CTkEntry(self.fields_frame, placeholder_text="10"), "duration")

        elif type_key == "key_repeat":
            self._key_row(0, "按鍵：", "key")
            self._row(1, "次數：",
                      ctk.CTkEntry(self.fields_frame, placeholder_text="5"), "count")
            self._row(2, "固定間隔（秒）：",
                      ctk.CTkEntry(self.fields_frame, placeholder_text="1.0"), "interval")
            # 隨機延遲範圍
            rnd = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            rnd.grid(row=3, column=0, columnspan=2, padx=10, pady=4, sticky="ew")
            ctk.CTkLabel(rnd, text="隨機範圍：", width=100, anchor="e").pack(side="left")
            e_min = ctk.CTkEntry(rnd, placeholder_text="最小", width=80)
            e_min.pack(side="left", padx=4)
            ctk.CTkLabel(rnd, text="～").pack(side="left")
            e_max = ctk.CTkEntry(rnd, placeholder_text="最大", width=80)
            e_max.pack(side="left", padx=4)
            ctk.CTkLabel(rnd, text="秒（留空=固定）", text_color="gray").pack(side="left", padx=4)
            self._field_widgets["delay_min"] = e_min
            self._field_widgets["delay_max"] = e_max

        elif type_key == "key_hotkey":
            inner = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            inner.grid(row=0, column=0, columnspan=2, padx=12, pady=10, sticky="ew")
            ctk.CTkLabel(inner, text="組合鍵（以 + 分隔）：", font=("", 12)).pack(anchor="w", pady=(0, 4))
            e = ctk.CTkEntry(inner, placeholder_text="例如：ctrl+c  或  alt+f4  或  ctrl+shift+s", width=320)
            e.pack(anchor="w")
            ctk.CTkLabel(inner,
                         text="可用修飾鍵：ctrl、shift、alt、command（Mac）、win（Windows）",
                         font=("", 10), text_color="gray").pack(anchor="w", pady=(6, 0))
            self._field_widgets["hotkey_str"] = e

        elif type_key == "type_text":
            ctk.CTkLabel(self.fields_frame, text="文字內容：", anchor="w").grid(
                row=0, column=0, columnspan=2, padx=12, pady=(10, 2), sticky="w"
            )
            tb = ctk.CTkTextbox(self.fields_frame, height=110, wrap="word")
            tb.grid(row=1, column=0, columnspan=2, padx=12, pady=2, sticky="ew")
            self._field_widgets["text"] = tb

            cb_var = tk.BooleanVar(value=True)
            ctk.CTkCheckBox(self.fields_frame, text="使用剪貼板貼上（建議，支援中文）",
                            variable=cb_var).grid(
                row=2, column=0, columnspan=2, padx=12, pady=4, sticky="w"
            )
            self._field_widgets["use_clipboard"] = cb_var

        elif type_key == "mouse_click":
            self._row(0, "X 座標：",
                      ctk.CTkEntry(self.fields_frame, placeholder_text="0"), "x")
            self._row(1, "Y 座標：",
                      ctk.CTkEntry(self.fields_frame, placeholder_text="0"), "y")

            btn_f = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            btn_f.grid(row=2, column=0, columnspan=2, padx=10, pady=4, sticky="ew")
            ctk.CTkLabel(btn_f, text="滑鼠按鍵：", width=100, anchor="e").pack(side="left")
            btn_var = tk.StringVar(value="左鍵")
            ctk.CTkOptionMenu(btn_f, values=["左鍵", "右鍵", "中鍵"],
                              variable=btn_var, width=100).pack(side="left", padx=6)
            self._field_widgets["button"] = btn_var

            ctk.CTkButton(self.fields_frame, text="📍 擷取滑鼠座標（3 秒後）",
                          command=self._capture_mouse).grid(
                row=3, column=0, columnspan=2, padx=12, pady=8
            )

    # ── 載入已有步驟 ──────────────────────────────────────────────

    def _load_step(self, step):
        t = step.get("type", "wait")
        label = next((v for k, v in STEP_TYPES if k == t), "等待")
        self.type_var.set(label)
        self._on_type_change(label)
        w = self._field_widgets

        if t == "wait":
            w["seconds"].insert(0, str(step.get("seconds", 1)))
        elif t == "key_press":
            w["key"].set(step.get("key", ""))
        elif t == "key_hold":
            w["key"].set(step.get("key", ""))
            w["duration"].insert(0, str(step.get("duration", 1)))
        elif t == "key_repeat":
            w["key"].set(step.get("key", ""))
            w["count"].insert(0, str(step.get("count", 1)))
            w["interval"].insert(0, str(step.get("interval", 0.5)))
            d_min = step.get("delay_min", "")
            d_max = step.get("delay_max", "")
            interval = step.get("interval", 0.5)
            if d_min != "" and float(d_min) != interval:
                w["delay_min"].insert(0, str(d_min))
            if d_max != "" and float(d_max) != interval:
                w["delay_max"].insert(0, str(d_max))
        elif t == "key_hotkey":
            w["hotkey_str"].insert(0, "+".join(step.get("keys", [])))
        elif t == "type_text":
            w["text"].insert("1.0", step.get("text", ""))
            w["use_clipboard"].set(step.get("use_clipboard", True))
        elif t == "mouse_click":
            w["x"].insert(0, str(step.get("x", 0)))
            w["y"].insert(0, str(step.get("y", 0)))
            btn_map = {"left": "左鍵", "right": "右鍵", "middle": "中鍵"}
            w["button"].set(btn_map.get(step.get("button", "left"), "左鍵"))

    # ── 確定送出 ──────────────────────────────────────────────────

    def _on_ok(self):
        type_label = self.type_var.get()
        t = next((k for k, v in STEP_TYPES if v == type_label), "wait")
        w = self._field_widgets
        try:
            if t == "wait":
                secs = float(w["seconds"].get() or "1")
                self.result = {"type": "wait", "seconds": secs}

            elif t == "key_press":
                key = w["key"].get().strip()
                if not key:
                    messagebox.showwarning("提示", "請輸入按鍵名稱", parent=self)
                    return
                self.result = {"type": "key_press", "key": key}

            elif t == "key_hold":
                key = w["key"].get().strip()
                if not key:
                    messagebox.showwarning("提示", "請輸入按鍵名稱", parent=self)
                    return
                duration = float(w["duration"].get() or "1")
                self.result = {"type": "key_hold", "key": key, "duration": duration}

            elif t == "key_repeat":
                key = w["key"].get().strip()
                if not key:
                    messagebox.showwarning("提示", "請輸入按鍵名稱", parent=self)
                    return
                count = int(w["count"].get() or "1")
                interval = float(w["interval"].get() or "0.5")
                s_min = w["delay_min"].get().strip()
                s_max = w["delay_max"].get().strip()
                d_min = float(s_min) if s_min else interval
                d_max = float(s_max) if s_max else interval
                self.result = {
                    "type": "key_repeat", "key": key,
                    "count": count, "interval": interval,
                    "delay_min": d_min, "delay_max": d_max,
                }

            elif t == "key_hotkey":
                raw = w["hotkey_str"].get().strip()
                if not raw:
                    messagebox.showwarning("提示", "請輸入組合鍵", parent=self)
                    return
                keys = [k.strip() for k in raw.split("+") if k.strip()]
                self.result = {"type": "key_hotkey", "keys": keys}

            elif t == "type_text":
                text = w["text"].get("1.0", "end-1c")
                if not text:
                    messagebox.showwarning("提示", "請輸入文字內容", parent=self)
                    return
                use_cb = w["use_clipboard"].get()
                self.result = {"type": "type_text", "text": text, "use_clipboard": use_cb}

            elif t == "mouse_click":
                x = int(w["x"].get() or "0")
                y = int(w["y"].get() or "0")
                btn_map = {"左鍵": "left", "右鍵": "right", "中鍵": "middle"}
                button = btn_map.get(w["button"].get(), "left")
                self.result = {"type": "mouse_click", "x": x, "y": y, "button": button}

            self.destroy()

        except ValueError as e:
            messagebox.showerror("輸入錯誤", f"請檢查數值格式：\n{e}", parent=self)

    # ── 擷取滑鼠座標 ──────────────────────────────────────────────

    def _capture_mouse(self):
        import pyautogui
        import threading

        def _do():
            import time
            for i in range(3, 0, -1):
                self.after(0, lambda i=i: self._set_capture_hint(f"請移動滑鼠到目標位置... {i}"))
                time.sleep(1)
            x, y = pyautogui.position()
            def _update():
                w = self._field_widgets
                w["x"].delete(0, "end")
                w["x"].insert(0, str(x))
                w["y"].delete(0, "end")
                w["y"].insert(0, str(y))
                self._set_capture_hint(f"已擷取：({x}, {y})")
            self.after(0, _update)

        threading.Thread(target=_do, daemon=True).start()

    def _set_capture_hint(self, msg):
        # 在 fields_frame 尋找或建立提示 label
        if not hasattr(self, "_hint_label"):
            self._hint_label = ctk.CTkLabel(self.fields_frame, text="", text_color="dodgerblue")
            self._hint_label.grid(row=4, column=0, columnspan=2, padx=12, pady=2)
        self._hint_label.configure(text=msg)
