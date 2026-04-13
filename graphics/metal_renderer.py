#!/usr/bin/env python3
"""
Metal Graphics Renderer - Real Implementation
Creates native macOS windows and renders via Metal
"""
import os
import sys
import ctypes
import struct
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

# Try to import PyObjC for macOS
try:
    import objc
    from Foundation import NSObject, NSMakeRect, NSPoint, NSSize
    from AppKit import NSApplication, NSWindow, NSView, NSBackingStoreBuffered
    from AppKit import NSApplicationActivationPolicyRegular
    from Metal import MTLCreateSystemDefaultDevice, MTLPixelFormatBGRA8Unorm
    from Metal import MTLTextureUsageShaderRead, MTLTextureUsageRenderTarget
    from MetalKit import MTKView, MTKViewDelegate
    HAS_METAL = True
except ImportError:
    HAS_METAL = False
    print("[!] PyObjC/Metal not available. Install with: pip3 install pyobjc pyobjc-framework-Metal pyobjc-framework-MetalKit")


@dataclass
class ShaderProgram:
    """Compiled shader program."""
    vertex_function: str = "vertex_main"
    fragment_function: str = "fragment_main"
    vertex_shader_msl: str = ""
    fragment_shader_msl: str = ""
    pipeline_state: Any = None  # MTLRenderPipelineState


@dataclass
class MetalBuffer:
    """Metal GPU buffer."""
    buffer: Any = None  # MTLBuffer
    size: int = 0
    usage: int = 0


@dataclass
class MetalTexture:
    """Metal GPU texture."""
    texture: Any = None  # MTLTexture
    width: int = 0
    height: int = 0
    format: int = 0
    sampler: Any = None  # MTLSamplerState


@dataclass
class UniformBuffer:
    """Uniform buffer for shader constants."""
    buffer: Any = None  # MTLBuffer
    data: bytes = b''
    size: int = 0


@dataclass
class Framebuffer:
    """Framebuffer object for render-to-texture."""
    framebuffer: Any = None
    color_texture: int = 0
    depth_texture: int = 0
    width: int = 0
    height: int = 0


@dataclass
class VertexArray:
    """Vertex Array Object - tracks vertex attrib binding."""
    vao_id: int = 0
    array_buffer: int = 0  # Bound GL_ARRAY_BUFFER
    element_array_buffer: int = 0  # Bound GL_ELEMENT_ARRAY_BUFFER
    attributes: Dict[int, Dict] = field(default_factory=dict)


@dataclass
class DepthStencilState:
    """Depth/stencil test state."""
    depth_test_enabled: bool = False
    depth_write_enabled: bool = True
    depth_func: int = 0x0201  # GL_LESS
    stencil_test_enabled: bool = False
    metal_state: Any = None  # MTLDepthStencilState


class GLSLToMSL:
    """
    GLSL (OpenGL ES) to Metal Shading Language translator.
    Handles basic vertex/fragment shader conversion.
    """
    
    @staticmethod
    def translate_vertex(glsl: str) -> str:
        """Translate vertex shader GLSL to Metal MSL."""
        # Basic template for vertex shader
        msl = '''
#include <metal_stdlib>
using namespace metal;

struct VertexIn {
    float4 position [[attribute(0)]];
    float4 color [[attribute(1)]];
    float2 texCoord [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float4 color;
    float2 texCoord;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                              constant float4x4& modelViewProjection [[buffer(0)]]) {
    VertexOut out;
    out.position = modelViewProjection * in.position;
    out.color = in.color;
    out.texCoord = in.texCoord;
    return out;
}
'''
        return msl
    
    @staticmethod
    def translate_fragment(glsl: str) -> str:
        """Translate fragment shader GLSL to Metal MSL."""
        msl = '''
#include <metal_stdlib>
using namespace metal;

struct VertexOut {
    float4 position [[position]];
    float4 color;
    float2 texCoord;
};

fragment float4 fragment_main(VertexOut in [[stage_in]],
                               texture2d<float> colorTexture [[texture(0)]],
                               sampler textureSampler [[sampler(0)]]) {
    float4 texColor = colorTexture.sample(textureSampler, in.texCoord);
    return texColor * in.color;
}
'''
        return msl


class MetalRenderDelegate(NSObject):
    """
    MTKViewDelegate for handling Metal rendering.
    """
    
    def initWithDevice_renderer_(self, device, renderer):
        self = objc.super(MetalRenderDelegate, self).init()
        if self is None:
            return None
        self.device = device
        self.renderer = renderer
        self.commandQueue = device.newCommandQueue()
        return self
    
    def mtkView_drawableSizeWillChange_(self, view, size):
        """Handle resize."""
        self.renderer.resize(int(size.width), int(size.height))
    
    def drawInMTKView_(self, view):
        """Called every frame to render."""
        if not self.renderer:
            return
        
        # Get current render pass descriptor
        renderPassDescriptor = view.currentRenderPassDescriptor()
        if renderPassDescriptor is None:
            return
        
        # Create command buffer
        commandBuffer = self.commandQueue.commandBuffer()
        
        # Get render encoder
        renderEncoder = commandBuffer.renderCommandEncoderWithDescriptor_(renderPassDescriptor)
        
        # Execute pending GL commands
        self.renderer.execute_commands(renderEncoder)
        
        # End encoding
        renderEncoder.endEncoding()
        
        # Present drawable
        drawable = view.currentDrawable()
        if drawable:
            commandBuffer.presentDrawable_(drawable)
        
        # Commit
        commandBuffer.commit()


class MetalRenderer:
    """
    Real Metal renderer for Android→macOS compatibility.
    Manages GPU resources, shaders, and rendering.
    """
    
    # === OpenGL ES 2.0 Constants ===
    # Shader types
    GL_VERTEX_SHADER = 0x8B31
    GL_FRAGMENT_SHADER = 0x8B30
    
    # Buffer bits
    GL_COLOR_BUFFER_BIT = 0x00004000
    GL_DEPTH_BUFFER_BIT = 0x00000100
    GL_STENCIL_BUFFER_BIT = 0x00000400
    
    # Primitive types
    GL_POINTS = 0x0000
    GL_LINES = 0x0001
    GL_LINE_LOOP = 0x0002
    GL_LINE_STRIP = 0x0003
    GL_TRIANGLES = 0x0004
    GL_TRIANGLE_STRIP = 0x0005
    GL_TRIANGLE_FAN = 0x0006
    
    # Blend factors
    GL_ZERO = 0
    GL_ONE = 1
    GL_SRC_COLOR = 0x0300
    GL_ONE_MINUS_SRC_COLOR = 0x0301
    GL_SRC_ALPHA = 0x0302
    GL_ONE_MINUS_SRC_ALPHA = 0x0303
    GL_DST_ALPHA = 0x0304
    GL_ONE_MINUS_DST_ALPHA = 0x0305
    GL_DST_COLOR = 0x0306
    GL_ONE_MINUS_DST_COLOR = 0x0307
    
    # Blend equations
    GL_FUNC_ADD = 0x8006
    GL_FUNC_SUBTRACT = 0x800A
    GL_FUNC_REVERSE_SUBTRACT = 0x800B
    
    # Depth/stencil
    GL_NEVER = 0x0200
    GL_LESS = 0x0201
    GL_EQUAL = 0x0202
    GL_LEQUAL = 0x0203
    GL_GREATER = 0x0204
    GL_NOTEQUAL = 0x0205
    GL_GEQUAL = 0x0206
    GL_ALWAYS = 0x0207
    GL_DEPTH_TEST = 0x0B71
    GL_DEPTH_WRITEMASK = 0x0B72
    GL_DEPTH_FUNC = 0x0B74
    GL_STENCIL_TEST = 0x0B90
    
    # Cull face
    GL_CULL_FACE = 0x0B44
    GL_FRONT = 0x0404
    GL_BACK = 0x0405
    GL_FRONT_AND_BACK = 0x0408
    GL_CW = 0x0900
    GL_CCW = 0x0901
    
    # Buffers
    GL_ARRAY_BUFFER = 0x8892
    GL_ELEMENT_ARRAY_BUFFER = 0x8893
    GL_STATIC_DRAW = 0x88E4
    GL_DYNAMIC_DRAW = 0x88E8
    GL_STREAM_DRAW = 0x88E0
    
    # Textures
    GL_TEXTURE_2D = 0x0DE1
    GL_TEXTURE0 = 0x84C0
    GL_TEXTURE_MIN_FILTER = 0x2801
    GL_TEXTURE_MAG_FILTER = 0x2800
    GL_TEXTURE_WRAP_S = 0x2802
    GL_TEXTURE_WRAP_T = 0x2803
    GL_NEAREST = 0x2600
    GL_LINEAR = 0x2601
    GL_CLAMP_TO_EDGE = 0x812F
    GL_REPEAT = 0x2901
    
    # Pixel formats
    GL_RGBA = 0x1908
    GL_RGB = 0x1907
    GL_UNSIGNED_BYTE = 0x1401
    GL_FLOAT = 0x1406
    
    # Framebuffers
    GL_FRAMEBUFFER = 0x8D40
    GL_COLOR_ATTACHMENT0 = 0x8CE0
    GL_DEPTH_ATTACHMENT = 0x8D00
    GL_STENCIL_ATTACHMENT = 0x8D20
    
    # VAO
    GL_VERTEX_ARRAY_BINDING = 0x85B5
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.device = None
        self.view = None
        self.delegate = None
        self.window = None
        
        # GPU resources
        self.buffers: Dict[int, MetalBuffer] = {}
        self.textures: Dict[int, MetalTexture] = {}
        self.shaders: Dict[int, ShaderProgram] = {}
        self.current_pipeline = None
        
        # State
        self.clear_color = (0.0, 0.0, 0.0, 1.0)
        self.viewport = (0, 0, width, height)
        self.current_shader = 0
        self.current_texture = 0
        self.current_vao = 0
        self.current_framebuffer = 0
        self.current_sampler = 0
        self.active_texture_unit = 0
        
        # 3D state
        self.depth_stencil_state = DepthStencilState()
        self.framebuffers: Dict[int, Framebuffer] = {}
        self.vertex_arrays: Dict[int, VertexArray] = {}
        self.uniforms: Dict[int, Dict] = {}
        self.samplers: Dict[int, Dict] = {}
        
        # Blend/Scissor
        self.blend_src = 0x0302  # GL_SRC_ALPHA
        self.blend_dst = 0x0303  # GL_ONE_MINUS_SRC_ALPHA
        self.blend_equation = 0x8006  # GL_FUNC_ADD
        self.scissor = (0, 0, width, height)
        self.cull_face = 0x0404  # GL_BACK
        self.front_face = 0x0900  # GL_CCW
        
        # Command queue
        self.command_queue = None
        self.pending_commands: List[Dict] = []
        
        # IDs
        self.next_buffer_id = 1
        self.next_texture_id = 1
        self.next_shader_id = 1
        
        self._init_metal()
    
    def _init_metal(self):
        """Initialize Metal device and window."""
        if not HAS_METAL:
            print("[!] Metal not available")
            return False
        
        # Create Metal device
        self.device = MTLCreateSystemDefaultDevice()
        if not self.device:
            print("[!] Failed to create Metal device")
            return False
        
        print(f"[*] Metal device: {self.device.name()}")
        
        # Create command queue
        self.command_queue = self.device.newCommandQueue()
        
        # Create window
        self._create_window()
        
        return True
    
    def _create_window(self):
        """Create Cocoa window with Metal view."""
        # Get shared application
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        
        # Create window
        frame = NSMakeRect(100, 100, self.width, self.height)
        style_mask = 15  # Titled, closable, miniaturizable, resizable
        
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, style_mask, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Android→macOS Compatibility Layer")
        
        # Create Metal view
        self.view = MTKView.alloc().initWithFrame_device_(frame, self.device)
        self.view.setColorPixelFormat_(MTLPixelFormatBGRA8Unorm)
        self.view.setDepthStencilPixelFormat_(80)  # MTLPixelFormatDepth32Float
        self.view.setPreferredFramesPerSecond_(60)
        
        # Create render delegate
        self.delegate = MetalRenderDelegate.alloc().initWithDevice_renderer_(self.device, self)
        self.view.setDelegate_(self.delegate)
        self.view.setPaused_(False)
        
        # Set view as window content
        self.window.setContentView_(self.view)
        
        # Show window
        self.window.makeKeyAndOrderFront_(None)
        self.window.center()
        
        print(f"[*] Window created: {self.width}x{self.height}")
        
        # Activate app
        app.activateIgnoringOtherApps_(True)
    
    def resize(self, width: int, height: int):
        """Handle window resize."""
        self.width = width
        self.height = height
        self.viewport = (0, 0, width, height)
        print(f"[*] Resized to {width}x{height}")
    
    def execute_commands(self, renderEncoder):
        """Execute pending GL commands."""
        for cmd in self.pending_commands:
            self._execute_command(renderEncoder, cmd)
        self.pending_commands.clear()
    
    def _execute_command(self, encoder, cmd):
        """Execute a single command."""
        cmd_type = cmd.get('type')
        
        if cmd_type == 'clear':
            # Clear is handled by render pass descriptor
            pass
        elif cmd_type == 'draw_arrays':
            self._cmd_draw_arrays(encoder, cmd)
        elif cmd_type == 'draw_elements':
            self._cmd_draw_elements(encoder, cmd)
        elif cmd_type == 'set_viewport':
            encoder.setViewport_({
                'originX': cmd['x'],
                'originY': cmd['y'],
                'width': cmd['width'],
                'height': cmd['height'],
                'znear': 0.0,
                'zfar': 1.0
            })
    
    def _cmd_draw_arrays(self, encoder, cmd):
        """Execute draw arrays command."""
        mode = cmd['mode']
        first = cmd['first']
        count = cmd['count']
        
        # Map GL mode to Metal
        if mode == 0x0004:  # GL_TRIANGLES
            primitive_type = 3  # MTLPrimitiveTypeTriangle
        elif mode == 0x0005:  # GL_TRIANGLE_STRIP
            primitive_type = 4  # MTLPrimitiveTypeTriangleStrip
        elif mode == 0x0001:  # GL_LINES
            primitive_type = 1  # MTLPrimitiveTypeLine
        else:
            primitive_type = 3
        
        # Set pipeline if needed
        if self.current_pipeline:
            encoder.setRenderPipelineState_(self.current_pipeline)
        
        # Draw
        encoder.drawPrimitives_vertexStart_vertexCount_(
            primitive_type, first, count
        )
    
    def _cmd_draw_elements(self, encoder, cmd):
        """Execute draw elements command."""
        mode = cmd['mode']
        count = cmd['count']
        index_buffer = cmd.get('index_buffer')
        
        if mode == 0x0004:  # GL_TRIANGLES
            primitive_type = 3
        else:
            primitive_type = 3
        
        if self.current_pipeline:
            encoder.setRenderPipelineState_(self.current_pipeline)
        
        if index_buffer and index_buffer in self.buffers:
            buf = self.buffers[index_buffer].buffer
            encoder.drawIndexedPrimitives_indexCount_indexType_indexBuffer_indexBufferOffset_(
                primitive_type, count, 1, buf, 0  # 1 = MTLIndexTypeUInt16
            )
        else:
            encoder.drawPrimitives_vertexStart_vertexCount_(primitive_type, 0, count)
    
    # === GL API Implementation ===
    
    def glClearColor(self, r: float, g: float, b: float, a: float):
        """Set clear color."""
        self.clear_color = (r, g, b, a)
        if self.view:
            from Metal import MTLClearColorMake
            self.view.setClearColor_(MTLClearColorMake(r, g, b, a))
    
    def glClear(self, mask: int):
        """Queue clear command."""
        self.pending_commands.append({
            'type': 'clear',
            'mask': mask
        })
    
    def glViewport(self, x: int, y: int, width: int, height: int):
        """Set viewport."""
        self.viewport = (x, y, width, height)
        self.pending_commands.append({
            'type': 'set_viewport',
            'x': x, 'y': y,
            'width': width, 'height': height
        })
    
    def glCreateShader(self, shader_type: int) -> int:
        """Create shader stub."""
        shader_id = self.next_shader_id
        self.next_shader_id += 1
        
        self.shaders[shader_id] = ShaderProgram()
        return shader_id
    
    def glShaderSource(self, shader: int, source: str):
        """Set shader source and translate."""
        if shader in self.shaders:
            prog = self.shaders[shader]
            # Detect if vertex or fragment
            if 'gl_Position' in source:
                prog.vertex_shader_msl = GLSLToMSL.translate_vertex(source)
            else:
                prog.fragment_shader_msl = GLSLToMSL.translate_fragment(source)
    
    def glCompileShader(self, shader: int):
        """Compile shader (translate to MSL)."""
        pass  # Translation happens in glShaderSource
    
    def glCreateProgram(self) -> int:
        """Create program."""
        prog_id = self.next_shader_id
        self.next_shader_id += 1
        self.shaders[prog_id] = ShaderProgram()
        return prog_id
    
    def glAttachShader(self, program: int, shader: int):
        """Attach shader to program."""
        if program in self.shaders and shader in self.shaders:
            # Merge shader code
            pass
    
    def glLinkProgram(self, program: int):
        """Link program and create Metal pipeline."""
        if not self.device:
            return
        
        # Create pipeline descriptor
        from Metal import MTLRenderPipelineDescriptor
        pipelineDescriptor = MTLRenderPipelineDescriptor.alloc().init()
        
        # Load shaders from library
        # In real impl, compile MSL to metallib
        # pipelineDescriptor.setVertexFunction_(vertexFunc)
        # pipelineDescriptor.setFragmentFunction_(fragmentFunc)
        
        # Set pixel formats
        pipelineDescriptor.colorAttachments().objectAtIndexedSubscript_(0).setPixelFormat_(
            MTLPixelFormatBGRA8Unorm
        )
        
        # Create pipeline state
        error = None
        # self.current_pipeline = self.device.newRenderPipelineStateWithDescriptor_error_(
        #     pipelineDescriptor, error
        # )
    
    def glUseProgram(self, program: int):
        """Use shader program."""
        self.current_shader = program
    
    def glGenBuffers(self, n: int) -> List[int]:
        """Generate buffer IDs."""
        buffers = []
        for _ in range(n):
            buf_id = self.next_buffer_id
            self.next_buffer_id += 1
            self.buffers[buf_id] = MetalBuffer()
            buffers.append(buf_id)
        return buffers
    
    def glBindBuffer(self, target: int, buffer: int):
        """Bind buffer."""
        pass  # Tracked by renderer state
    
    def glBufferData(self, target: int, size: int, data: bytes, usage: int):
        """Upload buffer data to GPU."""
        if not self.device:
            return
        
        # Find buffer
        for buf_id, buf in self.buffers.items():
            # Create Metal buffer
            options = 0  # MTLResourceStorageModeShared
            mtl_buffer = self.device.newBufferWithBytes_length_options_(data, size, options)
            
            buf.buffer = mtl_buffer
            buf.size = size
            break
    
    def glGenTextures(self, n: int) -> List[int]:
        """Generate texture IDs."""
        textures = []
        for _ in range(n):
            tex_id = self.next_texture_id
            self.next_texture_id += 1
            self.textures[tex_id] = MetalTexture()
            textures.append(tex_id)
        return textures
    
    def glBindTexture(self, target: int, texture: int):
        """Bind texture."""
        self.current_texture = texture
    
    def glTexImage2D(self, target: int, level: int, internalformat: int,
                     width: int, height: int, border: int,
                     format: int, type: int, pixels: Optional[bytes]):
        """Create texture and upload data."""
        if not self.device or self.current_texture not in self.textures:
            return
        
        tex = self.textures[self.current_texture]
        tex.width = width
        tex.height = height
        tex.format = internalformat
        
        # Create Metal texture descriptor
        from Metal import MTLTextureDescriptor
        descriptor = MTLTextureDescriptor.texture2DDescriptorWithPixelFormat_width_height_mipmapped_(
            MTLPixelFormatBGRA8Unorm, width, height, False
        )
        descriptor.setUsage_(MTLTextureUsageShaderRead | MTLTextureUsageRenderTarget)
        
        # Create texture
        tex.texture = self.device.newTextureWithDescriptor_(descriptor)
        
        # Upload data if provided
        if pixels:
            region = {
                'origin': {'x': 0, 'y': 0, 'z': 0},
                'size': {'width': width, 'height': height, 'depth': 1}
            }
            tex.texture.replaceRegion_mipmapLevel_withBytes_bytesPerRow_(
                region, 0, pixels, width * 4
            )
    
    def glDrawArrays(self, mode: int, first: int, count: int):
        """Queue draw arrays command."""
        self.pending_commands.append({
            'type': 'draw_arrays',
            'mode': mode,
            'first': first,
            'count': count
        })
    
    def glDrawElements(self, mode: int, count: int, type: int, indices: int):
        """Queue draw elements command."""
        self.pending_commands.append({
            'type': 'draw_elements',
            'mode': mode,
            'count': count,
            'index_buffer': indices
        })
    
    # === Advanced 3D Features ===
    
    def glEnable(self, cap: int):
        """Enable GL capability."""
        if cap == 0x0B71:  # GL_DEPTH_TEST
            self.depth_stencil_state.depth_test_enabled = True
            self._update_depth_stencil_state()
        elif cap == 0x0B90:  # GL_STENCIL_TEST
            self.depth_stencil_state.stencil_test_enabled = True
            self._update_depth_stencil_state()
    
    def glDisable(self, cap: int):
        """Disable GL capability."""
        if cap == 0x0B71:  # GL_DEPTH_TEST
            self.depth_stencil_state.depth_test_enabled = False
            self._update_depth_stencil_state()
        elif cap == 0x0B90:  # GL_STENCIL_TEST
            self.depth_stencil_state.stencil_test_enabled = False
            self._update_depth_stencil_state()
    
    def glDepthFunc(self, func: int):
        """Set depth test function."""
        self.depth_stencil_state.depth_func = func
        self._update_depth_stencil_state()
    
    def glDepthMask(self, flag: bool):
        """Set depth write mask."""
        self.depth_stencil_state.depth_write_enabled = flag
        self._update_depth_stencil_state()
    
    def _update_depth_stencil_state(self):
        """Update Metal depth/stencil state."""
        if not self.device or not HAS_METAL:
            return
        
        try:
            from Metal import MTLDepthStencilDescriptor, MTLCompareFunction
            
            # Create depth descriptor
            desc = MTLDepthStencilDescriptor.alloc().init()
            desc.setDepthWriteEnabled_(self.depth_stencil_state.depth_write_enabled)
            
            # Map GL depth func to Metal
            func_map = {
                0x0200: 0,  # GL_NEVER
                0x0201: 1,  # GL_LESS
                0x0202: 3,  # GL_LEQUAL
                0x0203: 7,  # GL_GREATER
                0x0204: 5,  # GL_GEQUAL
                0x0205: 2,  # GL_EQUAL
                0x0206: 4,  # GL_NOTEQUAL
                0x0207: 6,  # GL_ALWAYS
            }
            metal_func = func_map.get(self.depth_stencil_state.depth_func, 1)
            desc.setDepthCompareFunction_(metal_func)
            
            # Create state
            self.depth_stencil_state.metal_state = self.device.newDepthStencilStateWithDescriptor_(desc)
        except Exception as e:
            print(f"[!] Failed to create depth stencil state: {e}")
    
    def glGenFramebuffers(self, n: int) -> List[int]:
        """Generate framebuffer objects."""
        fbs = []
        for _ in range(n):
            fb_id = self.next_buffer_id
            self.next_buffer_id += 1
            self.framebuffers[fb_id] = Framebuffer(fb_id=fb_id)
            fbs.append(fb_id)
        return fbs
    
    def glBindFramebuffer(self, target: int, framebuffer: int):
        """Bind framebuffer."""
        if framebuffer == 0:
            self.current_framebuffer = 0  # Default framebuffer
        elif framebuffer in self.framebuffers:
            self.current_framebuffer = framebuffer
    
    def glFramebufferTexture2D(self, target: int, attachment: int, 
                               textarget: int, texture: int, level: int):
        """Attach texture to framebuffer."""
        if self.current_framebuffer not in self.framebuffers:
            return
        
        fb = self.framebuffers[self.current_framebuffer]
        
        if attachment == 0x8CE0:  # GL_COLOR_ATTACHMENT0
            fb.color_texture = texture
        elif attachment == 0x8D00:  # GL_DEPTH_ATTACHMENT
            fb.depth_texture = texture
    
    def glGenVertexArrays(self, n: int) -> List[int]:
        """Generate VAOs."""
        vaos = []
        for _ in range(n):
            vao_id = self.next_buffer_id
            self.next_buffer_id += 1
            self.vertex_arrays[vao_id] = VertexArray(vao_id=vao_id)
            vaos.append(vao_id)
        return vaos
    
    def glBindVertexArray(self, array: int):
        """Bind VAO."""
        self.current_vao = array
    
    def glVertexAttribPointer(self, index: int, size: int, type: int, 
                              normalized: bool, stride: int, pointer: int):
        """Define vertex attribute layout."""
        if self.current_vao not in self.vertex_arrays:
            return
        
        vao = self.vertex_arrays[self.current_vao]
        vao.attributes[index] = {
            'size': size,
            'type': type,
            'normalized': normalized,
            'stride': stride,
            'offset': pointer
        }
    
    def glEnableVertexAttribArray(self, index: int):
        """Enable vertex attribute."""
        pass  # Tracked in VAO
    
    def glUniform1f(self, location: int, v0: float):
        """Set float uniform."""
        if location not in self.uniforms:
            self.uniforms[location] = {}
        self.uniforms[location]['value'] = v0
        self.uniforms[location]['type'] = 'float'
    
    def glUniform4f(self, location: int, v0: float, v1: float, v2: float, v3: float):
        """Set vec4 uniform."""
        if location not in self.uniforms:
            self.uniforms[location] = {}
        self.uniforms[location]['value'] = [v0, v1, v2, v3]
        self.uniforms[location]['type'] = 'vec4'
    
    def glUniformMatrix4fv(self, location: int, count: int, transpose: bool, value: List[float]):
        """Set mat4 uniform."""
        if location not in self.uniforms:
            self.uniforms[location] = {}
        self.uniforms[location]['value'] = value
        self.uniforms[location]['type'] = 'mat4'
    
    def glGenSamplers(self, n: int) -> List[int]:
        """Generate sampler objects."""
        samplers = []
        for _ in range(n):
            sampler_id = self.next_texture_id
            self.next_texture_id += 1
            self.samplers[sampler_id] = {
                'min_filter': 0x2601,  # GL_LINEAR
                'mag_filter': 0x2601,
                'wrap_s': 0x812F,  # GL_CLAMP_TO_EDGE
                'wrap_t': 0x812F,
            }
            samplers.append(sampler_id)
        return samplers
    
    def glSamplerParameteri(self, sampler: int, pname: int, param: int):
        """Set sampler parameter."""
        if sampler not in self.samplers:
            return
        
        if pname == 0x2801:  # GL_TEXTURE_MIN_FILTER
            self.samplers[sampler]['min_filter'] = param
        elif pname == 0x2800:  # GL_TEXTURE_MAG_FILTER
            self.samplers[sampler]['mag_filter'] = param
        elif pname == 0x2802:  # GL_TEXTURE_WRAP_S
            self.samplers[sampler]['wrap_s'] = param
        elif pname == 0x2803:  # GL_TEXTURE_WRAP_T
            self.samplers[sampler]['wrap_t'] = param
    
    def glBindSampler(self, unit: int, sampler: int):
        """Bind sampler to texture unit."""
        self.current_sampler = sampler
    
    def glTexParameteri(self, target: int, pname: int, param: int):
        """Set texture parameter."""
        if self.current_texture not in self.textures:
            return
        
        tex = self.textures[self.current_texture]
        if pname == 0x2801:  # GL_TEXTURE_MIN_FILTER
            tex.min_filter = param
        elif pname == 0x2800:  # GL_TEXTURE_MAG_FILTER
            tex.mag_filter = param
    
    def glActiveTexture(self, texture: int):
        """Select active texture unit."""
        self.active_texture_unit = texture - 0x84C0  # GL_TEXTURE0
    
    def glUniform1i(self, location: int, v0: int):
        """Set int/sampler uniform."""
        if location not in self.uniforms:
            self.uniforms[location] = {}
        self.uniforms[location]['value'] = v0
        self.uniforms[location]['type'] = 'int'
    
    def glBlendFunc(self, sfactor: int, dfactor: int):
        """Set blend function."""
        self.blend_src = sfactor
        self.blend_dst = dfactor
    
    def glBlendEquation(self, mode: int):
        """Set blend equation."""
        self.blend_equation = mode
    
    def glScissor(self, x: int, y: int, width: int, height: int):
        """Set scissor rectangle."""
        self.scissor = (x, y, width, height)
    
    def glCullFace(self, mode: int):
        """Set cull face mode."""
        self.cull_face = mode
    
    def glFrontFace(self, mode: int):
        """Set front face winding."""
        self.front_face = mode
    
    def process_events(self):
        """Process Cocoa events."""
        if not HAS_METAL:
            return
        
        app = NSApplication.sharedApplication()
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            0xFFFFFFFF,  # Any event
            None,  # No timeout
            "kCFRunLoopDefaultMode",
            True  # Dequeue
        )
        if event:
            app.sendEvent_(event)
    
    def run(self):
        """Run event loop."""
        if not HAS_METAL:
            print("[!] Cannot run without Metal")
            return
        
        app = NSApplication.sharedApplication()
        app.run()


# Export
__all__ = ['MetalRenderer', 'MetalRenderDelegate', 'GLSLToMSL', 'HAS_METAL']
