import tkinter as tk
from datetime import datetime
import json
import os

# === Colour ===
COLORS = {
    "bg": "#000000",
    "focus": "#FFFFFF",
    "break_text": "#000000",
    "short_break_bg": "#00fff7",
    "long_break_bg": "#ff5100",
    "text_dim": "#4fb286",  # Accents for the 'QUANTA' header
    "icon": "#2c7764",
    "stats_card": "#1a1a1a",
    "button_dim": "#333333"
}

# === Timer Settings ===
# Alter these values to change duration in minutes
FOCUS_POMO = 45
SMALL_BREAK = 15
BIG_BREAK = 30

WORK_TIME = FOCUS_POMO * 60
SHORT_BREAK = SMALL_BREAK * 60
LONG_BREAK = BIG_BREAK * 60
DATA_FILE = "quanta_stats.json"  # Stores your session Data.

class QuantaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QUANTA")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg=COLORS["bg"])
        
        # State
        self.is_running = False
        self.time_left = WORK_TIME
        self.mode = "Focus" 
        self.sessions_count = 0
        self.timer_id = None
        self.stats_window = None

        self.load_data()
        self.setup_ui()
        self.update_display()

        # Bindings
        self.root.bind("<space>", lambda e: self.toggle())
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Right>", lambda e: self.skip())

    # --- File Handling ---
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f: 
                    self.all_data = json.load(f)
            except: 
                self.all_data = {}
        else:
            self.all_data = {}

    def save_data(self):
        with open(DATA_FILE, "w") as f: 
            json.dump(self.all_data, f, indent=4)

    def log_metric(self, key, value=1):
        date_key = datetime.now().strftime("%Y-%m-%d")
        if date_key not in self.all_data:
            self.all_data[date_key] = {
                "quanta_completed": 0, 
                "study_minutes": 0, 
                "breaks": 0, 
                "break_minutes": 0, 
                "interruptions": 0
            }
        
        if "minutes" in key: 
            self.all_data[date_key][key] += round(value / 60, 1)
        else: 
            self.all_data[date_key][key] += value
        self.save_data()

    # --- UI Setup ---
    def setup_ui(self):
        self.container = tk.Frame(self.root, bg=COLORS["bg"])
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        # Header: Q U A N T A
        self.header_label = tk.Label(
            self.container, 
            text="Q U A N T A", 
            font=("Helvetica Neue", 20, "bold"), 
            bg=COLORS["bg"], 
            fg=COLORS["text_dim"]
        )
        self.header_label.pack(pady=(0, 10))

        # Progression Dots
        self.dot_canvas = tk.Canvas(self.container, width=120, height=30, bg=COLORS["bg"], highlightthickness=0)
        self.dot_canvas.pack()

        # Main Timer
        self.time_label = tk.Label(
            self.container, 
            text=f"{FOCUS_POMO:02d}:00", 
            font=("Helvetica Neue", 160, "bold"), 
            bg=COLORS["bg"], 
            fg=COLORS["focus"]
        )
        self.time_label.pack(pady=10)

        # Control Icon
        self.btn_canvas = tk.Canvas(self.container, width=80, height=80, bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self.btn_canvas.pack(pady=20)
        self.btn_canvas.bind("<Button-1>", lambda e: self.toggle())
        self.draw_play()

        # Stats Toggle Button
        self.stats_toggle_btn = tk.Button(
            self.root, text="S T A T S", font=("Helvetica Neue", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["button_dim"], activebackground=COLORS["bg"],
            activeforeground=COLORS["focus"], relief="flat", borderwidth=0,
            command=self.toggle_stats_window, cursor="hand2"
        )
        self.stats_toggle_btn.place(relx=0.5, rely=0.9, anchor="center")

    # --- Analytics Logic ---
    def toggle_stats_window(self):
        if self.stats_window:
            self.hide_stats()
        else:
            self.show_stats()

    def show_stats(self):
        if self.stats_window: return
        self.stats_window = tk.Toplevel(self.root)
        self.stats_window.configure(bg=COLORS["bg"])
        self.stats_window.attributes('-topmost', True)
        self.stats_window.overrideredirect(True)
        self.stats_window.geometry("300x450+100+250") 

        tk.Label(self.stats_window, text="QUANTA LOG", font=("Helvetica Neue", 12, "bold"), bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(pady=20)

        date_key = datetime.now().strftime("%Y-%m-%d")
        data = self.all_data.get(date_key, {"quanta_completed":0, "study_minutes":0, "breaks":0, "break_minutes":0, "interruptions":0})
        
        metrics = [
            ("Total Quanta", data["quanta_completed"]), 
            ("Focus Time", f"{data['study_minutes']}m"), 
            ("Intervals", data["breaks"]), 
            ("Rest Time", f"{data['break_minutes']}m"), 
            ("Interruptions", data["interruptions"])
        ]

        for label, val in metrics:
            frame = tk.Frame(self.stats_window, bg=COLORS["stats_card"], padx=15, pady=10)
            frame.pack(fill="x", padx=20, pady=5)
            tk.Label(frame, text=label, font=("Helvetica Neue", 10), bg=COLORS["stats_card"], fg="#888888").pack(side="left")
            tk.Label(frame, text=val, font=("Helvetica Neue", 10, "bold"), bg=COLORS["stats_card"], fg="#FFFFFF").pack(side="right")

    def hide_stats(self):
        if self.stats_window:
            self.stats_window.destroy()
            self.stats_window = None

    # --- Timer Logic ---
    def toggle(self):
        self.is_running = not self.is_running
        if self.is_running:
            if self.mode == "Focus": self.hide_stats()
            self.draw_pause()
            self.tick()
        else:
            self.draw_play()
            if self.timer_id: self.root.after_cancel(self.timer_id)
            if self.mode == "Focus": self.log_metric("interruptions")
        self.update_display()

    def tick(self):
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            self.timer_id = self.root.after(1000, self.tick)
        elif self.time_left <= 0:
            self.finish_session()

    def finish_session(self):
        self.is_running = False
        if self.mode == "Focus":
            self.log_metric("quanta_completed")
            self.log_metric("study_minutes", WORK_TIME)
            self.sessions_count += 1
            self.mode = "Long Break" if self.sessions_count % 4 == 0 else "Short Break"
            self.time_left = LONG_BREAK if self.mode == "Long Break" else SHORT_BREAK
        else:
            dur = LONG_BREAK if self.mode == "Long Break" else SHORT_BREAK
            self.log_metric("breaks")
            self.log_metric("break_minutes", dur)
            self.mode = "Focus"
            self.time_left = WORK_TIME
        
        self.draw_play()
        self.update_display()

    def skip(self):
        if self.timer_id: self.root.after_cancel(self.timer_id)
        self.finish_session()

    def update_display(self):
        m, s = divmod(self.time_left, 60)
        
        if not self.is_running or self.mode != "Focus":
            self.stats_toggle_btn.place(relx=0.5, rely=0.9, anchor="center")
        else:
            self.stats_toggle_btn.place_forget()
            self.hide_stats()

        # Color Logic
        if self.mode == "Focus":
            current_bg, text_color, dot_inactive = COLORS["bg"], COLORS["focus"], "#1a1a1a"
            btn_fg = COLORS["button_dim"]
        elif self.mode == "Short Break":
            current_bg, text_color, dot_inactive = COLORS["short_break_bg"], COLORS["break_text"], "#99fcf9"
            btn_fg = COLORS["break_text"]
        else:
            current_bg, text_color, dot_inactive = COLORS["long_break_bg"], COLORS["break_text"], "#ff8c52"
            btn_fg = COLORS["break_text"]

        # Background Configuration
        self.root.configure(bg=current_bg)
        self.container.configure(bg=current_bg)
        self.header_label.configure(bg=current_bg)
        self.time_label.configure(bg=current_bg, fg=text_color, text=f"{m:02d}:{s:02d}")
        self.dot_canvas.configure(bg=current_bg)
        self.btn_canvas.configure(bg=current_bg)
        self.stats_toggle_btn.configure(bg=current_bg, fg=btn_fg, activebackground=current_bg)
        
        if self.is_running: self.draw_pause()
        else: self.draw_play()

        # Dots Progress
        self.dot_canvas.delete("all")
        idx = self.sessions_count % 4
        for i in range(4):
            x = 30 + (i * 20)
            d_color = COLORS["text_dim"] if i < idx else (text_color if i == idx and self.mode == "Focus" else dot_inactive)
            self.dot_canvas.create_oval(x-5, 10, x+5, 20, fill=d_color, outline="")

    def draw_play(self):
        self.btn_canvas.delete("all")
        color = COLORS["icon"] if self.mode == "Focus" else COLORS["break_text"]
        self.btn_canvas.create_polygon(30, 20, 30, 60, 60, 40, fill=color)

    def draw_pause(self):
        self.btn_canvas.delete("all")
        color = COLORS["icon"] if self.mode == "Focus" else COLORS["break_text"]
        self.btn_canvas.create_rectangle(30, 20, 38, 60, fill=color, outline="")
        self.btn_canvas.create_rectangle(45, 20, 53, 60, fill=color, outline="")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuantaApp(root)
    root.mainloop()