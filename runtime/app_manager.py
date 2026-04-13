#!/usr/bin/env python3
"""
Android App Manager - Persistent App Installation & Management
Manages installed Android apps like a package manager
"""
import os
import sys
import json
import shutil
import hashlib
import zipfile
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class InstalledApp:
    """Represents an installed Android application."""
    package_name: str
    app_name: str
    version_code: int
    version_name: str
    install_path: str
    data_path: str
    cache_path: str
    apk_path: str
    install_time: str
    last_launch: Optional[str] = None
    launch_count: int = 0
    main_activity: str = ""
    permissions: List[str] = field(default_factory=list)
    native_libs: List[str] = field(default_factory=list)
    dex_files: List[str] = field(default_factory=list)
    icon_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstalledApp':
        """Create from dictionary."""
        return cls(**data)


class AppManager:
    """
    Manages installed Android applications.
    Provides install, uninstall, launch, and data management.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize AppManager.
        
        Args:
            base_path: Base directory for app storage. Defaults to ~/.android_compat/apps
        """
        if base_path is None:
            base_path = os.path.expanduser("~/.android_compat/apps")
        
        self.base_path = Path(base_path)
        self.apps_dir = self.base_path / "installed"
        self.data_dir = self.base_path / "data"
        self.cache_dir = self.base_path / "cache"
        self.manifest_path = self.base_path / "apps.json"
        
        # Ensure directories exist
        self._init_directories()
        
        # Load app registry
        self.apps: Dict[str, InstalledApp] = {}
        self._load_manifest()
    
    def _init_directories(self):
        """Create necessary directories."""
        self.apps_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_manifest(self):
        """Load app registry from manifest file."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    data = json.load(f)
                    for pkg_name, app_data in data.items():
                        self.apps[pkg_name] = InstalledApp.from_dict(app_data)
                print(f"[*] Loaded {len(self.apps)} installed apps")
            except Exception as e:
                print(f"[!] Failed to load manifest: {e}")
    
    def _save_manifest(self):
        """Save app registry to manifest file."""
        data = {pkg: app.to_dict() for pkg, app in self.apps.items()}
        try:
            with open(self.manifest_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[!] Failed to save manifest: {e}")
    
    def install_apk(self, apk_path: str, app_name: Optional[str] = None) -> Optional[InstalledApp]:
        """
        Install an APK file.
        
        Args:
            apk_path: Path to APK file
            app_name: Optional display name for the app
            
        Returns:
            InstalledApp if successful, None otherwise
        """
        apk_path = Path(apk_path)
        
        if not apk_path.exists():
            print(f"[!] APK not found: {apk_path}")
            return None
        
        print(f"[*] Installing APK: {apk_path.name}")
        
        # Extract package info from APK
        package_name = None
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                # Try to read AndroidManifest.xml
                manifest_data = self._parse_manifest(zf)
                pkg = manifest_data.get('package', '')
                # Only use parsed package if it's valid (not unknown.package and not empty)
                if pkg and pkg != 'unknown.package' and '.' in pkg:
                    package_name = pkg
                version_code = manifest_data.get('versionCode', 1)
                version_name = manifest_data.get('versionName', '1.0')
                main_activity = manifest_data.get('mainActivity', '')
                permissions = manifest_data.get('permissions', [])
        except Exception as e:
            print(f"[!] Failed to parse APK manifest: {e}")
        
        # Fallback: use APK filename for package name
        if not package_name:
            # Convert filename to package-like name
            # e.g., "com.termux.apk" -> "com.termux"
            base_name = apk_path.stem
            
            # If filename looks like a package (has dots), use it directly
            if '.' in base_name and len(base_name.split('.')) >= 2:
                # Remove common suffixes but preserve dots
                package_name = base_name
                for suffix in ['-release', '-debug', '-signed', '-unsigned']:
                    package_name = package_name.replace(suffix, '')
                package_name = package_name.lower()
            else:
                # Convert filename to package-like name
                # e.g., "google-play-50-8-18.apk" -> "com.google.play"
                base_name = base_name.lower()
                # Try to detect common package patterns
                if 'google' in base_name and 'play' in base_name:
                    package_name = 'com.google.android.play'
                elif 'roblox' in base_name:
                    package_name = 'com.roblox.client'
                elif 'minecraft' in base_name:
                    package_name = 'com.mojang.minecraftpe'
                else:
                    # Convert to com.<name>.app format
                    clean_name = re.sub(r'[^a-z0-9]', '', base_name)[:20]
                    package_name = f"com.app.{clean_name}" if clean_name else f"com.app.{apk_path.stem[:20]}"
            
            version_code = 1
            version_name = '1.0'
            main_activity = ''
            permissions = []
        
        # Check if already installed
        if package_name in self.apps:
            print(f"[*] App already installed: {package_name}")
            print(f"    Use --force to reinstall")
            # TODO: Implement update logic
        
        # Create app directories
        app_install_dir = self.apps_dir / package_name
        app_data_dir = self.data_dir / package_name
        app_cache_dir = self.cache_dir / package_name
        
        # Remove existing installation if any
        if app_install_dir.exists():
            shutil.rmtree(app_install_dir)
        if app_data_dir.exists():
            shutil.rmtree(app_data_dir)
        if app_cache_dir.exists():
            shutil.rmtree(app_cache_dir)
        
        # Create fresh directories
        app_install_dir.mkdir(parents=True, exist_ok=True)
        app_data_dir.mkdir(parents=True, exist_ok=True)
        app_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy APK to installation directory
        installed_apk = app_install_dir / f"{package_name}.apk"
        shutil.copy2(apk_path, installed_apk)
        
        # Extract APK contents
        print(f"[*] Extracting APK contents...")
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                zf.extractall(app_install_dir)
        except Exception as e:
            print(f"[!] Failed to extract APK: {e}")
        
        # Find DEX files
        dex_files = [str(f.relative_to(app_install_dir)) 
                     for f in app_install_dir.glob('*.dex')]
        
        # Find native libraries
        native_libs = []
        lib_dir = app_install_dir / 'lib' / 'arm64-v8a'
        if lib_dir.exists():
            native_libs = [str(f.name) for f in lib_dir.glob('*.so')]
        
        # Find icon
        icon_path = None
        for icon_name in ['res/mipmap-xxxhdpi/ic_launcher.png', 
                          'res/mipmap-xxhdpi/ic_launcher.png',
                          'res/drawable/ic_launcher.png']:
            icon_file = app_install_dir / icon_name
            if icon_file.exists():
                icon_path = str(icon_file)
                break
        
        # Create app record
        app = InstalledApp(
            package_name=package_name,
            app_name=app_name or package_name.split('.')[-1].title(),
            version_code=version_code,
            version_name=version_name,
            install_path=str(app_install_dir),
            data_path=str(app_data_dir),
            cache_path=str(app_cache_dir),
            apk_path=str(installed_apk),
            install_time=datetime.now().isoformat(),
            main_activity=main_activity,
            permissions=permissions,
            native_libs=native_libs,
            dex_files=dex_files,
            icon_path=icon_path
        )
        
        # Add to registry
        self.apps[package_name] = app
        self._save_manifest()
        
        print(f"[+] App installed successfully!")
        print(f"    Package: {package_name}")
        print(f"    Version: {version_name} ({version_code})")
        print(f"    DEX files: {len(dex_files)}")
        print(f"    Native libs: {len(native_libs)}")
        if main_activity:
            print(f"    Main Activity: {main_activity}")
        
        return app
    
    def uninstall_app(self, package_name: str) -> bool:
        """
        Uninstall an app.
        
        Args:
            package_name: Package name of app to uninstall
            
        Returns:
            True if successful
        """
        if package_name not in self.apps:
            print(f"[!] App not installed: {package_name}")
            return False
        
        app = self.apps[package_name]
        
        print(f"[*] Uninstalling {package_name}...")
        
        # Remove directories
        try:
            if Path(app.install_path).exists():
                shutil.rmtree(app.install_path)
            if Path(app.data_path).exists():
                shutil.rmtree(app.data_path)
            if Path(app.cache_path).exists():
                shutil.rmtree(app.cache_path)
        except Exception as e:
            print(f"[!] Error removing files: {e}")
        
        # Remove from registry
        del self.apps[package_name]
        self._save_manifest()
        
        print(f"[+] {package_name} uninstalled")
        return True
    
    def get_app(self, package_name: str) -> Optional[InstalledApp]:
        """Get installed app by package name."""
        return self.apps.get(package_name)
    
    def list_apps(self) -> List[InstalledApp]:
        """List all installed apps."""
        return list(self.apps.values())
    
    def is_installed(self, package_name: str) -> bool:
        """Check if app is installed."""
        return package_name in self.apps
    
    def get_apk_path(self, package_name: str) -> Optional[str]:
        """Get path to installed APK."""
        app = self.apps.get(package_name)
        return app.apk_path if app else None
    
    def clear_data(self, package_name: str) -> bool:
        """Clear app data (not cache)."""
        app = self.apps.get(package_name)
        if not app:
            print(f"[!] App not installed: {package_name}")
            return False
        
        try:
            data_path = Path(app.data_path)
            if data_path.exists():
                shutil.rmtree(data_path)
                data_path.mkdir(parents=True, exist_ok=True)
            print(f"[+] Data cleared for {package_name}")
            return True
        except Exception as e:
            print(f"[!] Error clearing data: {e}")
            return False
    
    def clear_cache(self, package_name: str) -> bool:
        """Clear app cache."""
        app = self.apps.get(package_name)
        if not app:
            print(f"[!] App not installed: {package_name}")
            return False
        
        try:
            cache_path = Path(app.cache_path)
            if cache_path.exists():
                shutil.rmtree(cache_path)
                cache_path.mkdir(parents=True, exist_ok=True)
            print(f"[+] Cache cleared for {package_name}")
            return True
        except Exception as e:
            print(f"[!] Error clearing cache: {e}")
            return False
    
    def update_launch_stats(self, package_name: str):
        """Update app launch statistics."""
        if package_name in self.apps:
            app = self.apps[package_name]
            app.launch_count += 1
            app.last_launch = datetime.now().isoformat()
            self._save_manifest()
    
    def _parse_manifest(self, zf: zipfile.ZipFile) -> Dict[str, Any]:
        """Parse AndroidManifest.xml from APK."""
        result = {
            'package': 'unknown.package',
            'versionCode': 1,
            'versionName': '1.0',
            'mainActivity': '',
            'permissions': []
        }
        
        try:
            # Read manifest
            manifest_data = zf.read('AndroidManifest.xml')
            # Simple parsing - extract package name
            import re
            text = manifest_data.decode('utf-8', errors='ignore')
            
            # Extract package
            pkg_match = re.search(r'package="([^"]+)"', text)
            if pkg_match:
                result['package'] = pkg_match.group(1)
            
            # Extract version
            ver_match = re.search(r'android:versionCode="(\d+)"', text)
            if ver_match:
                result['versionCode'] = int(ver_match.group(1))
            
            ver_name_match = re.search(r'android:versionName="([^"]+)"', text)
            if ver_name_match:
                result['versionName'] = ver_name_match.group(1)
            
            # Extract main activity
            activity_match = re.search(r'<activity[^>]*android:name="\.([^"]+)"[^>]*>.*?<intent-filter>.*?<action[^>]*android:name="android\.intent\.action\.MAIN"', 
                                       text, re.DOTALL)
            if activity_match:
                result['mainActivity'] = activity_match.group(1)
            
            # Extract permissions
            perms = re.findall(r'<uses-permission[^>]*android:name="([^"]+)"', text)
            result['permissions'] = perms
            
        except Exception as e:
            print(f"[!] Manifest parsing error: {e}")
        
        return result
    
    def print_app_list(self):
        """Print formatted list of installed apps."""
        apps = self.list_apps()
        
        if not apps:
            print("\nNo apps installed.")
            print(f"Use: python3 run_apk.py --install <apk_file>")
            return
        
        print(f"\n=== Installed Apps ({len(apps)}) ===\n")
        
        for i, app in enumerate(apps, 1):
            print(f"{i}. {app.app_name}")
            print(f"   Package: {app.package_name}")
            print(f"   Version: {app.version_name} ({app.version_code})")
            print(f"   Path: {app.install_path}")
            print(f"   Launches: {app.launch_count}")
            if app.last_launch:
                print(f"   Last run: {app.last_launch}")
            print()


# Global instance
_app_manager: Optional[AppManager] = None

def get_app_manager() -> AppManager:
    """Get or create global AppManager instance."""
    global _app_manager
    if _app_manager is None:
        _app_manager = AppManager()
    return _app_manager


# Export
__all__ = ['AppManager', 'InstalledApp', 'get_app_manager']
