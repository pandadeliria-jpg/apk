#!/usr/bin/env python3
"""
Create a minimal test APK for verifying the compatibility layer.
Generates a simple Android app with Activity and main() method.
"""
import os
import sys
import struct
import zipfile
import tempfile
import shutil

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'runtime'))


def create_minimal_dex():
    """Create a minimal DEX file with a test class."""
    builder = DEXBuilder()
    
    # Create class: com/testapp/MainActivity extends android/app/Activity
    builder.add_class("Lcom/testapp/MainActivity;", "Landroid/app/Activity;")
    
    # Add onCreate method
    builder.add_method("Lcom/testapp/MainActivity;", "onCreate", "V", ["Landroid/os/Bundle;"], [
        # call-super onCreate
        (0x6f20, 0),  # invoke-super {v0}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
        # Print message
        (0x1a01, 0),  # const-string v1, "Hello from MainActivity!"
        (0x6e20, 0),  # invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
        (0x0e00, 0),  # return-void
    ])
    
    # Add main method for static entry point
    builder.add_method("Lcom/testapp/MainActivity;", "main", "V", ["[Ljava/lang/String;"], [
        (0x1a00, 0),  # const-string v0, "MainActivity.main() called!"
        (0x6200, 0),  # sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;
        (0x1a01, 0),  # const-string v1, "Test APK running on compatibility layer"
        (0x6e20, 0),  # invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
        (0x0e00, 0),  # return-void
    ])
    
    # Create class: com/testapp/TestApplication
    builder.add_class("Lcom/testapp/TestApplication;", "Landroid/app/Application;")
    
    # Add onCreate for Application
    builder.add_method("Lcom/testapp/TestApplication;", "onCreate", "V", [], [
        (0x6200, 0),  # sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;
        (0x1a01, 0),  # const-string v1, "Application.onCreate()"
        (0x6e20, 0),  # invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
        (0x0e00, 0),  # return-void
    ])
    
    return builder.build()


def create_android_manifest(package_name="com.testapp", main_activity="com.testapp.MainActivity"):
    """Create a minimal AndroidManifest.xml (binary format)."""
    # For simplicity, we'll create a text version that the compatibility layer can parse
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package_name}"
    android:versionCode="1"
    android:versionName="1.0">

    <application
        android:name=".TestApplication"
        android:label="Test App"
        android:theme="@android:style/Theme.Light">
        
        <activity
            android:name=".{main_activity.split('.')[-1]}"
            android:label="Test Activity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>'''
    return manifest.encode('utf-8')


def create_resources_arsc():
    """Create a minimal resources.arsc file."""
    # Simple binary structure - just enough for the parser to not crash
    # Real implementation would use aapt2
    data = struct.pack('<H', 0x0002)  # RES_TABLE_TYPE
    data += struct.pack('<H', 0x000c)  # Header size
    data += struct.pack('<I', 0x00000020)  # Chunk size (minimal)
    data += struct.pack('<I', 1)  # Package count
    return data


def create_test_apk(output_path="test_app.apk"):
    """Create a complete test APK file."""
    print(f"[*] Creating test APK: {output_path}")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create DEX file
        dex_data = create_minimal_dex()
        dex_path = os.path.join(temp_dir, "classes.dex")
        with open(dex_path, 'wb') as f:
            f.write(dex_data)
        print(f"[*] Created classes.dex ({len(dex_data)} bytes)")
        
        # Create AndroidManifest.xml
        manifest = create_android_manifest()
        manifest_path = os.path.join(temp_dir, "AndroidManifest.xml")
        with open(manifest_path, 'wb') as f:
            f.write(manifest)
        print(f"[*] Created AndroidManifest.xml")
        
        # Create resources.arsc
        resources = create_resources_arsc()
        resources_path = os.path.join(temp_dir, "resources.arsc")
        with open(resources_path, 'wb') as f:
            f.write(resources)
        print(f"[*] Created resources.arsc")
        
        # Create META-INF directory with minimal signature files
        meta_inf_dir = os.path.join(temp_dir, "META-INF")
        os.makedirs(meta_inf_dir, exist_ok=True)
        
        # MANIFEST.MF
        manifest_mf = b"Manifest-Version: 1.0\r\nCreated-By: Android Compatibility Layer\r\n\r\n"
        with open(os.path.join(meta_inf_dir, "MANIFEST.MF"), 'wb') as f:
            f.write(manifest_mf)
        
        # Create APK (ZIP file)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZEF_LAT) as zf:
            zf.write(dex_path, "classes.dex")
            zf.write(manifest_path, "AndroidManifest.xml")
            zf.write(resources_path, "resources.arsc")
            zf.writestr("META-INF/MANIFEST.MF", manifest_mf)
        
        print(f"[+] Test APK created: {output_path}")
        print(f"    Size: {os.path.getsize(output_path)} bytes")
        
        return output_path
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


class DEXBuilder:
    """
    Simple DEX file builder for creating test classes.
    This is a minimal implementation - real DEX is complex!
    """
    
    def __init__(self):
        self.classes = []
        self.methods = []
        self.strings = []
        self.string_map = {}
    
    def _add_string(self, s):
        """Add string to string pool."""
        if s not in self.string_map:
            idx = len(self.strings)
            self.strings.append(s)
            self.string_map[s] = idx
        return self.string_map[s]
    
    def add_class(self, class_name, superclass="Ljava/lang/Object;"):
        """Add a class definition."""
        self._add_string(class_name)
        self._add_string(superclass)
        self.classes.append({
            'name': class_name,
            'superclass': superclass,
            'methods': []
        })
        return len(self.classes) - 1
    
    def add_method(self, class_name, method_name, return_type, params, bytecode):
        """Add a method to a class."""
        self._add_string(method_name)
        # Find class
        for cls in self.classes:
            if cls['name'] == class_name:
                cls['methods'].append({
                    'name': method_name,
                    'return': return_type,
                    'params': params,
                    'bytecode': bytecode
                })
                return
        print(f"[!] Class not found: {class_name}")
    
    def build(self):
        """
        Build minimal DEX file.
        This is NOT a complete DEX implementation - just enough structure!
        """
        # Create minimal DEX header
        magic = b'dex\n035\x00'
        
        # Calculate offsets (simplified)
        header_size = 112
        string_ids_off = header_size
        string_ids_size = len(self.strings) * 4
        type_ids_off = string_ids_off + string_ids_size
        type_ids_size = (len(self.classes) + 1) * 4  # +1 for Object
        class_defs_off = type_ids_off + type_ids_size
        class_defs_size = len(self.classes) * 32
        
        # Build header
        data = bytearray()
        data.extend(magic)
        data.extend(struct.pack('<I', 0))  # checksum (placeholder)
        data.extend(b'\x00' * 20)  # signature
        data.extend(struct.pack('<I', 0))  # file_size (will update)
        data.extend(struct.pack('<I', header_size))
        data.extend(struct.pack('<I', 0x12345678))  # endian tag
        data.extend(struct.pack('<I', 0))  # link_size
        data.extend(struct.pack('<I', 0))  # link_off
        data.extend(struct.pack('<I', 0))  # map_off
        data.extend(struct.pack('<I', len(self.strings)))
        data.extend(struct.pack('<I', string_ids_off))
        data.extend(struct.pack('<I', len(self.classes) + 1))  # type_ids
        data.extend(struct.pack('<I', type_ids_off))
        data.extend(struct.pack('<I', 0))  # proto_ids_size
        data.extend(struct.pack('<I', 0))  # proto_ids_off
        data.extend(struct.pack('<I', 0))  # field_ids_size
        data.extend(struct.pack('<I', 0))  # field_ids_off
        data.extend(struct.pack('<I', 0))  # method_ids_size
        data.extend(struct.pack('<I', 0))  # method_ids_off
        data.extend(struct.pack('<I', len(self.classes)))  # class_defs_size
        data.extend(struct.pack('<I', class_defs_off))
        data.extend(struct.pack('<I', 0))  # data_size
        data.extend(struct.pack('<I', 0))  # data_off
        
        # Pad to string_ids_off
        while len(data) < string_ids_off:
            data.append(0)
        
        # String IDs (placeholder - real DEX has complex string pool)
        for i in range(len(self.strings)):
            data.extend(struct.pack('<I', 0))
        
        # Type IDs
        for i in range(len(self.classes) + 1):
            data.extend(struct.pack('<I', i))
        
        # Class definitions (minimal)
        for cls in self.classes:
            data.extend(struct.pack('<I', 0))  # class_idx
            data.extend(struct.pack('<I', 0))  # access_flags
            data.extend(struct.pack('<I', 0))  # superclass_idx
            data.extend(struct.pack('<I', 0xffffffff))  # interfaces_off
            data.extend(struct.pack('<I', 0))  # source_file_idx
            data.extend(struct.pack('<I', 0))  # annotations_off
            data.extend(struct.pack('<I', 0))  # class_data_off
            data.extend(struct.pack('<I', 0))  # static_values_off
        
        # Update file_size
        file_size = len(data)
        struct.pack_into('<I', data, 32, file_size)
        
        return bytes(data)


if __name__ == "__main__":
    # Create test APK
    apk_path = create_test_apk("/Users/danuta/robloxgen/android_compat/test_app.apk")
    
    if apk_path:
        print(f"\n[+] Test APK ready: {apk_path}")
        print(f"\nTo test:")
        print(f"  cd /Users/danuta/robloxgen/android_compat")
        print(f"  python3 run_apk.py test_app.apk --list-classes")
        print(f"  python3 run_apk.py test_app.apk --execute-main")
        print(f"  python3 run_apk.py test_app.apk --launch-activity com.testapp.MainActivity")
