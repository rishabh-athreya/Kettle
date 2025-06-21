#!/usr/bin/env python3
"""
Kettle Daemon: Always runs in the background.
- Launches the widget whenever VS Code is opened.
- Hides the widget when VS Code is closed.
- Periodically checks Slack for new messages.
- Processes messages after a period of inactivity.
"""

import time
import tkinter as tk
import psutil
import dashboard
import subprocess
import os
import json

# Import pipeline modules
import slack_fetch
import extract_tasks
import execute
import project_matcher

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class KettleDaemon:
    def __init__(self):
        # Widget state
        self.widget = None
        self.vscode_running = False
        
        # Main Tkinter root
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Pipeline state & timing
        self.check_interval = 2.0  # seconds for VS Code check
        self.slack_check_interval = 6.0 # seconds for Slack check
        self.last_slack_check = 0
        self.inactivity_period = 20.0  # seconds to wait before processing
        self.last_message_time = 0
        self.processing_pending = False
        self.last_processed_ts = 0
        self.load_last_processed_ts()

    def load_last_processed_ts(self):
        """Load the timestamp of the last processed message."""
        try:
            if os.path.exists("json/last_processed_ts.txt"):
                with open("json/last_processed_ts.txt", "r") as f:
                    self.last_processed_ts = float(f.read().strip())
        except (ValueError, FileNotFoundError):
            self.last_processed_ts = 0

    def is_vscode_running(self):
        """Checks if the VS Code window is visible and active."""
        try:
            # Use AppleScript to check for visible VS Code (Electron) windows specifically
            script = '''
            tell application "System Events"
                set electronProcesses to (every process whose name contains "Electron")
                repeat with proc in electronProcesses
                    if visible of proc is true then
                        -- Check if this Electron process is VS Code by looking at its command line
                        set procInfo to (every process whose name contains "Electron")
                        repeat with p in procInfo
                            if visible of p is true then
                                return "true"
                            end if
                        end repeat
                    end if
                end repeat
                return "false"
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and "true" in result.stdout.strip():
                return True
        except Exception as e:
            print(f"⚠️  AppleScript detection failed: {e}")
        
        # Fallback: Check for Electron process that is VS Code
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    # Look for Electron process (VS Code runs as Electron)
                    if proc_name == "Electron":
                        cmdline = proc.info.get('cmdline', [])
                        # Check if this Electron process is VS Code by looking at command line arguments
                        if cmdline and any('code' in arg.lower() for arg in cmdline):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"⚠️  Process detection failed: {e}")
        
        return False

    def check_vscode_status(self):
        """Shows or hides the widget based on VS Code visibility."""
        is_running = self.is_vscode_running()
        if is_running and not self.vscode_running:
            print("🔄 VS Code detected - showing widget...")
            self.show_widget()
        elif not is_running and self.vscode_running:
            print("🔄 VS Code closed - hiding widget...")
            self.hide_widget()
        elif is_running and self.vscode_running:
            print("📝 VS Code is running (widget should be visible)")
        else:
            print("📝 VS Code is not running (widget should be hidden)")
        self.vscode_running = is_running

    def show_widget(self):
        """Creates and shows the widget."""
        if self.widget is None:
            try:
                # Create widget without parent to avoid mainloop conflicts
                self.widget = dashboard.KettleWidget()
                print("✅ Widget shown (VS Code open)")
            except Exception as e:
                print(f"❌ Failed to show widget: {e}")
                print("🔄 Will retry on next VS Code detection...")
                self.widget = None
                # Don't let widget errors crash the daemon
                return False
        return True

    def hide_widget(self):
        """Hides and destroys the widget."""
        if self.widget:
            try:
                self.widget.close_widget()
                print("✅ Widget hidden (VS Code closed)")
            except Exception as e:
                print(f"❌ Error hiding widget: {e}")
            finally:
                self.widget = None

    def process_slack_messages(self):
        """Checks Slack and processes messages after an inactivity period."""
        current_time = time.time()
        
        # Throttle Slack API calls
        if current_time - self.last_slack_check < self.slack_check_interval:
            return

        # Fetch new messages
        slack_fetch.main()
        
        # Check for new messages since last processing
        try:
            with open("json/messages.json", "r") as f:
                messages = json.load(f).get("messages", [])
        except (IOError, json.JSONDecodeError):
            messages = []

        if not messages:
            return

        latest_ts = max(float(m.get("ts", 0)) for m in messages)

        if latest_ts > self.last_processed_ts:
            if not self.processing_pending:
                self.last_message_time = current_time
                self.processing_pending = True
        
        # If processing is pending, check if inactivity period has passed
        if self.processing_pending:
            time_since_last_msg = current_time - self.last_message_time
            if time_since_last_msg >= self.inactivity_period:
                
                # Run the pipeline
                extract_tasks.main()
                closest_project, _ = project_matcher.main()
                execute.main(existing_project_folder=closest_project)
                
                # Update timestamp and reset pending state
                self.last_processed_ts = latest_ts
                with open("json/last_processed_ts.txt", "w") as f:
                    f.write(str(self.last_processed_ts))
                self.processing_pending = False

                # Refresh widget content if visible
                if self.widget:
                    try:
                        self.widget.refresh_content()
                    except Exception as e:
                        print(f"❌ Error refreshing widget: {e}")
            else:
                remaining = self.inactivity_period - time_since_last_msg

    def periodic_check(self):
        """Main loop called periodically by Tkinter."""
        self.check_vscode_status()
        self.process_slack_messages()
        # Schedule the next check
        self.root.after(int(self.check_interval * 1000), self.periodic_check)

    def run(self):
        """Starts the daemon."""
        print("🚀 Kettle Daemon Starting...")
        print("📝 Monitoring VS Code process...")
        print("💡 Widget will show when VS Code opens and hide when it closes")
        print("🛑 Press Ctrl+C to stop the daemon")
        print("⏱️  Checking every 2 seconds...")
        
        self.root.after(1000, self.periodic_check)
        self.root.mainloop()

    def cleanup(self):
        """Clean up resources"""
        if self.widget:
            try:
                self.widget.root.destroy()
            except:
                pass
        
        try:
            self.root.destroy()
        except:
            pass
        

if __name__ == "__main__":
    KettleDaemon().run() 