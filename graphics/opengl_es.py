#!/usr/bin/env python3
"""
OpenGL ES → Metal Translation Layer
Translates Android OpenGL ES calls to macOS Metal
"""
import ctypes
from enum import IntEnum
from typing import Dict, List, Optional

# Check if Metal is available (macOS)
try:
    import Metal
    HAS_METAL = True
except ImportError:
    HAS_METAL = False
    print("[!] Metal not available - graphics will be stubbed")


class GLES20:
    """
    OpenGL ES 2.0 API implementation.
    Translates to Metal where possible, otherwise stubs.
    """
    
    # Constants from GLES2/gl2.h
    GL_FALSE = 0
    GL_TRUE = 1
    
    GL_ZERO = 0
    GL_ONE = 1
    
    GL_POINTS = 0x0000
    GL_LINES = 0x0001
    GL_LINE_LOOP = 0x0002
    GL_LINE_STRIP = 0x0003
    GL_TRIANGLES = 0x0004
    GL_TRIANGLE_STRIP = 0x0005
    GL_TRIANGLE_FAN = 0x0006
    
    GL_DEPTH_BUFFER_BIT = 0x00000100
    GL_STENCIL_BUFFER_BIT = 0x00000400
    GL_COLOR_BUFFER_BIT = 0x00004000
    
    GL_CW = 0x0900
    GL_CCW = 0x0901
    
    GL_BLEND = 0x0BE2
    GL_CULL_FACE = 0x0B44
    GL_DEPTH_TEST = 0x0B71
    GL_DITHER = 0x0BD0
    GL_SCISSOR_TEST = 0x0C11
    
    GL_TEXTURE_2D = 0x0DE1
    GL_TEXTURE_CUBE_MAP = 0x8513
    
    GL_BYTE = 0x1400
    GL_UNSIGNED_BYTE = 0x1401
    GL_SHORT = 0x1402
    GL_UNSIGNED_SHORT = 0x1403
    GL_INT = 0x1404
    GL_UNSIGNED_INT = 0x1405
    GL_FLOAT = 0x1406
    GL_FIXED = 0x140C
    
    GL_RGBA = 0x1908
    GL_RGB = 0x1907
    GL_ALPHA = 0x1906
    GL_LUMINANCE = 0x1909
    GL_LUMINANCE_ALPHA = 0x190A
    
    GL_VERTEX_SHADER = 0x8B31
    GL_FRAGMENT_SHADER = 0x8B30
    
    def __init__(self):
        self.context = None
        self.shaders: Dict[int, dict] = {}
        self.programs: Dict[int, dict] = {}
        self.textures: Dict[int, dict] = {}
        self.buffers: Dict[int, dict] = {}
        self.framebuffers: Dict[int, dict] = {}
        self.renderbuffers: Dict[int, dict] = {}
        
        self.current_program = 0
        self.bound_texture = 0
        self.bound_framebuffer = 0
        self.bound_renderbuffer = 0
        
        self.next_shader_id = 1
        self.next_program_id = 1
        self.next_texture_id = 1
        self.next_buffer_id = 1
        self.next_framebuffer_id = 1
        self.next_renderbuffer_id = 1
        
        # State
        self.viewport = (0, 0, 800, 600)
        self.clear_color = (0.0, 0.0, 0.0, 0.0)
        self.clear_depth = 1.0
        self.clear_stencil = 0
        
        self.capabilities = {
            self.GL_BLEND: False,
            self.GL_CULL_FACE: False,
            self.GL_DEPTH_TEST: False,
            self.GL_DITHER: True,
            self.GL_SCISSOR_TEST: False,
        }
        
        self.init_metal()
    
    def init_metal(self):
        """Initialize Metal context."""
        if HAS_METAL:
            try:
                self.device = Metal.MTLCreateSystemDefaultDevice()
                print(f"[+] Metal device: {self.device.name()}")
            except:
                self.device = None
                print("[!] Failed to create Metal device")
        else:
            self.device = None
    
    # === Viewport ===
    
    def glViewport(self, x: int, y: int, width: int, height: int):
        """Set viewport."""
        self.viewport = (x, y, width, height)
        print(f"[*] glViewport({x}, {y}, {width}, {height})")
    
    # === Clearing ===
    
    def glClearColor(self, r: float, g: float, b: float, a: float):
        """Set clear color."""
        self.clear_color = (r, g, b, a)
    
    def glClearDepthf(self, d: float):
        """Set clear depth."""
        self.clear_depth = d
    
    def glClearStencil(self, s: int):
        """Set clear stencil."""
        self.clear_stencil = s
    
    def glClear(self, mask: int):
        """Clear buffers."""
        print(f"[*] glClear({hex(mask)})")
        # In real implementation, would clear Metal render target
    
    # === Capabilities ===
    
    def glEnable(self, cap: int):
        """Enable capability."""
        if cap in self.capabilities:
            self.capabilities[cap] = True
            print(f"[*] glEnable({hex(cap)})")
    
    def glDisable(self, cap: int):
        """Disable capability."""
        if cap in self.capabilities:
            self.capabilities[cap] = False
            print(f"[*] glDisable({hex(cap)})")
    
    # === Shaders ===
    
    def glCreateShader(self, type: int) -> int:
        """Create shader."""
        shader_id = self.next_shader_id
        self.next_shader_id += 1
        
        self.shaders[shader_id] = {
            'type': type,
            'source': '',
            'compiled': False,
            'log': ''
        }
        
        print(f"[*] glCreateShader({hex(type)}) = {shader_id}")
        return shader_id
    
    def glShaderSource(self, shader: int, source: str):
        """Set shader source."""
        if shader in self.shaders:
            self.shaders[shader]['source'] = source
            print(f"[*] glShaderSource({shader}, <{len(source)} chars>)")
    
    def glCompileShader(self, shader: int):
        """Compile shader."""
        if shader in self.shaders:
            # In real implementation, would compile GLSL to Metal shader
            self.shaders[shader]['compiled'] = True
            print(f"[*] glCompileShader({shader})")
    
    def glDeleteShader(self, shader: int):
        """Delete shader."""
        if shader in self.shaders:
            del self.shaders[shader]
    
    # === Programs ===
    
    def glCreateProgram(self) -> int:
        """Create shader program."""
        program_id = self.next_program_id
        self.next_program_id += 1
        
        self.programs[program_id] = {
            'vertex_shader': 0,
            'fragment_shader': 0,
            'linked': False,
            'attributes': {},
            'uniforms': {}
        }
        
        print(f"[*] glCreateProgram() = {program_id}")
        return program_id
    
    def glAttachShader(self, program: int, shader: int):
        """Attach shader to program."""
        if program in self.programs and shader in self.shaders:
            shader_type = self.shaders[shader]['type']
            if shader_type == self.GL_VERTEX_SHADER:
                self.programs[program]['vertex_shader'] = shader
            elif shader_type == self.GL_FRAGMENT_SHADER:
                self.programs[program]['fragment_shader'] = shader
            print(f"[*] glAttachShader({program}, {shader})")
    
    def glLinkProgram(self, program: int):
        """Link program."""
        if program in self.programs:
            self.programs[program]['linked'] = True
            print(f"[*] glLinkProgram({program})")
    
    def glUseProgram(self, program: int):
        """Use program."""
        self.current_program = program
        print(f"[*] glUseProgram({program})")
    
    def glDeleteProgram(self, program: int):
        """Delete program."""
        if program in self.programs:
            del self.programs[program]
    
    # === Buffers ===
    
    def glGenBuffers(self, n: int) -> List[int]:
        """Generate buffer names."""
        buffers = []
        for _ in range(n):
            buffer_id = self.next_buffer_id
            self.next_buffer_id += 1
            self.buffers[buffer_id] = {'data': None, 'size': 0}
            buffers.append(buffer_id)
        return buffers
    
    def glBindBuffer(self, target: int, buffer: int):
        """Bind buffer."""
        print(f"[*] glBindBuffer({hex(target)}, {buffer})")
    
    def glBufferData(self, target: int, size: int, data: bytes, usage: int):
        """Upload buffer data."""
        print(f"[*] glBufferData({hex(target)}, {size}, <data>, {hex(usage)})")
    
    def glDeleteBuffers(self, n: int, buffers: List[int]):
        """Delete buffers."""
        for buf in buffers:
            if buf in self.buffers:
                del self.buffers[buf]
    
    # === Textures ===
    
    def glGenTextures(self, n: int) -> List[int]:
        """Generate texture names."""
        textures = []
        for _ in range(n):
            tex_id = self.next_texture_id
            self.next_texture_id += 1
            self.textures[tex_id] = {
                'width': 0,
                'height': 0,
                'format': 0,
                'data': None
            }
            textures.append(tex_id)
        return textures
    
    def glBindTexture(self, target: int, texture: int):
        """Bind texture."""
        self.bound_texture = texture
        print(f"[*] glBindTexture({hex(target)}, {texture})")
    
    def glTexImage2D(self, target: int, level: int, internalformat: int,
                     width: int, height: int, border: int,
                     format: int, type: int, pixels: Optional[bytes]):
        """Specify texture image."""
        if self.bound_texture in self.textures:
            self.textures[self.bound_texture]['width'] = width
            self.textures[self.bound_texture]['height'] = height
            self.textures[self.bound_texture]['format'] = internalformat
            self.textures[self.bound_texture]['data'] = pixels
        print(f"[*] glTexImage2D({hex(target)}, {level}, {hex(internalformat)}, {width}, {height})")
    
    def glTexParameteri(self, target: int, pname: int, param: int):
        """Set texture parameter."""
        print(f"[*] glTexParameteri({hex(target)}, {hex(pname)}, {hex(param)})")
    
    # === Vertex Arrays ===
    
    def glVertexAttribPointer(self, index: int, size: int, type: int,
                               normalized: bool, stride: int, pointer: int):
        """Specify vertex attribute pointer."""
        print(f"[*] glVertexAttribPointer({index}, {size}, {hex(type)}, {normalized}, {stride}, {pointer})")
    
    def glEnableVertexAttribArray(self, index: int):
        """Enable vertex attribute array."""
        print(f"[*] glEnableVertexAttribArray({index})")
    
    def glDisableVertexAttribArray(self, index: int):
        """Disable vertex attribute array."""
        print(f"[*] glDisableVertexAttribArray({index})")
    
    # === Drawing ===
    
    def glDrawArrays(self, mode: int, first: int, count: int):
        """Draw arrays."""
        print(f"[*] glDrawArrays({hex(mode)}, {first}, {count})")
    
    def glDrawElements(self, mode: int, count: int, type: int, indices: int):
        """Draw elements."""
        print(f"[*] glDrawElements({hex(mode)}, {count}, {hex(type)}, {indices})")
    
    # === Uniforms ===
    
    def glGetUniformLocation(self, program: int, name: str) -> int:
        """Get uniform location."""
        # In real implementation, would parse shader and return location
        loc = hash(name) % 1000
        print(f"[*] glGetUniformLocation({program}, '{name}') = {loc}")
        return loc
    
    def glUniform1f(self, location: int, v0: float):
        """Set float uniform."""
        print(f"[*] glUniform1f({location}, {v0})")
    
    def glUniform4f(self, location: int, v0: float, v1: float, v2: float, v3: float):
        """Set vec4 uniform."""
        print(f"[*] glUniform4f({location}, {v0}, {v1}, {v2}, {v3})")
    
    def glUniformMatrix4fv(self, location: int, count: int, transpose: bool, value: List[float]):
        """Set mat4 uniform."""
        print(f"[*] glUniformMatrix4fv({location}, {count}, {transpose}, <{len(value)} floats>)")


class Surface:
    """
    Android Surface → macOS CALayer/MTKView
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.gles = GLES20()
        self.pixels = bytearray(width * height * 4)  # RGBA
        
        print(f"[*] Surface created: {width}x{height}")
    
    def lockCanvas(self):
        """Lock canvas for drawing."""
        print("[*] Surface.lockCanvas()")
        return self  # Return self as canvas stub
    
    def unlockCanvasAndPost(self, canvas):
        """Unlock and post canvas."""
        print("[*] Surface.unlockCanvasAndPost()")
    
    def drawColor(self, color: int):
        """Fill with color."""
        print(f"[*] Canvas.drawColor({hex(color)})")


class EGLContext:
    """
    EGL context management.
    """
    
    def __init__(self):
        self.display = None
        self.surface = None
        self.context = None
        self.gles = None
    
    def eglGetDisplay(self, display_id: int):
        """Get EGL display."""
        print(f"[*] eglGetDisplay({display_id})")
        return 1  # Return dummy display handle
    
    def eglInitialize(self, display: int) -> bool:
        """Initialize EGL."""
        print("[*] eglInitialize()")
        return True
    
    def eglCreateContext(self, display: int, config: int, share_context: int, attrib_list: List[int]) -> int:
        """Create EGL context."""
        print("[*] eglCreateContext()")
        self.gles = GLES20()
        return 1  # Return dummy context handle
    
    def eglCreateWindowSurface(self, display: int, config: int, window: int, attrib_list: List[int]) -> int:
        """Create window surface."""
        print("[*] eglCreateWindowSurface()")
        self.surface = Surface()
        return 1  # Return dummy surface handle
    
    def eglMakeCurrent(self, display: int, draw: int, read: int, context: int) -> bool:
        """Make context current."""
        print("[*] eglMakeCurrent()")
        return True
    
    def eglSwapBuffers(self, display: int, surface: int) -> bool:
        """Swap buffers."""
        print("[*] eglSwapBuffers()")
        return True


# Global instances
_gles = None
_egl = None
_metal_renderer = None

def getGLES20():
    """Get or create GLES20 instance."""
    global _gles, _metal_renderer
    
    # Use real Metal renderer if available
    try:
        from metal_renderer import MetalRenderer, HAS_METAL
        if HAS_METAL and _metal_renderer is None:
            _metal_renderer = MetalRenderer()
            print("[+] Using real Metal renderer")
            return _metal_renderer
    except ImportError:
        pass
    
    # Fallback to stub
    if _gles is None:
        _gles = GLES20()
    return _gles

def getEGL():
    """Get or create EGL context."""
    global _egl
    if _egl is None:
        _egl = EGLContext()
    return _egl

def getMetalRenderer():
    """Get Metal renderer directly."""
    global _metal_renderer
    if _metal_renderer is None:
        try:
            from metal_renderer import MetalRenderer, HAS_METAL
            if HAS_METAL:
                _metal_renderer = MetalRenderer()
        except ImportError:
            pass
    return _metal_renderer
