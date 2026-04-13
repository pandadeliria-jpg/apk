#!/usr/bin/env python3
"""
DEX Method Executor
Executes methods from parsed DEX files with full framework support
"""
import os
import sys
import zipfile
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

from interpreter import Interpreter, JavaObject, Frame, JNIEnvironment
from class_data import ClassDataParser, EncodedMethod


@dataclass
class LoadedClass:
    """Runtime representation of loaded class."""
    name: str
    class_def: Any
    data_item: Any = None
    methods: Dict[str, EncodedMethod] = field(default_factory=dict)
    static_fields: Dict[str, Any] = field(default_factory=dict)
    instance_fields: List[str] = field(default_factory=list)
    superclass: str = "Ljava/lang/Object;"


class MethodExecutor:
    """
    Executes methods from DEX files.
    Bridges DEX parsing → Bytecode execution
    """
    
    def __init__(self, dex_loader, apk_path: str = None):
        self.dex = dex_loader
        self.apk_path = apk_path
        self.interpreter = Interpreter(dex_loader)
        self.loaded_classes: Dict[str, LoadedClass] = {}
        self.jni = JNIEnvironment()
        
        # Native libraries
        self.native_libs: Dict[str, Any] = {}
        self.native_lib_manager = None
        
        # Resources
        self.resources = None
        
        # Initialize JNI
        self._init_jni()
        
        # Load APK resources if provided
        if apk_path:
            self._load_apk_resources(apk_path)
    
    def _init_jni(self):
        """Initialize JNI with framework bindings."""
        # Add framework imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))
        
        try:
            from android import Context, Activity, Handler, Looper
            from activity_manager import ActivityManager, Intent
            from resources import Resources, R
            
            # Register framework classes
            self.framework_classes = {
                'android/content/Context': Context,
                'android/app/Activity': Activity,
                'android/os/Handler': Handler,
                'android/os/Looper': Looper,
                'android/content/Intent': Intent,
            }
            print(f"[*] Framework loaded: {len(self.framework_classes)} classes")
        except Exception as e:
            print(f"[!] Failed to load framework: {e}")
            self.framework_classes = {}
    
    def _load_apk_resources(self, apk_path: str):
        """Load resources and native libs from APK."""
        sys.path.insert(0, os.path.dirname(__file__))
        from resources import Resources, R
        from elf_loader import NativeLibraryManager
        
        # Load resources
        self.resources = Resources()
        self.resources.load_from_apk(apk_path)
        R.init_from_resources(self.resources)
        
        # Extract and load native libraries
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                # Find native libs
                lib_files = [n for n in zf.namelist() if 'lib/arm64-v8a/' in n and n.endswith('.so')]
                if lib_files:
                    print(f"[*] Found {len(lib_files)} native libraries")
                    
                    # Create temp dir for libs
                    import tempfile
                    lib_dir = tempfile.mkdtemp()
                    
                    # Create data directory for bootstrap extraction
                    data_dir = os.path.join(os.path.dirname(apk_path), 'data')
                    os.makedirs(data_dir, exist_ok=True)
                    
                    # Extract and load
                    self.native_lib_manager = NativeLibraryManager()
                    self.native_lib_manager.set_native_path(lib_dir)
                    
                    for lib_file in lib_files:
                        lib_name = os.path.basename(lib_file)
                        zf.extract(lib_file, lib_dir)
                        lib_path = os.path.join(lib_dir, lib_file)
                        
                        # Check if this is a valid ELF or a ZIP (bootstrap)
                        with open(lib_path, 'rb') as f:
                            magic = f.read(4)
                        
                        if magic == b'PK\x03\x04':  # ZIP file (bootstrap)
                            print(f"[*] Extracting bootstrap: {lib_name}")
                            bootstrap_dir = os.path.join(data_dir, 'usr')
                            os.makedirs(bootstrap_dir, exist_ok=True)
                            with zipfile.ZipFile(lib_path, 'r') as bootstrap_zip:
                                bootstrap_zip.extractall(bootstrap_dir)
                            print(f"[+] Bootstrap extracted to {bootstrap_dir}")
                        elif magic == b'\x7fELF':  # Valid ELF
                            self.native_lib_manager.load_library(lib_name)
                        else:
                            print(f"[!] Unknown file type for {lib_name}: {magic.hex()}")
        except Exception as e:
            print(f"[!] Failed to load native libs: {e}")
    
    def call_native_method(self, class_name: str, method_name: str, *args) -> Any:
        """Call a method via JNI/native binding."""
        jni_key = f"{class_name}.{method_name}"
        
        # Check native libraries first
        if self.native_lib_manager:
            for lib_name in self.native_lib_manager.loaded_libs:
                result = self.native_lib_manager.call_function(lib_name, method_name, *args)
                if result is not None:
                    return result
        
        # Check for framework class
        if class_name in self.framework_classes:
            clazz = self.framework_classes[class_name]
            method = getattr(clazz, method_name, None)
            if method and callable(method):
                return method(*args)
        
        # Check JNI registration
        return self.jni.call(jni_key, *args)
    
    def load_all_classes(self):
        """Load all classes from DEX file."""
        if not self.dex or not self.dex.class_defs:
            print("[!] No DEX loaded")
            return False
        
        print(f"[*] Loading {len(self.dex.class_defs)} classes...")
        
        for class_def in self.dex.class_defs:
            class_name = self.dex.types[class_def.class_idx]
            
            loaded = LoadedClass(
                name=class_name,
                class_def=class_def,
                superclass=self.dex.types[class_def.superclass_idx] if class_def.superclass_idx < len(self.dex.types) else "Ljava/lang/Object;"
            )
            
            # Load class data if available
            if hasattr(self.dex, 'class_data_items') and class_name in self.dex.class_data_items:
                data_item = self.dex.class_data_items[class_name]
                loaded.data_item = data_item
                
                # Index methods
                for method in data_item.direct_methods + data_item.virtual_methods:
                    full_name = f"{class_name}.{method.name}{method.proto_desc}"
                    loaded.methods[method.name] = method
                    
            self.loaded_classes[class_name] = loaded
        
        print(f"[+] Loaded {len(self.loaded_classes)} classes")
        return True
    
    def find_method(self, class_name: str, method_name: str) -> Optional[EncodedMethod]:
        """Find method by class and name."""
        if class_name in self.loaded_classes:
            clazz = self.loaded_classes[class_name]
            if method_name in clazz.methods:
                return clazz.methods[method_name]
        return None
    
    def find_main_method(self) -> Optional[tuple]:
        """Find main(String[]) method in loaded classes."""
        for class_name, clazz in self.loaded_classes.items():
            for method_name, method in clazz.methods.items():
                # Check for main method
                if method_name == "main":
                    # Verify signature
                    if "([Ljava/lang/String;)V" in method.proto_desc or "V" == method.proto_desc[-1]:
                        return (class_name, method)
        return None
    
    def execute_method(self, class_name: str, method_name: str, args: List[Any] = None) -> Any:
        """Execute a method by name."""
        method = self.find_method(class_name, method_name)
        
        if not method:
            print(f"[!] Method not found: {class_name}.{method_name}")
            return None
        
        if not method.code_item:
            print(f"[!] No code for {class_name}.{method_name}")
            return None
        
        print(f"[*] Executing: {class_name}.{method_name}")
        print(f"    Signature: {method.proto_desc}")
        print(f"    Access: {hex(method.access_flags)}")
        print(f"    Code size: {len(method.code_item.insns)} bytes")
        
        # Execute via interpreter
        bytecode = method.code_item.get_bytecode()
        
        try:
            result = self.interpreter.execute_method(
                f"{class_name}.{method_name}",
                bytecode,
                args
            )
            return result
        except Exception as e:
            print(f"[!] Execution error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def execute_main(self, args: List[str] = None) -> bool:
        """Execute main method."""
        main_info = self.find_main_method()
        
        if not main_info:
            print("[!] No main() method found")
            print("[*] Available classes:")
            for name in list(self.loaded_classes.keys())[:10]:
                clazz = self.loaded_classes[name]
                methods = list(clazz.methods.keys())
                if methods:
                    print(f"    {name}: {methods[:5]}")
            return False
        
        class_name, method = main_info
        print(f"[*] Found main: {class_name}.main")
        
        # Execute
        result = self.execute_method(class_name, "main", [args or []])
        return result is not None
    
    def call_native_method(self, class_name: str, method_name: str, *args) -> Any:
        """Call a method via JNI/native binding."""
        # Check for framework class
        if class_name in self.framework_classes:
            clazz = self.framework_classes[class_name]
            
            # Get method
            method = getattr(clazz, method_name, None)
            if method and callable(method):
                return method(*args)
            
        # Check for registered JNI method
        jni_key = f"{class_name}.{method_name}"
        return self.jni.call(jni_key, *args)
    
    def list_classes(self) -> List[str]:
        """List all loaded classes."""
        return list(self.loaded_classes.keys())
    
    def list_methods(self, class_name: str) -> List[str]:
        """List methods in a class."""
        if class_name in self.loaded_classes:
            return list(self.loaded_classes[class_name].methods.keys())
        return []


class AndroidRuntime:
    """
    Complete Android Runtime for macOS.
    Orchestrates DEX loading, class loading, and execution.
    """
    
    def __init__(self):
        self.executors: Dict[str, MethodExecutor] = {}  # dex_path -> executor
        self.system_properties = {
            'ro.product.model': 'MacBookPro',
            'ro.product.brand': 'Apple',
            'ro.product.name': 'android_compat',
            'ro.build.version.sdk': '33',
            'ro.build.version.release': '13',
            'ro.build.id': 'android_compat_1.0',
        }
        self.context = None
        
    def initialize(self, package_name: str = None):
        """Initialize runtime."""
        print("=" * 60)
        print("Android→macOS Compatibility Layer")
        print("=" * 60)
        print()
        print("[*] Initializing runtime...")
        
        # Setup system properties
        for key, value in self.system_properties.items():
            print(f"    {key}={value}")
        
        # Initialize framework
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))
        try:
            from android import Context
            self.context = Context(package_name=package_name)
            print(f"[*] Android Context created for {package_name or 'default'}")
        except Exception as e:
            print(f"[!] Failed to create Context: {e}")
        
        print("[+] Runtime initialized")
        print()
        return True
    
    def load_dex(self, dex_path: str, apk_path: str = None) -> bool:
        """Load a DEX file (with optional APK for resources)."""
        from dex_interpreter import DEXLoader
        
        print(f"[*] Loading DEX: {dex_path}")
        
        try:
            loader = DEXLoader(dex_path)
            if not loader.load():
                print("[!] Failed to load DEX")
                return False
            
            # Create executor with APK path for resources
            executor = MethodExecutor(loader, apk_path=apk_path)
            executor.load_all_classes()
            
            self.executors[dex_path] = executor
            print(f"[+] DEX loaded and ready")
            return True
            
        except Exception as e:
            print(f"[!] Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def launch_activity(self, class_name: str = None, dex_path: str = None) -> bool:
        """Launch an activity using Android lifecycle."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))
        from activity_manager import ActivityManager, Intent
        
        # Find executor
        executor = self.get_executor(dex_path)
        if not executor:
            print("[!] No DEX loaded")
            return False
        
        # Create real activity manager (not the stub)
        am = ActivityManager()
        if self.context:
            am.system_context = self.context
        
        # Register all loaded Activity classes
        for loaded_class in executor.loaded_classes.values():
            # Check if it's an Activity subclass
            if 'Activity' in loaded_class.name and not '$' in loaded_class.name:
                # Try to find or create Python class
                try:
                    from android import Activity
                    # Create a dynamic subclass
                    class DynamicActivity(Activity):
                        def __init__(self):
                            super().__init__()
                            self._loaded_class = loaded_class
                        
                        def onCreate(self, savedInstanceState=None):
                            print(f"[*] {loaded_class.name}.onCreate() called")
                            # Could call DEX methods here if implemented
                    
                    # Register with ActivityManager
                    am.register_activity_class(loaded_class.name, DynamicActivity)
                except Exception as e:
                    print(f"[!] Failed to register activity {loaded_class.name}: {e}")
        
        # Find main activity if not specified
        if not class_name:
            for name in executor.loaded_classes.keys():
                if 'MainActivity' in name or 'Launcher' in name:
                    class_name = name
                    break
        
        if not class_name:
            print("[!] No activity class found")
            return False
        
        # Create intent and start activity
        intent = Intent()
        intent.setClassName(self.context.getPackageName(), class_name)
        intent.setAction(ActivityManager.ACTION_MAIN)
        intent.addCategory(ActivityManager.CATEGORY_LAUNCHER)
        
        print(f"[*] Launching activity: {class_name}")
        return am.startActivity(intent)
    
    def dump_activities(self):
        """Dump activity stack."""
        # Activity stack is managed separately - print basic info
        print("[*] Activity stack dump not yet implemented")
    
    def get_activity_count(self) -> int:
        """Get number of running activities."""
        if self.context:
            am = self.context.getActivityManager()
            if am:
                return am.getActivityCount()
        return 0
    
    def execute(self, class_name: str = None, method_name: str = None, 
                dex_path: str = None, args: List[str] = None) -> Any:
        """Execute a method or main."""
        # Find executor
        if dex_path and dex_path in self.executors:
            executor = self.executors[dex_path]
        elif self.executors:
            executor = list(self.executors.values())[0]
        else:
            print("[!] No DEX loaded")
            return None
        
        # Execute specific method or main
        if class_name and method_name:
            return executor.execute_method(class_name, method_name, args)
        else:
            return executor.execute_main(args)
    
    def get_executor(self, dex_path: str = None) -> Optional[MethodExecutor]:
        """Get executor for DEX."""
        if dex_path:
            return self.executors.get(dex_path)
        elif self.executors:
            return list(self.executors.values())[0]
        return None


# Global runtime instance
_global_runtime = None

def get_runtime():
    """Get or create global runtime."""
    global _global_runtime
    if _global_runtime is None:
        _global_runtime = AndroidRuntime()
        _global_runtime.initialize()
    return _global_runtime
