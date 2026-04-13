#!/usr/bin/env python3
"""
Standalone GUI APK Installer Launcher
This is a simpler alternative that works reliably on macOS
"""
import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

# Get paths
COMPAT_DIR = Path("/Users/danuta/robloxgen/android_compat")
if not COMPAT_DIR.exists():
    COMPAT_DIR = Path.home() / "robloxgen/android_compat"

class APKInstallerGUI:
    def __init__(self, apk_path=None):
        self.apk_path = apk_path
        self.root = tk.Tk()
        self.root.title("APK Installer")
        self.root.geometry("600x500")
        self.root.resizable(True, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (300)
        y = (self.root.winfo_screenheight() // 2) - (250)
        self.root.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        # If APK provided, start installation
        if self.apk_path:
            self.root.after(500, self.start_install)
    
    def setup_ui(self):
        # Title
        tk.Label(self.root, text="📱 APK Installer", 
                font=("Helvetica", 24, "bold")).pack(pady=20)
        
        # File selection frame
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=10, padx=30, fill=tk.X)
        
        tk.Label(file_frame, text="APK File:", font=("Helvetica", 12)).pack(side=tk.LEFT)
        
        self.file_entry = tk.Entry(file_frame, width=35, font=("Helvetica", 11))
        self.file_entry.pack(side=tk.LEFT, padx=5)
        
        if self.apk_path:
            self.file_entry.insert(0, self.apk_path)
        
        tk.Button(file_frame, text="Browse...", command=self.browse_file,
                 font=("Helvetica", 10)).pack(side=tk.LEFT)
        
        # Status
        tk.Label(self.root, text="Status", font=("Helvetica", 14, "bold")).pack(pady=(20, 5))
        
        self.status_label = tk.Label(self.root, text="Ready to install", 
                                    font=("Helvetica", 12), fg="gray")
        self.status_label.pack()
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=500, mode='determinate')
        self.progress.pack(pady=15)
        self.progress['value'] = 0
        
        # Log area
        tk.Label(self.root, text="Installation Log", font=("Helvetica", 12)).pack(pady=(10, 5))
        
        # Create text widget with scrollbar
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=5, padx=30, fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=10, width=60, state=tk.DISABLED,
                               bg="#f5f5f5", font=("Courier", 10),
                               wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        self.install_btn = tk.Button(btn_frame, text="▶ Install APK", 
                                    command=self.start_install,
                                    bg="#4CAF50", fg="white",
                                    font=("Helvetica", 14, "bold"),
                                    width=15, height=1)
        self.install_btn.pack(side=tk.LEFT, padx=5)
        
        self.run_btn = tk.Button(btn_frame, text="Install & Run", 
                                command=self.install_and_run,
                                bg="#2196F3", fg="white",
                                font=("Helvetica", 12),
                                width=12, height=1,
                                state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Close", command=self.root.quit,
                 font=("Helvetica", 12), width=10).pack(side=tk.LEFT, padx=5)
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select APK file",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")]
        )
        if filename:
            self.apk_path = filename
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def set_status(self, text, progress=None):
        self.status_label.config(text=text)
        if progress is not None:
            self.progress['value'] = progress
        self.root.update()
    
    def start_install(self):
        # Get path from entry
        self.apk_path = self.file_entry.get()
        
        if not self.apk_path or not os.path.isfile(self.apk_path):
            messagebox.showerror("Error", "Please select a valid APK file")
            return
        
        # Disable buttons
        self.install_btn.config(state=tk.DISABLED)
        self.run_btn.config(state=tk.DISABLED)
        
        # Start in thread
        thread = threading.Thread(target=self._install_thread)
        thread.daemon = True
        thread.start()
    
    def _install_thread(self):
        try:
            self.set_status("Starting installation...", 10)
            self.log(f"[*] Installing: {os.path.basename(self.apk_path)}")
            
            # Run installer
            self.set_status("Installing APK...", 40)
            
            cmd = ['python3', str(COMPAT_DIR / 'run_apk.py'), 
                   self.apk_path, '--install']
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=str(COMPAT_DIR), text=True, bufsize=1
            )
            
            # Read output in real-time
            for line in iter(process.stdout.readline, ''):
                line = line.rstrip()
                if line:
                    self.log(line)
                    self.root.update()
            
            process.stdout.close()
            process.wait()
            
            if process.returncode == 0:
                self.set_status("✓ Installation complete!", 100)
                self.log("[+] Success!")
                self.run_btn.config(state=tk.NORMAL, command=self.run_app)
                messagebox.showinfo("Success", "APK installed successfully!")
            else:
                self.set_status("✗ Installation failed", 0)
                self.log("[!] Installation failed")
                self.install_btn.config(state=tk.NORMAL)
                
        except Exception as e:
            self.log(f"[!] Error: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.set_status("Error occurred", 0)
            self.install_btn.config(state=tk.NORMAL)
    
    def install_and_run(self):
        self.start_install()
        # Will run after install completes
    
    def run_app(self):
        try:
            import sys
            sys.path.insert(0, str(COMPAT_DIR / 'runtime'))
            from app_manager import get_app_manager
            
            app_mgr = get_app_manager()
            for app in app_mgr.list_apps():
                if self.apk_path in str(app.apk_path):
                    self.log(f"[*] Running {app.package_name}...")
                    subprocess.Popen([
                        'python3', str(COMPAT_DIR / 'run_apk.py'),
                        '--run', app.package_name
                    ], cwd=str(COMPAT_DIR))
                    self.log("[+] App launched!")
                    return
            
            self.log("[!] Could not find installed app to run")
        except Exception as e:
            self.log(f"[!] Error running app: {e}")
    
    def run(self):
        self.root.mainloop()

def main():
    # Get APK from command line if provided
    apk_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    app = APKInstallerGUI(apk_path)
    app.run()

if __name__ == "__main__":
    main()
