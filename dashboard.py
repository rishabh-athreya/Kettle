import tkinter as tk
from tkinter import ttk
import json
import os
import threading
import time
from datetime import datetime

class KettleWidget:
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(parent)
        self.root.title("Kettle AI")
        self.root.geometry("60x60")
        
        # Set transparent background for the window (macOS only)
        try:
            self.root.attributes('-transparent', True)
            self.root.configure(bg='systemTransparent')
        except tk.TclError:
            # Fallback for non-macOS or when transparency fails
            try:
                self.root.configure(bg='#000000')
            except:
                self.root.configure(bg='black')
        
        # Make window stay on top
        try:
            self.root.attributes('-topmost', True)
        except tk.TclError:
            pass
        
        # Remove window decorations
        try:
            self.root.overrideredirect(True)
        except tk.TclError:
            pass
        
        # Position at bottom right
        self.position_window()
        
        # Widget state
        self.expanded = False
        self.expanded_window = None
        
        # Create circular button
        self.create_widget()
        
        # Bind events
        self.root.bind('<Button-1>', self.toggle_expand)
        self.root.bind('<Escape>', self.close_widget)
        
        # Auto-hide after 5 seconds when expanded
        self.auto_hide_timer = None
        
    def position_window(self):
        """Position the widget at bottom right of screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Position at bottom right, accounting for macOS dock
        # A common dock height is around 80-100px.
        # We'll add a margin above that.
        widget_width = 60
        margin_x = 20  # Margin from the right edge
        margin_y = 100 # Margin from the bottom edge (to clear the dock)

        x = screen_width - widget_width - margin_x
        y = screen_height - widget_width - margin_y
        
        self.root.geometry(f"+{x}+{y}")
    
    def create_widget(self):
        """Create the circular widget button"""
        # Create circular canvas with transparent background
        try:
            canvas = tk.Canvas(self.root, width=60, height=60, bg='systemTransparent')
        except tk.TclError:
            # Fallback for non-macOS
            canvas = tk.Canvas(self.root, width=60, height=60, bg='#000000')
        
        canvas.configure(highlightthickness=0)
        canvas.pack()
        
        # Draw circular background with dark gray
        canvas.create_oval(5, 5, 55, 55, fill='#404040', outline='#404040')
        
        # Add "K" in white
        canvas.create_text(30, 30, text="K", font=('Arial', 24, 'bold'), fill='white')
        
        # Add hover effect
        def on_enter(e):
            canvas.create_oval(5, 5, 55, 55, fill='#505050', outline='#505050', tags='hover')
            canvas.create_text(30, 30, text="K", font=('Arial', 24, 'bold'), fill='white', tags='hover')
        
        def on_leave(e):
            canvas.delete('hover')
            canvas.create_oval(5, 5, 55, 55, fill='#404040', outline='#404040')
            canvas.create_text(30, 30, text="K", font=('Arial', 24, 'bold'), fill='white')
        
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        
        self.canvas = canvas
    
    def toggle_expand(self, event=None):
        """Toggle between collapsed and expanded states"""
        if self.expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """Expand the widget to show latest work"""
        self.expanded = True
        
        # Create expanded window
        self.expanded_window = tk.Toplevel(self.root)
        self.expanded_window.title("Kettle AI - Latest Work")
        self.expanded_window.geometry("400x500")
        self.expanded_window.configure(bg='#2b2b2b')
        self.expanded_window.attributes('-topmost', True)
        
        # Position next to the widget
        x = self.root.winfo_x() - 420
        y = self.root.winfo_y() - 440
        self.expanded_window.geometry(f"+{x}+{y}")
        
        # Create content
        self.create_expanded_content()
        
        # Start auto-hide timer
        self.auto_hide_timer = threading.Timer(5.0, self.collapse)
        self.auto_hide_timer.start()
    
    def create_expanded_content(self):
        """Create the content for the expanded widget"""
        # Header
        header_frame = tk.Frame(self.expanded_window, bg='#2b2b2b')
        header_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = tk.Label(header_frame, text="☕ Kettle AI", font=('Arial', 16, 'bold'), 
                              fg='white', bg='#2b2b2b')
        title_label.pack(side='left')
        
        close_btn = tk.Button(header_frame, text="×", font=('Arial', 16), 
                             command=self.collapse, bg='#2b2b2b', fg='white', 
                             bd=0)
        close_btn.configure(highlightthickness=0)
        close_btn.pack(side='right')
        
        # Content area
        content_frame = tk.Frame(self.expanded_window, bg='#2b2b2b')
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Load and display latest work
        self.load_latest_work(content_frame)
    
    def load_latest_work(self, parent):
        """Load and display the latest work from the system"""
        try:
            # Load latest messages
            messages = []
            if os.path.exists("json/messages.json"):
                with open("json/messages.json", "r") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
            
            # Load latest tasks
            tasks = []
            if os.path.exists("json/phased_tasks.json"):
                with open("json/phased_tasks.json", "r") as f:
                    tasks = json.load(f)
            
            # Create scrollable content
            canvas = tk.Canvas(parent, bg='#2b2b2b')
            canvas.configure(highlightthickness=0)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Latest Slack message
            if messages:
                latest_msg = messages[-1].get("text", "No message content")
                msg_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
                msg_frame.pack(fill='x', pady=(0, 10))
                
                tk.Label(msg_frame, text="Latest Slack Message:", font=('Arial', 12, 'bold'), 
                        fg='#0078d4', bg='#2b2b2b').pack(anchor='w')
                
                msg_text = tk.Text(msg_frame, height=3, wrap='word', bg='#3b3b3b', fg='white',
                                 insertbackground='white', relief='flat', padx=5, pady=5)
                msg_text.insert('1.0', latest_msg)
                msg_text.config(state='disabled')
                msg_text.pack(fill='x', pady=(5, 0))
            
            # Latest tasks
            if tasks:
                tasks_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
                tasks_frame.pack(fill='x', pady=(0, 10))
                
                tk.Label(tasks_frame, text="Extracted Tasks:", font=('Arial', 12, 'bold'), 
                        fg='#0078d4', bg='#2b2b2b').pack(anchor='w')
                
                for i, task in enumerate(tasks[:5]):  # Show first 5 tasks
                    task_frame = tk.Frame(tasks_frame, bg='#3b3b3b', relief='flat', bd=1)
                    task_frame.pack(fill='x', pady=2)
                    
                    phase_color = {
                        'project_setup': '#28a745',
                        'dependency_installation': '#ffc107',
                        'feature_implementation': '#17a2b8'
                    }.get(task.get('phase', ''), '#6c757d')
                    
                    phase_label = tk.Label(task_frame, text=f" {task.get('phase', 'unknown')} ", 
                                         bg=phase_color, fg='white', font=('Arial', 8))
                    phase_label.pack(side='left', padx=5, pady=5)
                    
                    task_text = tk.Label(task_frame, text=task.get('task', ''), 
                                       bg='#3b3b3b', fg='white', wraplength=300, justify='left')
                    task_text.pack(side='left', padx=5, pady=5, fill='x', expand=True)
            
            # Project info
            if os.path.exists("script.py"):
                project_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
                project_frame.pack(fill='x', pady=(0, 10))
                
                tk.Label(project_frame, text="Generated Script:", font=('Arial', 12, 'bold'), 
                        fg='#0078d4', bg='#2b2b2b').pack(anchor='w')
                
                script_info = tk.Label(project_frame, text="script.py has been generated and executed", 
                                     bg='#2b2b2b', fg='#28a745', font=('Arial', 10))
                script_info.pack(anchor='w', pady=(5, 0))
            
            # Status
            status_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
            status_frame.pack(fill='x', pady=(10, 0))
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_label = tk.Label(status_frame, text=f"Last updated: {timestamp}", 
                                  bg='#2b2b2b', fg='#6c757d', font=('Arial', 9))
            status_label.pack(anchor='w')
            
            # Pack scrollable elements
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
        except Exception as e:
            error_label = tk.Label(parent, text=f"Error loading data: {str(e)}", 
                                 bg='#2b2b2b', fg='#dc3545')
            error_label.pack(pady=20)
    
    def collapse(self):
        """Collapse the widget back to circular button"""
        self.expanded = False
        
        if self.auto_hide_timer:
            self.auto_hide_timer.cancel()
            self.auto_hide_timer = None
        
        if self.expanded_window:
            self.expanded_window.destroy()
            self.expanded_window = None
    
    def close_widget(self, event=None):
        """Close the entire widget"""
        if self.auto_hide_timer:
            self.auto_hide_timer.cancel()
        self.root.destroy()
    
    def refresh_content(self):
        """Refresh the widget content with latest data"""
        if self.expanded and self.expanded_window:
            try:
                # Clear existing content
                for widget in self.expanded_window.winfo_children():
                    widget.destroy()
                
                # Recreate content
                self.create_expanded_content()
                print("🔄 Widget content refreshed")
            except Exception as e:
                print(f"Error refreshing widget: {e}")
    
    def run(self):
        """Start the widget"""
        self.root.mainloop()

def start_dashboard():
    """Start the Kettle dashboard widget"""
    widget = KettleWidget()
    widget.run()

if __name__ == "__main__":
    start_dashboard() 