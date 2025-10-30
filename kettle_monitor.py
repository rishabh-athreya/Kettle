#!/usr/bin/env python3
"""
Kettle Monitor: Continuous Slack monitoring for web dashboard.
- Periodically checks Slack for new messages.
- Extracts tasks from new messages based on a silence window (no new messages for a configured duration).
- Continues Slack polling while extraction/analysis runs asynchronously.
- Designed to work with the web dashboard architecture.
"""

import os
import sys
import time
import json
import subprocess
import signal
import psutil
from datetime import datetime
import threading
import queue
import requests
import slack_fetch
import tools.extract_tasks as extract_tasks
import tools.dependency_analyzer as dependency_analyzer
import tools.project_matcher as project_matcher

# Import clear_json_files and call it at startup
from utils.json_utils import clear_json_files
clear_json_files()

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class KettleMonitor:
    def __init__(self):
        # Polling configuration
        self.poll_interval = 10.0          # seconds between Slack polls
        self.silence_seconds = 60.0        # required silence (no new messages) to trigger pipeline
        self.cooldown_after_run = 5.0      # seconds to wait after a run finishes

        # State
        self.last_slack_check = 0.0        # throttles Slack API calls
        self.last_processed_ts = 0.0       # last message ts incorporated by the pipeline
        self.last_new_message_ts = 0.0     # last observed newest message ts
        self.pipeline_running = False      # concurrency guard

        # Load last processed timestamp (don't reset - run continuously)
        self.load_last_processed_ts()
        self.last_new_message_ts = self.last_processed_ts
        self.running = True

        # Lock for safe updates
        self._lock = threading.Lock()

    def load_last_processed_ts(self):
        """Load the timestamp of the last processed message."""
        try:
            if os.path.exists("json/last_processed_ts.txt"):
                with open("json/last_processed_ts.txt", "r") as f:
                    self.last_processed_ts = float(f.read().strip())
        except (ValueError, FileNotFoundError):
            self.last_processed_ts = 0

    def _read_messages(self):
        try:
            with open("json/messages.json", "r") as f:
                return json.load(f).get("messages", [])
        except (IOError, json.JSONDecodeError):
            return []

    def _update_last_processed_ts(self, ts_val: float):
        self.last_processed_ts = ts_val
        with open("json/last_processed_ts.txt", "w") as f:
            f.write(str(self.last_processed_ts))

    def _maybe_start_pipeline(self, latest_ts: float):
        """Start the pipeline in a background thread if silence is satisfied and not already running."""
        now = time.time()
        silence_met = (now - self.last_new_message_ts) >= self.silence_seconds
        newer_than_processed = latest_ts > self.last_processed_ts

        if not silence_met:
            print(f"MONITOR - Silence not met ({now - self.last_new_message_ts:.1f}s < {self.silence_seconds}s); skipping run")
            return
        if not newer_than_processed:
            print("MONITOR - No newer messages than last processed; skipping run")
            return
        if self.pipeline_running:
            print("MONITOR - Pipeline already running; skipping run")
            return

        def _run_pipeline(snapshot_latest_ts: float):
            with self._lock:
                self.pipeline_running = True
            start_t = time.time()
            print("PIPELINE - Starting extract/analyze run...")
            batch_path = None
            try:
                # Snapshot current accumulated messages into batch.json and clear messages.json for next batch
                try:
                    with open("json/messages.json", "r") as f:
                        current_msgs = json.load(f).get("messages", [])
                except (IOError, json.JSONDecodeError):
                    current_msgs = []
                if current_msgs:
                    batch_path = "json/batch.json"
                    with open(batch_path, "w") as sf:
                        json.dump({"messages": current_msgs}, sf, indent=2)
                    # Clear original to let poller accumulate next batch
                    with open("json/messages.json", "w") as of:
                        json.dump({"messages": []}, of, indent=2)

                # 1) Extraction
                print("PIPELINE - Extracting tasks from messages (extract_tasks.main)...")
                extract_tasks.main()

                # 2) Dependency analysis (use categorized tasks when available)
                print("PIPELINE - Running dependency analysis...")
                try:
                    # Prefer combining coding/research tasks if present
                    try:
                        with open("json/coding_tasks.json", "r") as f:
                            coding_tasks = json.load(f)
                    except Exception:
                        coding_tasks = []
                    try:
                        with open("json/research_tasks.json", "r") as f:
                            research_tasks = json.load(f)
                    except Exception:
                        research_tasks = []
                    all_tasks = (coding_tasks or []) + (research_tasks or [])
                    if all_tasks:
                        dependency_analyzer.create_dependency_matrix(all_tasks)
                    else:
                        # Fallback: attempt to read phased_tasks (flat list)
                        try:
                            with open("json/phased_tasks.json", "r") as f:
                                phased = json.load(f)
                            if isinstance(phased, list):
                                dependency_analyzer.create_dependency_matrix(phased)
                        except Exception:
                            pass
                except Exception as dep_e:
                    print(f"PIPELINE - Dependency analysis error: {dep_e}")

                # 3) Optional: similar project lookup (informational)
                try:
                    closest_project, similarity = project_matcher.main()
                    if closest_project:
                        print(f"PIPELINE - Similar project: {closest_project} (sim={similarity:.2f})")
                except Exception as match_e:
                    print(f"PIPELINE - Project match error: {match_e}")

                # Mark processed watermark to the snapshot latest message
                self._update_last_processed_ts(snapshot_latest_ts)
                print("PIPELINE - Run complete")
            except Exception as e:
                print(f"PIPELINE - Run failed: {e}")
            finally:
                # Cleanup batch snapshot if created
                if batch_path and os.path.exists(batch_path):
                    try:
                        os.remove(batch_path)
                    except Exception:
                        pass
                dur = time.time() - start_t
                print(f"PIPELINE - Duration: {dur:.2f}s")
                with self._lock:
                    self.pipeline_running = False
                # brief cooldown before next eligibility check
                time.sleep(self.cooldown_after_run)

        # Launch background thread
        threading.Thread(target=_run_pipeline, args=(latest_ts,), daemon=True).start()

    def check_slack_messages(self):
        """Checks Slack for new messages and manages silence-gated pipeline triggering."""
        now = time.time()
        if now - self.last_slack_check < self.poll_interval:
            return

        print(f"MONITOR - Polling Slack (last check: {time.strftime('%H:%M:%S', time.localtime(self.last_slack_check))})")

        # Fetch new messages
        try:
            slack_fetch.main()
            self.last_slack_check = now
        except Exception as e:
            print(f"MONITOR - Slack fetch error: {e}")
            return

        # Inspect messages
        messages = self._read_messages()
        if not messages:
            print("MONITOR - No messages found")
            return

        latest_ts = max(float(m.get("ts", 0)) for m in messages)
        if latest_ts > self.last_new_message_ts:
            self.last_new_message_ts = latest_ts
            print(f"MONITOR - New message ts observed: {latest_ts}")

        # Decide whether to start the pipeline (non-blocking)
        self._maybe_start_pipeline(latest_ts)

    def run(self):
        """Main monitoring loop."""
        print("MONITOR - Starting Kettle Monitor...")
        print("MONITOR - Web dashboard http://localhost:3000")
        print(f"MONITOR - Poll interval: {self.poll_interval}s, Silence: {self.silence_seconds}s")
        print("MONITOR - Ctrl+C to stop")
        
        try:
            while self.running:
                self.check_slack_messages()
                time.sleep(1.0)  # fine-grained loop; throttling is handled internally
        except KeyboardInterrupt:
            print("MONITOR - Stopping Kettle Monitor...")
            self.running = False

def main():
    monitor = KettleMonitor()
    monitor.run()

if __name__ == "__main__":
    main() 