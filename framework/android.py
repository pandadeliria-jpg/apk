#!/usr/bin/env python3
"""
Android Framework Stubs
Essential Android classes for running Roblox
"""
import os
import sys
import json
import time
import random
import hashlib
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'graphics'))

from interpreter import JavaObject, JavaArray
from resources import Resources, R
from activity_manager import ActivityManager, Intent, ActivityState


class Context:
    """android.content.Context stub."""
    
    MODE_PRIVATE = 0x0000
    MODE_WORLD_READABLE = 0x0001
    MODE_WORLD_WRITEABLE = 0x0002
    
    _global_context = None
    
    def __init__(self, package_name: str = None):
        self.package_name = package_name or "com.android.app"
        self.files_dir = os.path.expanduser(f"~/.android_compat/files/{self.package_name}")
        self.cache_dir = os.path.expanduser("~/.android_compat/cache")
        self.prefs_dir = os.path.expanduser("~/.android_compat/shared_prefs")
        
        os.makedirs(self.files_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.prefs_dir, exist_ok=True)
        
        self._resources = None
        self._package_manager = None
        self._activity_manager = None
        
        Context._global_context = self
    
    @classmethod
    def get_global(cls):
        """Get global context instance."""
        return cls._global_context
    
    def getPackageName(self) -> str:
        return self.package_name
    
    def getFilesDir(self) -> str:
        return self.files_dir
    
    def getCacheDir(self) -> str:
        return self.cache_dir
    
    def openFileInput(self, name: str):
        path = os.path.join(self.files_dir, name)
        return open(path, 'rb')
    
    def openFileOutput(self, name: str, mode: int):
        path = os.path.join(self.files_dir, name)
        return open(path, 'wb')
    
    def getSharedPreferences(self, name: str, mode: int):
        return SharedPreferences(os.path.join(self.prefs_dir, f"{name}.xml"))
    
    def getResources(self):
        if self._resources is None:
            self._resources = Resources()
        return self._resources
    
    def getActivityManager(self):
        if self._activity_manager is None:
            self._activity_manager = ActivityManager()
            self._activity_manager.system_context = self
        return self._activity_manager
    
    def getAssets(self):
        """Get asset manager."""
        return Assets()
    
    def getSystemService(self, name: str):
        """Get system service by name."""
        if name == 'activity':
            return self.getActivityManager()
        elif name == 'package':
            return self.getPackageManager()
        return None
    
    def getPackageManager(self):
        if self._package_manager is None:
            self._package_manager = PackageManager()
        return self._package_manager
    
    def getSystemService(self, name: str):
        """Get system service."""
        services = {
            'activity': ActivityManager(),
            'window': WindowManager(),
            'input_method': InputMethodManager(),
            'connectivity': ConnectivityManager(),
            'wifi': WifiManager(),
            'sensor': SensorManager(),
            'location': LocationManager(),
            'notification': NotificationManager(),
            'alarm': AlarmManager(),
            'power': PowerManager(),
            'storage': StorageManager(),
            'telephony': TelephonyManager(),
        }
        return services.get(name)


class Resources:
    """android.content.res.Resources stub."""
    
    def __init__(self):
        self.strings = {}
        self.drawables = {}
    
    def getString(self, id: int) -> str:
        return self.strings.get(id, f"<string_{id}>")
    
    def getIdentifier(self, name: str, defType: str, defPackage: str) -> int:
        return hash(name) % 0x7FFFFFFF


class PackageManager:
    """android.content.pm.PackageManager stub."""
    
    def getPackageInfo(self, packageName: str, flags: int):
        return PackageInfo(packageName)


class PackageInfo:
    """android.content.pm.PackageInfo stub."""
    
    def __init__(self, package_name: str):
        self.packageName = package_name
        self.versionCode = 1
        self.versionName = "1.0.0"


class SharedPreferences:
    """android.content.SharedPreferences stub."""
    
    def __init__(self, path: str):
        self.path = path
        self.data = {}
        self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    self.data = json.load(f)
            except:
                pass
    
    def _save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f)
    
    def getString(self, key: str, default: str = None) -> str:
        return self.data.get(key, default)
    
    def getInt(self, key: str, default: int = 0) -> int:
        return self.data.get(key, default)
    
    def getBoolean(self, key: str, default: bool = False) -> bool:
        return self.data.get(key, default)
    
    def edit(self):
        return SharedPreferencesEditor(self)


class SharedPreferencesEditor:
    """android.content.SharedPreferences.Editor stub."""
    
    def __init__(self, prefs: SharedPreferences):
        self.prefs = prefs
        self.changes = {}
    
    def putString(self, key: str, value: str):
        self.changes[key] = value
        return self
    
    def putInt(self, key: str, value: int):
        self.changes[key] = value
        return self
    
    def putBoolean(self, key: str, value: bool):
        self.changes[key] = value
        return self
    
    def remove(self, key: str):
        self.changes[key] = None
        return self
    
    def apply(self):
        for k, v in self.changes.items():
            if v is None:
                self.prefs.data.pop(k, None)
            else:
                self.prefs.data[k] = v
        self.prefs._save()
    
    def commit(self) -> bool:
        self.apply()
        return True


class ActivityManager:
    """android.app.ActivityManager stub."""
    pass


class WindowManager:
    """android.view.WindowManager stub."""
    pass


class InputMethodManager:
    """android.view.inputmethod.InputMethodManager stub."""
    pass


class ConnectivityManager:
    """android.net.ConnectivityManager stub."""
    
    TYPE_WIFI = 1
    TYPE_MOBILE = 0
    
    def getActiveNetworkInfo(self):
        return NetworkInfo()


class NetworkInfo:
    """android.net.NetworkInfo stub."""
    
    def isConnected(self) -> bool:
        return True
    
    def getType(self) -> int:
        return ConnectivityManager.TYPE_WIFI


class WifiManager:
    """android.net.wifi.WifiManager stub."""
    pass


class SensorManager:
    """android.hardware.SensorManager stub."""
    pass


class LocationManager:
    """android.location.LocationManager stub."""
    pass


class NotificationManager:
    """android.app.NotificationManager stub."""
    pass


class AlarmManager:
    """android.app.AlarmManager stub."""
    pass


class PowerManager:
    """android.os.PowerManager stub."""
    pass


class StorageManager:
    """android.os.storage.StorageManager stub."""
    pass


class TelephonyManager:
    """android.telephony.TelephonyManager stub."""
    
    def getDeviceId(self) -> str:
        return "000000000000000"
    
    def getSubscriberId(self) -> str:
        return "310260000000000"


class Activity:
    """android.app.Activity stub."""
    
    def __init__(self):
        self.context = None
    
    def onCreate(self, savedInstanceState=None):
        """Activity lifecycle - called when activity is created."""
        pass
    
    def onStart(self):
        """Activity lifecycle - called when activity becomes visible."""
        pass
    
    def onResume(self):
        """Activity lifecycle - called when activity starts interacting."""
        pass
    
    def onPause(self):
        """Activity lifecycle - called when activity is pausing."""
        pass
    
    def onStop(self):
        """Activity lifecycle - called when activity is no longer visible."""
        pass
    
    def onDestroy(self):
        """Activity lifecycle - called when activity is being destroyed."""
        pass
    
    def setContentView(self, layoutResID):
        """Set the activity content from a layout resource."""
        print(f"[*] Activity content view set: {layoutResID}")
    
    def getApplicationContext(self):
        return self.context
    
    def runOnUiThread(self, action: Callable):
        """Run on UI thread."""
        action()


class Handler:
    """android.os.Handler stub."""
    
    def __init__(self, looper=None):
        self.looper = looper
    
    def post(self, runnable: Callable) -> bool:
        """Post runnable to handler."""
        runnable()
        return True
    
    def postDelayed(self, runnable: Callable, delayMillis: int) -> bool:
        """Post with delay."""
        import threading
        threading.Timer(delayMillis / 1000.0, runnable).start()
        return True


class Looper:
    """android.os.Looper stub."""
    
    @staticmethod
    def prepare():
        pass
    
    @staticmethod
    def loop():
        """Would block forever in real implementation."""
        pass
    
    @staticmethod
    def getMainLooper():
        return None


class Bundle:
    """android.os.Bundle stub."""
    
    def __init__(self):
        self.data = {}
    
    def putString(self, key: str, value: str):
        self.data[key] = value
    
    def getString(self, key: str) -> str:
        return self.data.get(key)
    
    def putInt(self, key: str, value: int):
        self.data[key] = value
    
    def getInt(self, key: str) -> int:
        return self.data.get(key, 0)


class Intent:
    """android.content.Intent stub."""
    
    def __init__(self, action: str = None, uri=None):
        self.action = action
        self.data = uri
        self.extras = Bundle()
    
    def putExtra(self, name: str, value):
        self.extras.data[name] = value
        return self
    
    def getStringExtra(self, name: str) -> str:
        return self.extras.data.get(name)


class Uri:
    """android.net.Uri stub."""
    
    @staticmethod
    def parse(uriString: str):
        return Uri(uriString)


class WebView:
    """android.webkit.WebView stub."""
    
    def __init__(self, context: Context):
        self.context = context
        self.url = ""
        self.settings = WebSettings()
    
    def loadUrl(self, url: str):
        self.url = url
        print(f"[*] WebView.loadUrl({url})")
    
    def getSettings(self):
        return self.settings
    
    def setWebViewClient(self, client):
        pass
    
    def setWebChromeClient(self, client):
        pass


class WebSettings:
    """android.webkit.WebSettings stub."""
    
    def setJavaScriptEnabled(self, enabled: bool):
        pass


class Toast:
    """android.widget.Toast stub."""
    
    LENGTH_SHORT = 0
    LENGTH_LONG = 1
    
    @staticmethod
    def makeText(context: Context, text: str, duration: int):
        print(f"[Toast] {text}")
        return Toast()
    
    def show(self):
        pass


# Export common classes
__all__ = [
    'Context', 'Activity', 'Resources', 'SharedPreferences',
    'Handler', 'Looper', 'Bundle', 'Intent', 'Uri',
    'View', 'WebView', 'Toast',
    'ConnectivityManager', 'NetworkInfo',
]
