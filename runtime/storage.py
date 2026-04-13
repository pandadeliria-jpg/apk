#!/usr/bin/env python3
"""
Android Storage - Persistent App Data Management
Handles SharedPreferences, databases, files, and cache
"""
import os
import json
import sqlite3
import pickle
import hashlib
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


class SharedPreferences:
    """
    Android SharedPreferences implementation.
    Key-value storage for app settings and data.
    """
    
    def __init__(self, name: str, data_dir: str):
        self.name = name
        self.data_dir = Path(data_dir)
        self.prefs_dir = self.data_dir / "shared_prefs"
        self.prefs_dir.mkdir(parents=True, exist_ok=True)
        
        self.file_path = self.prefs_dir / f"{name}.xml"
        self.data: Dict[str, Any] = {}
        self._loaded = False
        
        self._load()
    
    def _load(self):
        """Load preferences from file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
                    self.data = json.load(f)
                self._loaded = True
            except Exception as e:
                print(f"[!] Error loading preferences: {e}")
                self.data = {}
    
    def _save(self):
        """Save preferences to file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving preferences: {e}")
    
    # === Getters ===
    
    def getString(self, key: str, defaultValue: str = "") -> str:
        """Get string value."""
        return self.data.get(key, defaultValue)
    
    def getInt(self, key: str, defaultValue: int = 0) -> int:
        """Get integer value."""
        val = self.data.get(key, defaultValue)
        return int(val) if val is not None else defaultValue
    
    def getLong(self, key: str, defaultValue: int = 0) -> int:
        """Get long value."""
        return self.getInt(key, defaultValue)
    
    def getFloat(self, key: str, defaultValue: float = 0.0) -> float:
        """Get float value."""
        val = self.data.get(key, defaultValue)
        return float(val) if val is not None else defaultValue
    
    def getBoolean(self, key: str, defaultValue: bool = False) -> bool:
        """Get boolean value."""
        val = self.data.get(key, defaultValue)
        return bool(val) if val is not None else defaultValue
    
    def getStringSet(self, key: str, defaultValue: Optional[set] = None) -> Optional[set]:
        """Get string set."""
        val = self.data.get(key)
        if val is None:
            return defaultValue
        return set(val) if isinstance(val, list) else val
    
    def contains(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.data
    
    def getAll(self) -> Dict[str, Any]:
        """Get all preferences."""
        return self.data.copy()
    
    # === Setters ===
    
    def edit(self) -> 'SharedPreferences.Editor':
        """Get editor for modifying preferences."""
        return SharedPreferences.Editor(self)
    
    class Editor:
        """Editor for batch preference changes."""
        
        def __init__(self, prefs: 'SharedPreferences'):
            self.prefs = prefs
            self.changes: Dict[str, Any] = {}
            self.removals: List[str] = []
        
        def putString(self, key: str, value: str) -> 'SharedPreferences.Editor':
            self.changes[key] = value
            return self
        
        def putInt(self, key: str, value: int) -> 'SharedPreferences.Editor':
            self.changes[key] = value
            return self
        
        def putLong(self, key: str, value: int) -> 'SharedPreferences.Editor':
            self.changes[key] = value
            return self
        
        def putFloat(self, key: str, value: float) -> 'SharedPreferences.Editor':
            self.changes[key] = value
            return self
        
        def putBoolean(self, key: str, value: bool) -> 'SharedPreferences.Editor':
            self.changes[key] = value
            return self
        
        def putStringSet(self, key: str, values: set) -> 'SharedPreferences.Editor':
            self.changes[key] = list(values)
            return self
        
        def remove(self, key: str) -> 'SharedPreferences.Editor':
            self.removals.append(key)
            return self
        
        def clear(self) -> 'SharedPreferences.Editor':
            self.removals.extend(self.prefs.data.keys())
            return self
        
        def commit(self) -> bool:
            """Apply changes synchronously."""
            for key in self.removals:
                self.prefs.data.pop(key, None)
            self.prefs.data.update(self.changes)
            self.prefs._save()
            return True
        
        def apply(self):
            """Apply changes asynchronously."""
            self.commit()


class AppStorage:
    """
    Manages all app storage: files, cache, databases, preferences.
    """
    
    def __init__(self, package_name: str, base_path: str):
        self.package_name = package_name
        self.base_path = Path(base_path)
        
        # Standard Android paths
        self.files_dir = self.base_path / "files"
        self.cache_dir = self.base_path / "cache"
        self.databases_dir = self.base_path / "databases"
        self.shared_prefs_dir = self.base_path / "shared_prefs"
        
        # Create directories
        self._init_directories()
        
        # Active preferences
        self._prefs: Dict[str, SharedPreferences] = {}
        self._databases: Dict[str, sqlite3.Connection] = {}
    
    def _init_directories(self):
        """Create storage directories."""
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.databases_dir.mkdir(parents=True, exist_ok=True)
        self.shared_prefs_dir.mkdir(parents=True, exist_ok=True)
    
    # === SharedPreferences ===
    
    def getSharedPreferences(self, name: str, mode: int = 0) -> SharedPreferences:
        """
        Get SharedPreferences instance.
        
        Args:
            name: Preference file name
            mode: Access mode (ignored)
        """
        if name not in self._prefs:
            self._prefs[name] = SharedPreferences(name, str(self.base_path))
        return self._prefs[name]
    
    def getDefaultSharedPreferences(self) -> SharedPreferences:
        """Get default SharedPreferences."""
        return self.getSharedPreferences(f"{self.package_name}_preferences")
    
    # === File Operations ===
    
    def openFileInput(self, name: str) -> Optional[bytes]:
        """Open file for reading."""
        file_path = self.files_dir / name
        if file_path.exists():
            with open(file_path, 'rb') as f:
                return f.read()
        return None
    
    def openFileOutput(self, name: str, mode: int = 0) -> 'FileOutputStream':
        """Open file for writing."""
        return FileOutputStream(self.files_dir / name)
    
    def deleteFile(self, name: str) -> bool:
        """Delete a file."""
        file_path = self.files_dir / name
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def fileList(self) -> List[str]:
        """List files in files directory."""
        return [f.name for f in self.files_dir.iterdir() if f.is_file()]
    
    def getFileStreamPath(self, name: str) -> str:
        """Get path to file."""
        return str(self.files_dir / name)
    
    # === Cache ===
    
    def getCacheDir(self) -> str:
        """Get cache directory path."""
        return str(self.cache_dir)
    
    def getCacheFile(self, name: str) -> str:
        """Get path to cache file."""
        return str(self.cache_dir / name)
    
    def clearCache(self):
        """Clear all cached files."""
        for f in self.cache_dir.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                import shutil
                shutil.rmtree(f)
    
    # === Database ===
    
    def openOrCreateDatabase(self, name: str, version: int = 1) -> sqlite3.Connection:
        """Open or create SQLite database."""
        if name not in self._databases:
            db_path = self.databases_dir / name
            self._databases[name] = sqlite3.connect(str(db_path))
        return self._databases[name]
    
    def deleteDatabase(self, name: str) -> bool:
        """Delete a database."""
        db_path = self.databases_dir / name
        if db_path.exists():
            if name in self._databases:
                self._databases[name].close()
                del self._databases[name]
            db_path.unlink()
            return True
        return False
    
    def databaseList(self) -> List[str]:
        """List databases."""
        return [f.name for f in self.databases_dir.iterdir() 
                if f.is_file() and f.suffix in ['.db', '.sqlite']]
    
    # === Data Storage ===
    
    def saveData(self, key: str, data: Any) -> bool:
        """Save arbitrary data using pickle."""
        try:
            data_path = self.files_dir / f"{key}.dat"
            with open(data_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"[!] Error saving data: {e}")
            return False
    
    def loadData(self, key: str) -> Optional[Any]:
        """Load pickled data."""
        try:
            data_path = self.files_dir / f"{key}.dat"
            if data_path.exists():
                with open(data_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"[!] Error loading data: {e}")
        return None
    
    # === JSON Storage ===
    
    def saveJson(self, key: str, data: dict) -> bool:
        """Save data as JSON."""
        try:
            json_path = self.files_dir / f"{key}.json"
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[!] Error saving JSON: {e}")
            return False
    
    def loadJson(self, key: str) -> Optional[dict]:
        """Load JSON data."""
        try:
            json_path = self.files_dir / f"{key}.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[!] Error loading JSON: {e}")
        return None
    
    # === Storage Stats ===
    
    def getTotalSize(self) -> int:
        """Get total storage size in bytes."""
        total = 0
        for path in [self.files_dir, self.cache_dir, self.databases_dir, self.shared_prefs_dir]:
            if path.exists():
                for f in path.rglob('*'):
                    if f.is_file():
                        total += f.stat().st_size
        return total
    
    def clearAll(self):
        """Clear all app storage."""
        for path in [self.files_dir, self.cache_dir, self.databases_dir, self.shared_prefs_dir]:
            if path.exists():
                for f in path.iterdir():
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        import shutil
                        shutil.rmtree(f)


class FileOutputStream:
    """File output stream for writing."""
    
    def __init__(self, path: Path):
        self.path = path
        self._file = None
    
    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.path, 'wb')
        return self
    
    def __exit__(self, *args):
        if self._file:
            self._file.close()
    
    def write(self, data: bytes):
        """Write bytes to file."""
        if self._file:
            self._file.write(data)
    
    def close(self):
        """Close the file."""
        if self._file:
            self._file.close()
            self._file = None


# Global storage registry
_storage_instances: Dict[str, AppStorage] = {}

def get_app_storage(package_name: str, base_path: str) -> AppStorage:
    """Get or create AppStorage for a package."""
    key = f"{package_name}:{base_path}"
    if key not in _storage_instances:
        _storage_instances[key] = AppStorage(package_name, base_path)
    return _storage_instances[key]


# Export
__all__ = ['AppStorage', 'SharedPreferences', 'FileOutputStream', 'get_app_storage']
