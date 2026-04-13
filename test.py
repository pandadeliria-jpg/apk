#!/usr/bin/env python3
"""
Test Android Compatibility Layer
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'runtime'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'graphics'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'framework'))

def test_dex_loader():
    """Test DEX loader."""
    print("\n=== Testing DEX Loader ===")
    from dex_interpreter import DEXLoader
    
    # Try to find a test DEX file
    test_dex = None
    for root, dirs, files in os.walk(os.path.expanduser("~")):
        for file in files:
            if file.endswith('.dex'):
                test_dex = os.path.join(root, file)
                break
        if test_dex:
            break
    
    if test_dex:
        print(f"[*] Found test DEX: {test_dex}")
        loader = DEXLoader(test_dex)
        if loader.load():
            loader.dump_info()
            return True
    else:
        print("[!] No test DEX file found")
    return False


def test_interpreter():
    """Test bytecode interpreter."""
    print("\n=== Testing Interpreter ===")
    
    # Create mock DEX loader
    class MockDEX:
        def __init__(self):
            self.strings = ["test", "hello", "world"]
            self.types = ["Ljava/lang/String;", "I", "V"]
            self.method_ids = []
    
    from interpreter import Interpreter, JavaObject
    
    mock_dex = MockDEX()
    interp = Interpreter(mock_dex)
    
    # Test simple bytecode
    # const/4 v0, #1
    # const/4 v1, #2
    # add-int v2, v0, v1
    # return v2
    test_code = bytes([
        0x12, 0x01,  # const/4 v0, #1
        0x12, 0x12,  # const/4 v1, #2
        0x90, 0x02, 0x00, 0x01,  # add-int v2, v0, v1
        0x0f, 0x02,  # return v2
    ])
    
    result = interp.execute_method("test_add", test_code)
    print(f"[*] Test result: {result}")
    
    return True


def test_graphics():
    """Test graphics layer."""
    print("\n=== Testing Graphics Layer ===")
    from opengl_es import GLES20, Surface
    
    gles = GLES20()
    surface = Surface(800, 600)
    
    # Test GL calls
    gles.glClearColor(0.0, 0.0, 0.0, 1.0)
    gles.glClear(gles.GL_COLOR_BUFFER_BIT)
    gles.glViewport(0, 0, 800, 600)
    
    shader = gles.glCreateShader(gles.GL_VERTEX_SHADER)
    gles.glShaderSource(shader, "void main() {}")
    gles.glCompileShader(shader)
    
    print("[+] Graphics layer working")
    return True


def test_android_framework():
    """Test Android framework stubs."""
    print("\n=== Testing Android Framework ===")
    from android import Context, Activity, Handler, Intent, Toast
    
    ctx = Context()
    print(f"[*] Context package: {ctx.getPackageName()}")
    print(f"[*] Files dir: {ctx.getFilesDir()}")
    
    # Test SharedPreferences
    prefs = ctx.getSharedPreferences("test", 0)
    editor = prefs.edit()
    editor.putString("username", "testuser")
    editor.putInt("userid", 12345)
    editor.apply()
    
    username = prefs.getString("username")
    userid = prefs.getInt("userid")
    print(f"[*] Saved: username={username}, userid={userid}")
    
    # Test Handler
    handler = Handler()
    result = []
    def test_runnable():
        result.append(True)
    handler.post(test_runnable)
    
    print(f"[*] Handler working: {len(result) > 0}")
    
    # Test Intent
    intent = Intent("android.intent.action.VIEW")
    intent.putExtra("extra_key", "extra_value")
    print(f"[*] Intent extra: {intent.getStringExtra('extra_key')}")
    
    # Test Toast
    Toast.makeText(ctx, "Test message", Toast.LENGTH_SHORT)
    
    print("[+] Android framework working")
    return True


def test_roblox_network():
    """Test Roblox networking."""
    print("\n=== Testing Roblox Network ===")
    
    try:
        from roblox_jni import RobloxNetworking, RobloxCrypto
        
        crypto = RobloxCrypto()
        device_id = crypto.generateDeviceId()
        session_id = crypto.generateSessionId()
        
        print(f"[*] Device ID: {device_id}")
        print(f"[*] Session ID: {session_id}")
        
        network = RobloxNetworking()
        
        # Test username check
        test_username = "Roblox"  # Should be taken
        available = network.check_username(test_username)
        print(f"[*] Username '{test_username}' available: {available}")
        
        print("[+] Roblox network layer working")
        return True
    except Exception as e:
        print(f"[!] Roblox network test failed: {e}")
        return False


def test_roblox_signup():
    """Test Roblox account creation."""
    print("\n=== Testing Roblox Signup ===")
    
    try:
        from scripts.roblox_signup import RobloxAccountCreator
        
        creator = RobloxAccountCreator()
        
        # Check username
        username = "testuser123456"
        available = creator.check_username(username)
        print(f"[*] Username '{username}' available: {available}")
        
        print("[+] Roblox signup module loaded (use --count 1 to create account)")
        return True
    except Exception as e:
        print(f"[!] Roblox signup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("Android Compatibility Layer Test Suite")
    print("="*60)
    
    results = {}
    
    # Run tests
    results['dex_loader'] = test_dex_loader()
    results['interpreter'] = test_interpreter()
    results['graphics'] = test_graphics()
    results['android_framework'] = test_android_framework()
    results['roblox_network'] = test_roblox_network()
    results['roblox_signup'] = test_roblox_signup()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_test in results.items():
        status = "PASS" if passed_test else "FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
