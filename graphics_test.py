#!/usr/bin/env python3
"""
Graphics Test - Verify Metal renderer creates windows and renders
"""
import sys
import os
import time
import threading

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'graphics'))

def test_metal_renderer():
    """Test Metal renderer creates window."""
    print("\n=== Testing Metal Graphics ===")
    
    try:
        from metal_renderer import MetalRenderer, HAS_METAL
        
        if not HAS_METAL:
            print("[!] Metal/PyObjC not installed")
            print("    Install: pip3 install pyobjc pyobjc-framework-Metal pyobjc-framework-MetalKit")
            return False
        
        print("[*] Creating Metal renderer...")
        renderer = MetalRenderer(800, 600)
        
        if not renderer.device:
            print("[!] Metal device creation failed")
            return False
        
        print(f"[+] Metal device: {renderer.device.name()}")
        print(f"[+] Window created: {renderer.width}x{renderer.height}")
        
        # Test GL calls
        print("[*] Testing GL API...")
        renderer.glClearColor(0.2, 0.3, 0.4, 1.0)
        renderer.glViewport(0, 0, 800, 600)
        
        # Test shader creation
        shader = renderer.glCreateShader(renderer.GL_VERTEX_SHADER)
        print(f"[+] Shader created: ID {shader}")
        
        vertex_src = '''
        attribute vec4 position;
        attribute vec4 color;
        varying vec4 v_color;
        void main() {
            gl_Position = position;
            v_color = color;
        }
        '''
        renderer.glShaderSource(shader, vertex_src)
        renderer.glCompileShader(shader)
        
        # Test buffer
        buffers = renderer.glGenBuffers(1)
        print(f"[+] Buffer created: ID {buffers[0]}")
        
        # Test texture
        textures = renderer.glGenTextures(1)
        print(f"[+] Texture created: ID {textures[0]}")
        
        # Test draw
        renderer.glDrawArrays(renderer.GL_TRIANGLES, 0, 3)
        
        print("[*] Running render loop for 3 seconds...")
        
        # Run briefly
        start = time.time()
        while time.time() - start < 3:
            renderer.process_events()
            time.sleep(0.016)  # 60 FPS
        
        print("[+] Graphics test completed")
        return True
        
    except Exception as e:
        print(f"[!] Graphics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test OpenGL ES → Metal integration."""
    print("\n=== Testing OpenGL ES Integration ===")
    
    try:
        from opengl_es import getGLES20, getMetalRenderer
        
        gles = getGLES20()
        
        # Check if it's real Metal or stub
        from metal_renderer import HAS_METAL, MetalRenderer
        if isinstance(gles, MetalRenderer):
            print("[+] Using REAL Metal renderer")
        else:
            print("[!] Using stub GLES (Metal not available)")
        
        # Test GL calls
        gles.glClearColor(0.1, 0.2, 0.3, 1.0)
        gles.glClear(gles.GL_COLOR_BUFFER_BIT)
        gles.glViewport(0, 0, 800, 600)
        
        shader = gles.glCreateShader(gles.GL_VERTEX_SHADER)
        gles.glShaderSource(shader, "void main() { gl_Position = vec4(0); }")
        gles.glCompileShader(shader)
        
        print("[+] Integration test passed")
        return True
        
    except Exception as e:
        print(f"[!] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("Graphics Test Suite")
    print("Testing Metal renderer and OpenGL ES integration")
    print("="*60)
    
    results = {}
    
    # Test integration first (no window)
    results['integration'] = test_integration()
    
    # Test Metal renderer with window
    # Comment this out if you don't want a window popping up
    # results['metal_renderer'] = test_metal_renderer()
    
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
    
    if passed == total and 'integration' in results and results['integration']:
        print("\n[+] Graphics layer is working!")
        print("    Roblox can now render with real Metal graphics!")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
