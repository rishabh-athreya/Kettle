#!/usr/bin/env python3
"""
Minimal pop_widget.py: Shows the widget when VS Code is open, hides it when closed.
No Slack or code processing logic.
"""

import time
import tkinter as tk
import psutil
import dashboard
import subprocess

class PopWidget:
    def __init__(self):
        self.widget = None
        self.vscode_running = False
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        self.check_interval = 2.0  # seconds

    def is_vscode_running(self):
        try:
            script = '''
            tell application "System Events"
                set visibleApps to name of every process whose visible is true
                return visibleApps
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and ("Electron" in result.stdout or "Code" in result.stdout):
                return True
            else:
                return False
        except Exception:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if "Code" in proc.info['name']:
                        if proc.info['name'] == "Code Helper" or proc.info['name'] == "Code Helper (Renderer)":
                            continue
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False

    def check_vscode_status(self):
        vscode_running = self.is_vscode_running()
        if vscode_running and not self.vscode_running:
            self.show_widget()
        elif not vscode_running and self.vscode_running:
            self.hide_widget()
        self.vscode_running = vscode_running

    def show_widget(self):
        if self.widget is None:
            self.widget = dashboard.KettleWidget(parent=self.root)
            print("Widget shown (VS Code open)")

    def hide_widget(self):
        if self.widget:
            try:
                self.widget.root.quit()
            except:
                pass
            self.widget = None
            print("Widget hidden (VS Code closed)")

    def periodic_check(self):
        self.check_vscode_status()
        self.root.after(int(self.check_interval * 1000), self.periodic_check)

    def run(self):
        print("PopWidget running: will show/hide widget based on VS Code visibility.")
        self.root.after(1000, self.periodic_check)
        self.root.mainloop()

if __name__ == "__main__":
    PopWidget().run() 