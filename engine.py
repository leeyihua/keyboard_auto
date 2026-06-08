import time
import threading
import platform
import random

import pyautogui
import pyperclip

pyautogui.FAILSAFE = True

STEP_LABELS = {
    "wait": "等待",
    "key_press": "按鍵",
    "key_hold": "按住",
    "key_repeat": "連按",
    "key_hotkey": "組合鍵",
    "type_text": "輸入文字",
    "mouse_click": "滑鼠點擊",
}


class ExecutionEngine:
    def __init__(self):
        self.running = False
        self._thread = None
        self.on_status = None    # callback(loop, total_loops, step, total_steps, message)
        self.on_finished = None  # callback(cancelled: bool)
        self.status_text = ""    # 供主執行緒輪詢用

    def start(self, config):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._run, args=(config,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self.status_text = "已停止"
        self.running = False

    def is_running(self):
        return self.running

    # ── 主執行迴圈 ────────────────────────────────────────────────

    def _run(self, config):
        steps = config.get("steps", [])
        loop_count = config.get("loop_count", 1)
        start_delay = int(config.get("start_delay", 3))
        infinite = loop_count == 0
        pyautogui.PAUSE = 0
        key_pause = float(config.get("key_pause", 0.1))

        # 倒數計時
        for i in range(start_delay, 0, -1):
            if not self.running:
                self._finish(True)
                return
            self._notify(0, loop_count, 0, len(steps), f"準備中... {i} 秒後開始")
            time.sleep(1)

        loop = 0
        try:
            while self.running and (infinite or loop < loop_count):
                loop += 1
                for idx, step in enumerate(steps):
                    if not self.running:
                        break
                    self._notify(loop, loop_count, idx + 1, len(steps),
                                 self._step_desc(step))
                    self._execute_step(step, key_pause)
        except pyautogui.FailSafeException:
            self.running = False
            self._notify(0, loop_count, 0, len(steps), "緊急停止（滑鼠移至螢幕角落）")
        except Exception as e:
            self.running = False
            self._notify(0, loop_count, 0, len(steps), f"執行錯誤：{e}")

        self._finish(not self.running)

    # ── 步驟執行 ──────────────────────────────────────────────────

    def _execute_step(self, step, key_pause=0.1):
        t = step.get("type")

        if t == "wait":
            self._sleep(float(step.get("seconds", 1)))

        elif t == "key_press":
            key = step.get("key", "")
            if key:
                pyautogui.press(key)

        elif t == "key_hold":
            key = step.get("key", "")
            duration = float(step.get("duration", 1))
            if key:
                pyautogui.keyDown(key)
                self._sleep(duration)
                pyautogui.keyUp(key)

        elif t == "key_repeat":
            key = step.get("key", "")
            count = int(step.get("count", 1))
            interval = float(step.get("interval", 0.5))
            d_min = float(step.get("delay_min", interval))
            d_max = float(step.get("delay_max", interval))
            for i in range(count):
                if not self.running:
                    break
                pyautogui.press(key)
                if i < count - 1:
                    self._sleep(random.uniform(d_min, d_max))

        elif t == "key_hotkey":
            keys = step.get("keys", [])
            if keys:
                pyautogui.hotkey(*keys)

        elif t == "type_text":
            text = step.get("text", "")
            use_cb = step.get("use_clipboard", True)
            if not text:
                return
            if use_cb:
                # 使用剪貼板貼上，支援中文及特殊字元
                old = ""
                try:
                    old = pyperclip.paste()
                except Exception:
                    pass
                pyperclip.copy(text)
                time.sleep(0.1)
                if platform.system() == "Darwin":
                    pyautogui.hotkey("command", "v")
                else:
                    pyautogui.hotkey("ctrl", "v")
                time.sleep(0.1)
                try:
                    pyperclip.copy(old)
                except Exception:
                    pass
            else:
                pyautogui.write(text, interval=0.05)

        elif t == "mouse_click":
            x = int(step.get("x", 0))
            y = int(step.get("y", 0))
            btn = step.get("button", "left")
            pyautogui.click(x, y, button=btn)

        # wait 和 key_repeat 本身已控制時間，其餘步驟補上預設間隔
        if t not in ("wait", "key_repeat", "key_hold"):
            self._sleep(key_pause)

    # ── 工具方法 ──────────────────────────────────────────────────

    def _sleep(self, seconds):
        """可中斷的 sleep，每 50ms 檢查一次 running 旗標"""
        end = time.time() + seconds
        while time.time() < end and self.running:
            time.sleep(0.05)

    def _notify(self, loop, total, step, total_steps, msg):
        if total == 0:
            loop_txt = f"第 {loop} 輪（無限）"
        elif loop == 0:
            loop_txt = ""
        else:
            loop_txt = f"第 {loop}/{total} 輪"
        if step:
            prefix = f"{loop_txt}  ▶  " if loop_txt else ""
            self.status_text = f"{prefix}步驟 {step}/{total_steps}：{msg}"
        else:
            self.status_text = msg
        if self.on_status:
            self.on_status(loop, total, step, total_steps, msg)

    def _finish(self, cancelled):
        self.status_text = "已停止" if cancelled else "執行完成 ✓"
        self.running = False
        if self.on_finished:
            self.on_finished(cancelled)

    def _step_desc(self, step):
        t = step.get("type", "")
        if t == "wait":
            return f"等待 {step.get('seconds', 1)} 秒"
        if t == "key_press":
            return f"按鍵 [{step.get('key', '')}]"
        if t == "key_hold":
            return f"按住 [{step.get('key', '')}] {step.get('duration', 1)} 秒"
        if t == "key_repeat":
            d_min = step.get("delay_min", step.get("interval", 0.5))
            d_max = step.get("delay_max", step.get("interval", 0.5))
            interval_str = (f"{d_min}~{d_max}" if d_min != d_max
                            else str(step.get("interval", 0.5)))
            return f"連按 [{step.get('key', '')}] × {step.get('count', 1)} 次，間隔 {interval_str} 秒"
        if t == "key_hotkey":
            return f"組合鍵 [{' + '.join(step.get('keys', []))}]"
        if t == "type_text":
            text = step.get("text", "")
            preview = text[:25] + "..." if len(text) > 25 else text
            return f"輸入文字 \"{preview}\""
        if t == "mouse_click":
            btn_map = {"left": "左鍵", "right": "右鍵", "middle": "中鍵"}
            return (f"滑鼠點擊 {btn_map.get(step.get('button','left'),'左鍵')} "
                    f"({step.get('x',0)}, {step.get('y',0)})")
        return t
