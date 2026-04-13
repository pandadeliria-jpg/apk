#!/usr/bin/env python3
"""
Android APK Runner - Working Compatibility Layer
Loads and executes Android APK on macOS
"""
import os
import sys
import argparse
import zipfile
import tempfile
import shutil

# Add runtime to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'runtime'))

from runtime.executor import AndroidRuntime, MethodExecutor
from dex_interpreter import DEXLoader


def extract_apk(apk_path, temp_dir):
    """Extract APK contents."""
    print(f"[*] Extracting APK: {apk_path}")
    
    with zipfile.ZipFile(apk_path, 'r') as zf:
        files = zf.namelist()
        print(f"[*] APK contains {len(files)} files")
        
        dex_files = [f for f in files if f.endswith('.dex')]
        print(f"[*] Found {len(dex_files)} DEX files")
        
        # Extract DEX files
        extracted = []
        for dex_name in dex_files:
            zf.extract(dex_name, temp_dir)
            extracted.append(os.path.join(temp_dir, dex_name))
        
        return extracted


def main():
    parser = argparse.ArgumentParser(
        description="Android→macOS Compatibility Layer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s app.apk --list-classes          # List all classes
  %(prog)s app.apk --execute-main           # Execute main() method
  %(prog)s app.apk --class Main --method run # Execute specific method
        """
    )
    parser.add_argument("apk", nargs="?", default="", help="Path to APK file (optional for --run, --list-apps, etc.)")
    parser.add_argument("--list-classes", action="store_true", help="List loaded classes")
    parser.add_argument("--list-methods", type=str, help="List methods in class")
    parser.add_argument("--execute-main", action="store_true", help="Execute main method")
    parser.add_argument("--class", dest="class_name", type=str, help="Class name to execute")
    parser.add_argument("--method", dest="method_name", type=str, help="Method name to execute")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument("--launch-activity", type=str, help="Launch specific activity class")
    
    # App management commands
    parser.add_argument("--install", action="store_true", help="Install APK to app library")
    parser.add_argument("--uninstall", type=str, help="Uninstall app by package name")
    parser.add_argument("--list-apps", action="store_true", help="List installed apps")
    parser.add_argument("--run", type=str, help="Run installed app by package name")
    parser.add_argument("--clear-data", type=str, help="Clear app data")
    parser.add_argument("--clear-cache", type=str, help="Clear app cache")
    
    args = parser.parse_args()
    
    # Management commands that don't need APK
    mgmt_commands = [args.list_apps, args.uninstall, args.clear_data, args.clear_cache, args.run]
    
    if not any(mgmt_commands):
        # These commands require an APK file
        if not os.path.exists(args.apk):
            print(f"[!] APK not found: {args.apk}")
            return 1
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Determine package name early for context initialization
        package_name = None
        if args.run:
            package_name = args.run
        elif args.apk and os.path.exists(args.apk):
            # Try to extract package from APK filename
            apk_base = os.path.basename(args.apk).replace('.apk', '')
            if '.' in apk_base:
                package_name = apk_base
        
        # Initialize runtime with package name
        runtime = AndroidRuntime()
        runtime.initialize(package_name=package_name)
        
        # App management commands (no APK needed)
        if args.list_apps:
            from runtime.app_manager import get_app_manager
            app_mgr = get_app_manager()
            app_mgr.print_app_list()
            return 0
        
        if args.uninstall:
            from runtime.app_manager import get_app_manager
            app_mgr = get_app_manager()
            if app_mgr.uninstall_app(args.uninstall):
                return 0
            return 1
        
        if args.clear_data:
            from runtime.app_manager import get_app_manager
            app_mgr = get_app_manager()
            if app_mgr.clear_data(args.clear_data):
                return 0
            return 1
        
        if args.clear_cache:
            from runtime.app_manager import get_app_manager
            app_mgr = get_app_manager()
            if app_mgr.clear_cache(args.clear_cache):
                return 0
            return 1
        
        # Commands that need APK extraction
        if args.install:
            from runtime.app_manager import get_app_manager
            app_mgr = get_app_manager()
            app = app_mgr.install_apk(args.apk)
            if app:
                print(f"\n[+] Installed: {app.app_name}")
                print(f"    Package: {app.package_name}")
                print(f"    Run with: python3 run_apk.py --run {app.package_name}")
            return 0 if app else 1
        
        # Handle --run before DEX extraction (uses installed app's DEX)
        if args.run:
            # Run installed app
            from runtime.app_manager import get_app_manager
            app_mgr = get_app_manager()
            app = app_mgr.get_app(args.run)
            
            if not app:
                print(f"[!] App not installed: {args.run}")
                print(f"    Install with: python3 run_apk.py <apk> --install")
                return 1
            
            print(f"\n[*] Running: {app.app_name}")
            print(f"    Package: {app.package_name}")
            print(f"    APK: {app.apk_path}")
            
            # Update launch stats
            app_mgr.update_launch_stats(args.run)
            
            # Load DEX from installed app
            for dex_file in app.dex_files:
                dex_path = os.path.join(app.install_path, dex_file)
                if os.path.exists(dex_path):
                    runtime.load_dex(dex_path, apk_path=app.apk_path)
            
            # Get executor after loading DEX
            executor = runtime.get_executor()
            
            # Find main activity - from manifest or auto-detect
            main_activity = app.main_activity
            if not main_activity and executor:
                # Auto-detect main activity from loaded classes
                # Priority: 1) Main/Launcher in name, 2) Package-specific activity, 3) First valid activity
                package_simple = app.package_name.split('.')[-1] if '.' in app.package_name else app.package_name
                
                candidates = []
                for class_name in executor.loaded_classes.keys():
                    # Skip internal AndroidX classes and lambda classes
                    if 'Activity' in class_name and not '$' in class_name and not 'androidx' in class_name.lower():
                        score = 0
                        # Highest priority: Main/Launcher in name
                        if 'Main' in class_name or 'Launcher' in class_name:
                            score = 100
                        # High priority: exact package match (e.g., com.termux.app.TermuxActivity)
                        elif f"{package_simple}.app." in class_name or f"{package_simple}/app/" in class_name:
                            score = 80
                        # Medium priority: package name in class
                        elif package_simple.lower() in class_name.lower():
                            score = 50
                        # Lower priority: other app-related names
                        elif 'Termux' in class_name or 'App' in class_name:
                            score = 40
                        # Penalize utility activities (file picker, settings, views, etc.)
                        if any(x in class_name.lower() for x in ['filepicker', 'receiver', 'settings', 'help', 'report', 'rootview', 'view', 'dialog']):
                            score -= 30
                        candidates.append((score, class_name))
                
                # Sort by score descending
                candidates.sort(reverse=True)
                
                if candidates:
                    main_activity = candidates[0][1]
                    print(f"[*] Auto-detected main activity: {main_activity} (score: {candidates[0][0]})")
                    # Show other candidates for debugging
                    if len(candidates) > 1:
                        print(f"    Other candidates: {[(s, n) for s, n in candidates[1:3]]}")
            
            # Launch main activity
            if main_activity:
                print(f"[*] Launching activity: {main_activity}")
                runtime.launch_activity(class_name=main_activity)
                
                # Run briefly
                import time
                time.sleep(5)
                runtime.dump_activities()
            else:
                # Try to execute main method (for CLI apps)
                print("[*] No Activity found, trying main method...")
                if executor:
                    executor.execute_main()
            
            return 0
        
        # Extract APK for non-management commands
        if not os.path.exists(args.apk):
            print(f"[!] APK not found: {args.apk}")
            return 1
            
        dex_files = extract_apk(args.apk, temp_dir)
        
        if not dex_files:
            print("[!] No DEX files found")
            return 1
        
        # Load DEX files with APK path for resources
        for dex_path in dex_files:
            runtime.load_dex(dex_path, apk_path=args.apk)
        
        # Get executor
        executor = runtime.get_executor()
        if not executor:
            print("[!] No executor available")
            return 1
        
        # Handle commands
        if args.list_classes:
            print("\n[*] Loaded classes:")
            for name in executor.list_classes()[:50]:  # Limit output
                print(f"    {name}")
            total = len(executor.list_classes())
            if total > 50:
                print(f"    ... and {total - 50} more")
        
        elif args.list_methods:
            print(f"\n[*] Methods in {args.list_methods}:")
            methods = executor.list_methods(args.list_methods)
            for name in methods:
                print(f"    {name}")
        
        elif args.execute_main or (args.class_name is None and args.method_name is None):
            # Execute main method
            print("\n[*] Executing main method...")
            result = executor.execute_main()
            if result:
                print("[+] Execution completed")
            else:
                print("[!] Execution failed or no main method found")
        
        elif args.class_name and args.method_name:
            # Execute specific method
            print(f"\n[*] Executing {args.class_name}.{args.method_name}...")
            result = executor.execute_method(args.class_name, args.method_name)
            print(f"[*] Result: {result}")
        
        elif args.launch_activity:
            # Launch activity via Android lifecycle
            print(f"\n[*] Launching activity: {args.launch_activity}")
            runtime.launch_activity(class_name=args.launch_activity)
            
            # Run event loop briefly
            import time
            print("[*] Running for 5 seconds...")
            time.sleep(5)
            
            # Dump activity state
            runtime.dump_activities()
        
        else:
            parser.print_help()
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
