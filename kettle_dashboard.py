import sys
import tkinter as tk
from tkinter import ttk
import json
import os

DASHBOARD_WIDTH = 350
DASHBOARD_HEIGHT = 300
CIRCLE_DIAMETER = 60

PHASED_TASKS_PATH = os.path.join("json", "phased_tasks.json")

class KettleDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kettle Dashboard")
        self.overrideredirect(True)  # Remove window decorations
        self.attributes("-topmost", True)
        # Make the window background transparent (platform-specific)
        if sys.platform == "darwin":
            self.attributes("-transparent", True)
            self.config(bg='systemTransparent')
        elif sys.platform == "win32":
            self.wm_attributes("-transparentcolor", "#f7f7f8")
            self.config(bg="#f7f7f8")
        else:
            self.config(bg="#f7f7f8")
        self.expanded = False
        self.geometry(self._circle_geometry())
        self._place_bottom_right()
        self._draw_circle()
        self.bind("<Button-1>", self.toggle_expand)
        self.summary_frame = None

    def _place_bottom_right(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - CIRCLE_DIAMETER - 20
        y = screen_height - CIRCLE_DIAMETER - 60
        self.geometry(f"{CIRCLE_DIAMETER}x{CIRCLE_DIAMETER}+{x}+{y}")

    def _circle_geometry(self):
        return f"{CIRCLE_DIAMETER}x{CIRCLE_DIAMETER}"

    def _rectangle_geometry(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - DASHBOARD_WIDTH - 20
        y = screen_height - DASHBOARD_HEIGHT - 60
        return f"{DASHBOARD_WIDTH}x{DASHBOARD_HEIGHT}+{x}+{y}"

    def _draw_circle(self):
        if hasattr(self, 'canvas'):
            self.canvas.destroy()
        # Use a transparent background for the canvas
        self.canvas = tk.Canvas(self, width=CIRCLE_DIAMETER, height=CIRCLE_DIAMETER, highlightthickness=0, bg="systemTransparent" if sys.platform == "darwin" else "#f7f7f8")
        self.canvas.pack()
        self.circle = self.canvas.create_oval(2, 2, CIRCLE_DIAMETER-2, CIRCLE_DIAMETER-2, fill="#22232A", outline="")
        self.canvas.create_text(CIRCLE_DIAMETER//2, CIRCLE_DIAMETER//2, text="K", fill="white", font=("Arial", 28, "bold"))

    def toggle_expand(self, event=None):
        if not self.expanded:
            self.expanded = True
            self.geometry(self._rectangle_geometry())
            self.canvas.pack_forget()
            self._show_summary()
        else:
            self.expanded = False
            self.geometry(self._circle_geometry())
            self._place_bottom_right()
            if self.summary_frame:
                self.summary_frame.destroy()
            self._draw_circle()

    def _show_summary(self):
        self.summary_frame = tk.Frame(self, bg="#f7f7f8")
        self.summary_frame.pack(fill="both", expand=True)
        title = tk.Label(self.summary_frame, text="Kettle: Latest Work", font=("Arial", 14, "bold"), bg="#f7f7f8", fg="#333")
        title.pack(pady=(10, 5))
        tasks = self._load_tasks()
        if not tasks:
            tk.Label(self.summary_frame, text="No recent tasks.", bg="#f7f7f8").pack(pady=10)
            return
        for t in tasks:
            task_text = f"• {t['task']}"
            source_text = f"  (from: {t['source']})"
            task_label = tk.Label(self.summary_frame, text=task_text, anchor="w", justify="left", wraplength=DASHBOARD_WIDTH-40, bg="#f7f7f8", fg="#222")
            task_label.pack(fill="x", padx=15, pady=(6,0))
            source_label = tk.Label(self.summary_frame, text=source_text, anchor="w", justify="left", wraplength=DASHBOARD_WIDTH-40, bg="#f7f7f8", fg="#888", font=("Arial", 9, "italic"))
            source_label.pack(fill="x", padx=25, pady=(0,2))
        close_btn = ttk.Button(self.summary_frame, text="Minimize", command=self.toggle_expand)
        close_btn.pack(pady=10)

    def _load_tasks(self):
        try:
            with open(PHASED_TASKS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return []

def show_dashboard():
    app = KettleDashboard()
    app.mainloop()

if __name__ == "__main__":
    show_dashboard() 