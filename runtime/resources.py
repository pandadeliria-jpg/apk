#!/usr/bin/env python3
"""
Android Resource Loader
Parses resources.arsc and provides R.java-like access
"""
import os
import struct
import zipfile
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import IntEnum


class ResourceType(IntEnum):
    """Android resource types."""
    ANIM = 0x01
    ANIMATOR = 0x02
    ARRAY = 0x03
    ATTR = 0x04
    BOOL = 0x05
    COLOR = 0x06
    DIMEN = 0x07
    DRAWABLE = 0x08
    FONT = 0x09
    FRACTION = 0x0a
    ID = 0x0b
    INTEGER = 0x0c
    INTERPOLATOR = 0x0d
    LAYOUT = 0x0e
    MENU = 0x0f
    MIPMAP = 0x10
    NAVIGATION = 0x11
    PLURALS = 0x12
    RAW = 0x13
    STRING = 0x14
    STYLE = 0x15
    STYLEABLE = 0x16
    TRANSITION = 0x17
    XML = 0x18


@dataclass
class ResourceEntry:
    """Single resource entry."""
    entry_id: int
    name: str
    value: Any = None
    config: str = ""
    type_name: str = ""


@dataclass
class ResourceTypeSpec:
    """Resource type specification."""
    type_id: int
    name: str
    entry_count: int
    entries: Dict[int, ResourceEntry] = field(default_factory=dict)


class Resources:
    """
    Android Resources implementation.
    Parses resources.arsc from APK and provides access like R.java.
    """
    
    def __init__(self):
        self.package_name: str = ""
        self.types: Dict[str, ResourceTypeSpec] = {}
        self.id_to_name: Dict[int, Tuple[str, str]] = {}  # id -> (type, name)
        self.name_to_id: Dict[str, Dict[str, int]] = {}  # type -> {name -> id}
        self.strings: Dict[int, str] = {}
        self.values: Dict[Tuple[str, str, str], Any] = {}  # (type, name, config) -> value
        self.assets: Dict[str, bytes] = {}  # asset path -> data
    
    def load_from_apk(self, apk_path: str) -> bool:
        """Load resources from APK file."""
        print(f"[*] Loading resources from APK: {apk_path}")
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                # Load resources.arsc if exists
                if 'resources.arsc' in zf.namelist():
                    arsc_data = zf.read('resources.arsc')
                    self._parse_resources_arsc(arsc_data)
                else:
                    print("[!] No resources.arsc in APK")
                
                # Load assets
                for name in zf.namelist():
                    if name.startswith('assets/'):
                        self.assets[name] = zf.read(name)
                
                if self.assets:
                    print(f"[*] Loaded {len(self.assets)} assets")
        
        except Exception as e:
            print(f"[!] Failed to load resources: {e}")
            return False
        
        print(f"[+] Resources loaded: {len(self.types)} types, {len(self.id_to_name)} IDs")
        return True
    
    def _parse_resources_arsc(self, data: bytes):
        """Parse resources.arsc binary XML."""
        # This is a simplified parser - full ARSC parsing is complex
        # Just extract what we can
        
        # Header
        if len(data) < 12:
            return
        
        chunk_type = struct.unpack('<H', data[0:2])[0]
        header_size = struct.unpack('<H', data[2:4])[0]
        chunk_size = struct.unpack('<I', data[4:8])[0]
        
        if chunk_type != 0x0002:  # RES_TABLE_TYPE
            print(f"[!] Invalid resources.arsc header: {hex(chunk_type)}")
            return
        
        package_count = struct.unpack('<I', data[8:12])[0]
        
        # For now, create some dummy resource mappings
        # Real implementation would parse the full structure
        self._create_dummy_resources()
    
    def _create_dummy_resources(self):
        """Create basic resource mappings for common types."""
        # Layout resources
        self.name_to_id['layout'] = {
            'main': 0x7f030000,
            'activity_main': 0x7f030001,
        }
        
        # String resources
        self.name_to_id['string'] = {
            'app_name': 0x7f040000,
            'hello': 0x7f040001,
        }
        
        # Drawable resources
        self.name_to_id['drawable'] = {
            'ic_launcher': 0x7f050000,
            'icon': 0x7f050001,
        }
        
        # ID resources
        self.name_to_id['id'] = {
            'content': 0x1020002,  # android.R.id.content
            'button1': 0x7f060000,
            'text1': 0x7f060001,
        }
        
        # Build reverse mapping
        for type_name, names in self.name_to_id.items():
            for name, resid in names.items():
                self.id_to_name[resid] = (type_name, name)
    
    def getIdentifier(self, name: str, defType: str, defPackage: str = "") -> int:
        """
        Get resource identifier by name.
        Like Resources.getIdentifier() in Android.
        """
        if defType in self.name_to_id:
            return self.name_to_id[defType].get(name, 0)
        return 0
    
    def getString(self, id: int) -> str:
        """Get string resource by ID."""
        if id in self.strings:
            return self.strings[id]
        
        # Check mapping
        if id in self.id_to_name:
            type_name, res_name = self.id_to_name[id]
            if type_name == 'string':
                return f"@{res_name}"
        
        return ""
    
    def getText(self, id: int) -> str:
        """Get text resource."""
        return self.getString(id)
    
    def getDrawable(self, id: int) -> Any:
        """Get drawable resource."""
        # Return placeholder
        return {'type': 'drawable', 'id': id}
    
    def getLayout(self, id: int) -> Any:
        """Get layout resource."""
        return {'type': 'layout', 'id': id}
    
    def getColor(self, id: int) -> int:
        """Get color resource."""
        return 0xFF000000  # Default black
    
    def getDimension(self, id: int) -> float:
        """Get dimension resource."""
        return 0.0
    
    def getInteger(self, id: int) -> int:
        """Get integer resource."""
        return 0
    
    def getBoolean(self, id: int) -> bool:
        """Get boolean resource."""
        return False
    
    def getResourceEntryName(self, resid: int) -> str:
        """Get entry name for resource ID."""
        if resid in self.id_to_name:
            return self.id_to_name[resid][1]
        return ""
    
    def getResourceName(self, resid: int) -> str:
        """Get full resource name."""
        if resid in self.id_to_name:
            type_name, entry_name = self.id_to_name[resid]
            return f"{self.package_name}:{type_name}/{entry_name}"
        return ""
    
    def getResourceTypeName(self, resid: int) -> str:
        """Get type name for resource ID."""
        if resid in self.id_to_name:
            return self.id_to_name[resid][0]
        return ""
    
    def openRawResource(self, id: int) -> bytes:
        """Open raw resource by ID."""
        name = self.getResourceEntryName(id)
        for asset_path, data in self.assets.items():
            if name in asset_path:
                return data
        return b''
    
    def openAsset(self, fileName: str) -> Optional[bytes]:
        """Open asset file."""
        path = f"assets/{fileName}"
        return self.assets.get(path)
    
    def listAssets(self, path: str = "") -> List[str]:
        """List assets in given path."""
        prefix = f"assets/{path}"
        results = []
        for asset_path in self.assets:
            if asset_path.startswith(prefix):
                results.append(asset_path[len(prefix):].lstrip('/'))
        return results
    
    def dump(self):
        """Dump resource information."""
        print(f"\n=== Resources ===")
        print(f"Package: {self.package_name}")
        print(f"Types: {list(self.name_to_id.keys())}")
        print(f"Assets: {len(self.assets)}")
        
        for type_name, names in self.name_to_id.items():
            print(f"\n{type_name}:")
            for name, resid in names.items():
                print(f"  0x{resid:08x} = {name}")


class R:
    """
    Generated R.java equivalent.
    Provides static access to resource IDs.
    """
    
    class attr:
        pass
    
    class drawable:
        pass
    
    class id:
        content = 0x1020002
    
    class layout:
        pass
    
    class string:
        pass
    
    class style:
        pass
    
    class color:
        pass
    
    class dimen:
        pass
    
    class raw:
        pass
    
    class anim:
        pass
    
    class array:
        pass
    
    @classmethod
    def init_from_resources(cls, resources: Resources):
        """Initialize R class from Resources instance."""
        for type_name, names in resources.name_to_id.items():
            type_class = getattr(cls, type_name, None)
            if type_class:
                for name, resid in names.items():
                    setattr(type_class, name, resid)


# Export
__all__ = ['Resources', 'R', 'ResourceType', 'ResourceEntry']
