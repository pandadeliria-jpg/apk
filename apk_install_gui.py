#!/usr/bin/env python3
"""
GUI APK Installer for macOS
Provides drag-and-drop and double-click installation with progress UI
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import zipfile

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'runtime'))

try:
    from app_manager import get_app_manager
except ImportError:
    print("[!] app_manager not available")
    get_app_manager = None


class APKInstallerGUI:
    def __init__(self, apk_path=None):
        self.apk_path = apk_path
        self.root = tk.Tk()
        self.root.title("APK Installer")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        # If APK path provided, start installation
        if self.apk_path:
            self.root.after(500, self.start_installation)
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="Android→macOS APK Installer",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # APK file frame
        self.file_frame = tk.Frame(self.root)
        self.file_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(self.file_frame, text="APK File:").pack(side=tk.LEFT)
        self.file_entry = tk.Entry(self.file_frame, width=40)
        self.file_entry.pack(side=tk.LEFT, padx=5)
        
        if self.apk_path:
            self.file_entry.insert(0, self.apk_path)
        
        browse_btn = tk.Button(self.file_frame, text="Browse...", command=self.browse_apk)
        browse_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_label = tk.Label(self.root, text="Ready to install", font=("Helvetica", 10))
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        # Status text
        self.status_text = tk.Text(self.root, height=6, width=50, state=tk.DISABLED)
        self.status_text.pack(pady=10)
        
        # Buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)
        
        self.install_btn = tk.Button(
            self.button_frame, 
            text="Install APK", 
            command=self.start_installation,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=15
        )
        self.install_btn.pack(side=tk.LEFT, padx=5)
        
        self.run_btn = tk.Button(
            self.button_frame,
            text="Run After Install",
            command=self.install_and_run,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 12),
            width=15,
            state=tk.DISABLED
        )
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = tk.Button(
            self.button_frame,
            text="Close",
            command=self.root.quit,
            width=10
        )
        self.close_btn.pack(side=tk.LEFT, padx=5)
    
    def browse_apk(self):
        filename = filedialog.askopenfilename(
            title="Select APK file",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")]
        )
        if filename:
            self.apk_path = filename
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
    
    def log(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
    
    def start_installation(self):
        if not self.apk_path:
            self.apk_path = self.file_entry.get()
        
        if not self.apk_path or not os.path.exists(self.apk_path):
            messagebox.showerror("Error", "Please select a valid APK file")
            return
        
        # Run in thread to keep UI responsive
        thread = threading.Thread(target=self._install)
        thread.daemon = True
        thread.start()
    
    def _install(self):
        self.install_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        
        try:
            self.log(f"[*] Installing: {os.path.basename(self.apk_path)}")
            self.progress_label.config(text="Reading APK...")
            self.progress_bar['value'] = 20
            
            # Check APK validity
            try:
                with zipfile.ZipFile(self.apk_path, 'r') as zf:
                    files = zf.namelist()
                    has_dex = any(f.endswith('.dex') for f in files)
                    if not has_dex:
                        self.log("[!] Warning: No DEX files found in APK")
            except Exception as e:
                self.log(f"[!] Invalid APK: {e}")
                messagebox.showerror("Error", f"Invalid APK file: {e}")
                return
            
            self.progress_label.config(text="Extracting APK...")
            self.progress_bar['value'] = 40
            
            # Use command line installer
            compat_dir = os.path.dirname(os.path.abspath(__file__))
            cmd = [
                'python3',
                os.path.join(compat_dir, 'run_apk.py'),
                self.apk_path,
                '--install'
            ]
            
            self.progress_label.config(text="Installing...")
            self.progress_bar['value'] = 60
            
            # Run installation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=compat_dir
            )
            
            self.progress_bar['value'] = 100
            
            # Parse output
            for line in result.stdout.split('\n'):
                if line.strip():
                    self.log(line)
            
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.log(line)
            
            # Check success
            if result.returncode == 0:
                self.progress_label.config(text="Installation complete!")
                self.log("[+] Installation successful")
                self.run_btn.config(state=tk.NORMAL)
                
                # Enable run button
                if get_app_manager:
                    app_mgr = get_app_manager()
                    # Find the app we just installed
                    for app in app_mgr.list_apps():
                        if self.apk_path in app.apk_path:
                            self.installed_package = app.package_name
                            self.run_btn.config(command=self._run_app)
                            break
                
                messagebox.showinfo("Success", "APK installed successfully!")
            else:
                self.progress_label.config(text="Installation failed")
                self.log("[!] Installation failed")
                messagebox.showerror("Error", "Installation failed. Check the log for details.")
                
        except Exception as e:
            self.log(f"[!] Error: {e}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("Error", f"Installation error: {e}")
        
        finally:
            self.install_btn.config(state=tk.NORMAL)
    
    def install_and_run(self):
        self.start_installation()
        self._run_app()
    
    def _run_app(self):
        if hasattr(self, 'installed_package'):
            compat_dir = os.path.dirname(os.path.abspath(__file__))
            cmd = [
                'python3',
                os.path.join(compat_dir, 'run_apk.py'),
                '--run',
                self.installed_package
            ]
            
            self.log(f"[*] Running {self.installed_package}...")
            
            # Run in new terminal
            subprocess.Popen(
                cmd,
                cwd=compat_dir
            )
            
            self.log("[+] App launched in new window")
    
    def run(self):
        self.root.mainloop()


def main():
    # Get APK path from command line if provided
    apk_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    app = APKInstallerGUI(apk_path)
    app.run()


if __name__ == "__main__":
    main()
