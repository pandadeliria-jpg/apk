#!/usr/bin/env python3
"""
APK Installer Launcher for macOS
Handles Apple Events properly when double-clicking APK files
"""
import sys
import os
import subprocess
import argparse

# Try to import PyObjC for proper Apple Event handling
try:
    from Foundation import NSAppleEventDescriptor
    from AppKit import NSApplication, NSApp
    HAS_PLOBJC = True
except ImportError:
    HAS_PLOBJC = False

# Global to store file path from Apple Event
_apk_file_path = None

def get_compat_dir():
    """Find the android_compat directory."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navigate to android_compat directory (parent of APK Installer.app)
    compat_dir = os.path.dirname(os.path.dirname(script_dir))
    
    # If we're in the app bundle structure, use known path
    if "APK Installer.app" in compat_dir:
        compat_dir = "/Users/danuta/robloxgen/android_compat"
    
    # Fallback locations
    if not os.path.isdir(compat_dir):
        home = os.path.expanduser("~")
        compat_dir = os.path.join(home, "robloxgen/android_compat")
    
    if not os.path.isdir(compat_dir):
        compat_dir = "/Users/danuta/robloxgen/android_compat"
    
    return compat_dir

def install_apk(apk_path):
    """Install the APK using the compatibility layer."""
    compat_dir = get_compat_dir()
    
    if not os.path.exists(apk_path):
        print(f"[!] APK file not found: {apk_path}")
        osascript_dialog(f"APK file not found:\n{apk_path}")
        return False
    
    # Confirmation dialog
    result = osascript_confirm(f"Install {os.path.basename(apk_path)}?")
    if not result:
        print("[*] User cancelled")
        return False
    
    # Open Terminal and run installer
    cmd = f'''tell application "Terminal"
    activate
    do script "cd \\"{compat_dir}\\" && echo \\"[*] Installing APK: {os.path.basename(apk_path)}\\" && python3 run_apk.py \\"{apk_path}\\" --install && echo \\\
