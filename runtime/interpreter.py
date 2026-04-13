#!/usr/bin/env python3
"""
Dalvik Bytecode Interpreter
Executes Dalvik bytecode instructions
"""
import struct
from typing import Dict, List, Any, Optional, Callable
from enum import IntEnum
from dataclasses import dataclass, field

class OpCode(IntEnum):
    """Dalvik bytecode opcodes."""
    NOP = 0x00
    MOVE = 0x01
    MOVE_FROM16 = 0x02
    MOVE_16 = 0x03
    MOVE_WIDE = 0x04
    MOVE_WIDE_FROM16 = 0x05
    MOVE_WIDE_16 = 0x06
    MOVE_OBJECT = 0x07
    MOVE_OBJECT_FROM16 = 0x08
    MOVE_OBJECT_16 = 0x09
    MOVE_RESULT = 0x0a
    MOVE_RESULT_WIDE = 0x0b
    MOVE_RESULT_OBJECT = 0x0c
    MOVE_EXCEPTION = 0x0d
    RETURN_VOID = 0x0e
    RETURN = 0x0f
    RETURN_WIDE = 0x10
    RETURN_OBJECT = 0x11
    CONST_4 = 0x12
    CONST_16 = 0x13
    CONST = 0x14
    CONST_HIGH16 = 0x15
    CONST_WIDE_16 = 0x16
    CONST_WIDE_32 = 0x17
    CONST_WIDE = 0x18
    CONST_WIDE_HIGH16 = 0x19
    CONST_STRING = 0x1a
    CONST_STRING_JUMBO = 0x1b
    CONST_CLASS = 0x1c
    MONITOR_ENTER = 0x1d
    MONITOR_EXIT = 0x1e
    CHECK_CAST = 0x1f
    INSTANCE_OF = 0x20
    ARRAY_LENGTH = 0x21
    NEW_INSTANCE = 0x22
    NEW_ARRAY = 0x23
    FILLED_NEW_ARRAY = 0x24
    FILLED_NEW_ARRAY_RANGE = 0x25
    FILL_ARRAY_DATA = 0x26
    THROW = 0x27
    GOTO = 0x28
    GOTO_16 = 0x29
    GOTO_32 = 0x2a
    PACKED_SWITCH = 0x2b
    SPARSE_SWITCH = 0x2c
    IF_EQ = 0x32
    IF_NE = 0x33
    IF_LT = 0x34
    IF_GE = 0x35
    IF_GT = 0x36
    IF_LE = 0x37
    IF_EQZ = 0x38
    IF_NEZ = 0x39
    IF_LTZ = 0x3a
    IF_GEZ = 0x3b
    IF_GTZ = 0x3c
    IF_LEZ = 0x3d
    AGET = 0x44
    AGET_WIDE = 0x45
    AGET_OBJECT = 0x46
    AGET_BOOLEAN = 0x47
    AGET_BYTE = 0x48
    AGET_CHAR = 0x49
    AGET_SHORT = 0x4a
    APUT = 0x4b
    APUT_WIDE = 0x4c
    APUT_OBJECT = 0x4d
    APUT_BOOLEAN = 0x4e
    APUT_BYTE = 0x4f
    APUT_CHAR = 0x50
    APUT_SHORT = 0x51
    IGET = 0x52
    IGET_WIDE = 0x53
    IGET_OBJECT = 0x54
    IGET_BOOLEAN = 0x55
    IGET_BYTE = 0x56
    IGET_CHAR = 0x57
    IGET_SHORT = 0x58
    IPUT = 0x59
    IPUT_WIDE = 0x5a
    IPUT_OBJECT = 0x5b
    IPUT_BOOLEAN = 0x5c
    IPUT_BYTE = 0x5d
    IPUT_CHAR = 0x5e
    IPUT_SHORT = 0x5f
    SGET = 0x60
    SGET_WIDE = 0x61
    SGET_OBJECT = 0x62
    SGET_BOOLEAN = 0x63
    SGET_BYTE = 0x64
    SGET_CHAR = 0x65
    SGET_SHORT = 0x66
    SPUT = 0x67
    SPUT_WIDE = 0x68
    SPUT_OBJECT = 0x69
    SPUT_BOOLEAN = 0x6a
    SPUT_BYTE = 0x6b
    SPUT_CHAR = 0x6c
    SPUT_SHORT = 0x6d
    INVOKE_VIRTUAL = 0x6e
    INVOKE_SUPER = 0x6f
    INVOKE_DIRECT = 0x70
    INVOKE_STATIC = 0x71
    INVOKE_INTERFACE = 0x72
    INVOKE_VIRTUAL_RANGE = 0x74
    INVOKE_SUPER_RANGE = 0x75
    INVOKE_DIRECT_RANGE = 0x76
    INVOKE_STATIC_RANGE = 0x77
    INVOKE_INTERFACE_RANGE = 0x78
    NEG_INT = 0x7b
    NOT_INT = 0x7c
    NEG_LONG = 0x7d
    NOT_LONG = 0x7e
    NEG_FLOAT = 0x7f
    NEG_DOUBLE = 0x80
    INT_TO_LONG = 0x81
    INT_TO_FLOAT = 0x82
    INT_TO_DOUBLE = 0x83
    LONG_TO_INT = 0x84
    LONG_TO_FLOAT = 0x85
    LONG_TO_DOUBLE = 0x86
    FLOAT_TO_INT = 0x87
    FLOAT_TO_LONG = 0x88
    FLOAT_TO_DOUBLE = 0x89
    DOUBLE_TO_INT = 0x8a
    DOUBLE_TO_LONG = 0x8b
    DOUBLE_TO_FLOAT = 0x8c
    INT_TO_BYTE = 0x8d
    INT_TO_CHAR = 0x8e
    INT_TO_SHORT = 0x8f
    ADD_INT = 0x90
    SUB_INT = 0x91
    MUL_INT = 0x92
    DIV_INT = 0x93
    REM_INT = 0x94
    AND_INT = 0x95
    OR_INT = 0x96
    XOR_INT = 0x97
    SHL_INT = 0x98
    SHR_INT = 0x99
    USHR_INT = 0x9a
    ADD_LONG = 0x9b
    SUB_LONG = 0x9c
    MUL_LONG = 0x9d
    DIV_LONG = 0x9e
    REM_LONG = 0x9f
    AND_LONG = 0xa0
    OR_LONG = 0xa1
    XOR_LONG = 0xa2
    SHL_LONG = 0xa3
    SHR_LONG = 0xa4
    USHR_LONG = 0xa5
    ADD_FLOAT = 0xa6
    SUB_FLOAT = 0xa7
    MUL_FLOAT = 0xa8
    DIV_FLOAT = 0xa9
    REM_FLOAT = 0xaa
    ADD_DOUBLE = 0xab
    SUB_DOUBLE = 0xac
    MUL_DOUBLE = 0xad
    DIV_DOUBLE = 0xae
    REM_DOUBLE = 0xaf


@dataclass
class Frame:
    """Stack frame for method execution."""
    method_name: str
    registers: List[Any] = field(default_factory=list)
    pc: int = 0  # Program counter
    result: Any = None  # For move-result
    
    def __init__(self, method_name: str, num_regs: int = 16):
        self.method_name = method_name
        self.registers = [None] * num_regs
        self.pc = 0
        self.result = None


class JavaObject:
    """Represents a Java object in the interpreter."""
    def __init__(self, class_name: str, fields: Dict[str, Any] = None):
        self.class_name = class_name
        self.fields = fields or {}
    
    def __repr__(self):
        return f"JavaObject({self.class_name})"


class JavaArray:
    """Represents a Java array."""
    def __init__(self, element_type: str, length: int):
        self.element_type = element_type
        self.data = [None] * length
    
    def __repr__(self):
        return f"JavaArray({self.element_type}[{len(self.data)}])"


class JNIEnvironment:
    """
    JNI (Java Native Interface) bridge.
    Handles calls between Java bytecode and native code.
    """
    
    def __init__(self):
        self.native_methods: Dict[str, Callable] = {}
        self.objects: Dict[int, Any] = {}
        self.next_object_id = 1
        self._register_native_methods()
    
    def _register_native_methods(self):
        """Register native method implementations."""
        # System methods
        self.register("java/lang/System.currentTimeMillis()J", self._current_time_millis)
        self.register("java/lang/System.nanoTime()J", self._nano_time)
        self.register("java/lang/System.arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V", self._arraycopy)
        
        # Object methods
        self.register("java/lang/Object.getClass()Ljava/lang/Class;", self._object_get_class)
        self.register("java/lang/Object.hashCode()I", self._object_hash_code)
        self.register("java/lang/Object.clone()Ljava/lang/Object;", self._object_clone)
        
        # String methods
        self.register("java/lang/String.<init>()V", self._string_init)
        self.register("java/lang/String.<init>([B)V", self._string_init_bytes)
        self.register("java/lang/String.length()I", self._string_length)
        self.register("java/lang/String.charAt(I)C", self._string_char_at)
        
        # Thread methods
        self.register("java/lang/Thread.currentThread()Ljava/lang/Thread;", self._thread_current)
        
        # Android-specific
        self.register("android/os/Looper.prepare()V", self._looper_prepare)
        self.register("android/os/Looper.loop()V", self._looper_loop)
        
        # Debug
        self.register("android/util/Log.d(Ljava/lang/String;Ljava/lang/String;)I", self._log_d)
        self.register("android/util/Log.e(Ljava/lang/String;Ljava/lang/String;)I", self._log_e)
    
    def register(self, signature: str, func: Callable):
        """Register a native method."""
        self.native_methods[signature] = func
    
    def call(self, signature: str, args: List[Any]) -> Any:
        """Call a native method."""
        if signature in self.native_methods:
            try:
                return self.native_methods[signature](*args)
            except Exception as e:
                print(f"[!] Native method error {signature}: {e}")
                return None
        else:
            print(f"[!] Unimplemented native: {signature}")
            return None
    
    def new_object(self, obj: Any) -> int:
        """Create new object reference."""
        obj_id = self.next_object_id
        self.objects[obj_id] = obj
        self.next_object_id += 1
        return obj_id
    
    def get_object(self, obj_id: int) -> Any:
        """Get object by ID."""
        return self.objects.get(obj_id)
    
    # === Native Method Implementations ===
    
    def _current_time_millis(self) -> int:
        import time
        return int(time.time() * 1000)
    
    def _nano_time(self) -> int:
        import time
        return int(time.time() * 1e9)
    
    def _arraycopy(self, src, src_pos, dst, dst_pos, length):
        if isinstance(src, list) and isinstance(dst, list):
            for i in range(length):
                if dst_pos + i < len(dst):
                    dst[dst_pos + i] = src[src_pos + i] if src_pos + i < len(src) else None
    
    def _object_get_class(self, obj):
        return JavaObject("java/lang/Class", {"name": obj.class_name if isinstance(obj, JavaObject) else type(obj).__name__})
    
    def _object_hash_code(self, obj):
        return id(obj) & 0xFFFFFFFF
    
    def _object_clone(self, obj):
        import copy
        return copy.deepcopy(obj)
    
    def _string_init(self):
        return ""
    
    def _string_init_bytes(self, bytes_array):
        if isinstance(bytes_array, JavaArray):
            return "".join(chr(b) for b in bytes_array.data if b is not None)
        return ""
    
    def _string_length(self, s):
        return len(s) if isinstance(s, str) else 0
    
    def _string_char_at(self, s, index):
        return ord(s[index]) if isinstance(s, str) and index < len(s) else 0
    
    def _thread_current(self):
        return JavaObject("java/lang/Thread", {"name": "main"})
    
    def _looper_prepare(self):
        print("[JNI] Looper.prepare()")
    
    def _looper_loop(self):
        print("[JNI] Looper.loop() - would block forever")
    
    def _log_d(self, tag, msg):
        t = tag if isinstance(tag, str) else "?"
        m = msg if isinstance(msg, str) else "?"
        print(f"[D/{t}] {m}")
        return 0
    
    def _log_e(self, tag, msg):
        t = tag if isinstance(tag, str) else "?"
        m = msg if isinstance(msg, str) else "?"
        print(f"[E/{t}] {m}")
        return 0


class Interpreter:
    """
    Dalvik bytecode interpreter.
    Executes DEX bytecode instructions one by one.
    """
    
    def __init__(self, dex_loader):
        self.dex = dex_loader
        self.jni = JNIEnvironment()
        self.frames: List[Frame] = []
        self.class_objects: Dict[str, JavaObject] = {}
        self.static_fields: Dict[str, Any] = {}
        self.running = False
        
    def execute_method(self, method_name: str, code: bytes, args: List[Any] = None) -> Any:
        """
        Execute a method's bytecode.
        
        Args:
            method_name: Name of method for debugging
            code: Bytecode instructions
            args: Arguments to pass (go into registers v0, v1, ...)
        
        Returns:
            Return value of method
        """
        frame = Frame(method_name, num_regs=16)
        
        # Set up arguments in registers
        if args:
            for i, arg in enumerate(args[:16]):
                frame.registers[i] = arg
        
        self.frames.append(frame)
        
        print(f"[*] Executing {method_name} ({len(code)} bytes)")
        
        try:
            self._execute_bytecode(code, frame)
        except Exception as e:
            print(f"[!] Execution error in {method_name}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.frames.pop()
        
        return frame.result
    
    def _execute_bytecode(self, code: bytes, frame: Frame):
        """Execute bytecode instructions."""
        self.running = True
        
        while self.running and frame.pc < len(code):
            try:
                opcode = code[frame.pc]
                
                # Execute instruction
                next_pc = self._execute_instruction(opcode, code, frame, frame.pc)
                
                if next_pc < 0:
                    # Stop execution
                    break
                else:
                    frame.pc = next_pc
                    
            except Exception as e:
                print(f"[!] Instruction error at {frame.pc}: opcode={hex(opcode)}, error={e}")
                break
    
    def _execute_instruction(self, opcode: int, code: bytes, frame: Frame, pc: int) -> int:
        """
        Execute a single instruction.
        Returns next PC, or -1 to stop.
        """
        
        # Format constants
        def nibble_high(b): return (b >> 4) & 0x0f
        def nibble_low(b): return b & 0x0f
        def ubyte(code, idx): return code[idx]
        def ushort(code, idx): return struct.unpack('<H', code[idx:idx+2])[0]
        def short(code, idx): return struct.unpack('<h', code[idx:idx+2])[0]
        def uint(code, idx): return struct.unpack('<I', code[idx:idx+4])[0]
        def sint(code, idx): return struct.unpack('<i', code[idx:idx+4])[0]
        
        import struct
        
        # Simple instructions
        if opcode == OpCode.NOP:
            return pc + 2
        
        elif opcode == OpCode.MOVE:  # 0x01: move vA, vB
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            frame.registers[a] = frame.registers[b]
            return pc + 2
        
        elif opcode == OpCode.MOVE_OBJECT:  # 0x07: move-object vA, vB
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            frame.registers[a] = frame.registers[b]
            return pc + 2
        
        elif opcode == OpCode.MOVE_RESULT:  # 0x0a: move-result vAA
            aa = ubyte(code, pc + 1)
            frame.registers[aa] = frame.result
            return pc + 2
        
        elif opcode == OpCode.MOVE_RESULT_OBJECT:  # 0x0c: move-result-object vAA
            aa = ubyte(code, pc + 1)
            frame.registers[aa] = frame.result
            return pc + 2
        
        elif opcode == OpCode.RETURN_VOID:  # 0x0e: return-void
            return -1
        
        elif opcode == OpCode.RETURN:  # 0x0f: return vAA
            aa = ubyte(code, pc + 1)
            frame.result = frame.registers[aa]
            return -1
        
        elif opcode == OpCode.RETURN_OBJECT:  # 0x11: return-object vAA
            aa = ubyte(code, pc + 1)
            frame.result = frame.registers[aa]
            return -1
        
        elif opcode == OpCode.CONST_4:  # 0x12: const/4 vA, #+B
            b = nibble_high(code[pc + 1])
            a = nibble_low(code[pc + 1])
            # Sign extend 4-bit to 32-bit
            value = b if b < 8 else b - 16
            frame.registers[a] = value
            return pc + 2
        
        elif opcode == OpCode.CONST_16:  # 0x13: const/16 vAA, #+BBBB
            aa = ubyte(code, pc + 1)
            bbbb = short(code, pc + 2)
            frame.registers[aa] = bbbb
            return pc + 4
        
        elif opcode == OpCode.CONST:  # 0x14: const vAA, #+BBBBBBBB
            aa = ubyte(code, pc + 1)
            bbbbbbbb = sint(code, pc + 2)
            frame.registers[aa] = bbbbbbbb
            return pc + 6
        
        elif opcode == OpCode.CONST_STRING:  # 0x1a: const-string vAA, string@BBBB
            aa = ubyte(code, pc + 1)
            bbbb = ushort(code, pc + 2)
            if bbbb < len(self.dex.strings):
                frame.registers[aa] = self.dex.strings[bbbb]
            else:
                frame.registers[aa] = f"<string_{bbbb}>"
            return pc + 4
        
        elif opcode == OpCode.NEW_INSTANCE:  # 0x22: new-instance vAA, type@BBBB
            aa = ubyte(code, pc + 1)
            bbbb = ushort(code, pc + 2)
            if bbbb < len(self.dex.types):
                class_name = self.dex.types[bbbb]
                frame.registers[aa] = JavaObject(class_name)
            else:
                frame.registers[aa] = JavaObject(f"<type_{bbbb}>")
            return pc + 4
        
        elif opcode == OpCode.NEW_ARRAY:  # 0x23: new-array vA, vB, type@CCCC
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            cccc = ushort(code, pc + 2)
            length = frame.registers[b]
            if isinstance(length, int) and length >= 0:
                element_type = self.dex.types[cccc] if cccc < len(self.dex.types) else "java/lang/Object"
                frame.registers[a] = JavaArray(element_type, length)
            else:
                frame.registers[a] = None
            return pc + 4
        
        elif opcode == OpCode.AGET_OBJECT:  # 0x46: aget-object vAA, vBB, vCC
            aa = ubyte(code, pc + 1)
            bb = ubyte(code, pc + 2)
            cc = ubyte(code, pc + 3)
            arr = frame.registers[bb]
            idx = frame.registers[cc]
            if isinstance(arr, JavaArray) and isinstance(idx, int):
                frame.registers[aa] = arr.data[idx] if 0 <= idx < len(arr.data) else None
            else:
                frame.registers[aa] = None
            return pc + 4
        
        elif opcode == OpCode.APUT_OBJECT:  # 0x4e: aput-object vAA, vBB, vCC
            aa = ubyte(code, pc + 1)
            bb = ubyte(code, pc + 2)
            cc = ubyte(code, pc + 3)
            value = frame.registers[aa]
            arr = frame.registers[bb]
            idx = frame.registers[cc]
            if isinstance(arr, JavaArray) and isinstance(idx, int) and 0 <= idx < len(arr.data):
                arr.data[idx] = value
            return pc + 4
        
        elif opcode == OpCode.IGET_OBJECT:  # 0x54: iget-object vA, vB, field@CCCC
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            cccc = ushort(code, pc + 2)
            obj = frame.registers[b]
            if isinstance(obj, JavaObject):
                field_name = f"field_{cccc}"
                frame.registers[a] = obj.fields.get(field_name)
            else:
                frame.registers[a] = None
            return pc + 4
        
        elif opcode == OpCode.IPUT_OBJECT:  # 0x5b: iput-object vA, vB, field@CCCC
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            cccc = ushort(code, pc + 2)
            value = frame.registers[a]
            obj = frame.registers[b]
            if isinstance(obj, JavaObject):
                field_name = f"field_{cccc}"
                obj.fields[field_name] = value
            return pc + 4
        
        elif opcode == OpCode.SGET_OBJECT:  # 0x62: sget-object vAA, field@BBBB
            aa = ubyte(code, pc + 1)
            bbbb = ushort(code, pc + 2)
            field_name = f"static_{bbbb}"
            frame.registers[aa] = self.static_fields.get(field_name)
            return pc + 4
        
        elif opcode == OpCode.ADD_INT:  # 0x90: add-int vAA, vBB, vCC
            aa = ubyte(code, pc + 1)
            bb = ubyte(code, pc + 2)
            cc = ubyte(code, pc + 3)
            vb = frame.registers[bb]
            vc = frame.registers[cc]
            if isinstance(vb, int) and isinstance(vc, int):
                frame.registers[aa] = vb + vc
            else:
                frame.registers[aa] = 0
            return pc + 4
        
        elif opcode == OpCode.SUB_INT:  # 0x91
            aa = ubyte(code, pc + 1)
            bb = ubyte(code, pc + 2)
            cc = ubyte(code, pc + 3)
            vb = frame.registers[bb]
            vc = frame.registers[cc]
            if isinstance(vb, int) and isinstance(vc, int):
                frame.registers[aa] = vb - vc
            else:
                frame.registers[aa] = 0
            return pc + 4
        
        elif opcode == OpCode.MUL_INT:  # 0x92
            aa = ubyte(code, pc + 1)
            bb = ubyte(code, pc + 2)
            cc = ubyte(code, pc + 3)
            vb = frame.registers[bb]
            vc = frame.registers[cc]
            if isinstance(vb, int) and isinstance(vc, int):
                frame.registers[aa] = vb * vc
            else:
                frame.registers[aa] = 0
            return pc + 4
        
        elif opcode == OpCode.GOTO:  # 0x28: goto +AA
            aa = struct.unpack('b', bytes([code[pc + 1]]))[0]
            return pc + (aa * 2)
        
        elif opcode == OpCode.GOTO_16:  # 0x29: goto/16 +AAAA
            aaaa = short(code, pc + 2)
            return pc + (aaaa * 2)
        
        elif opcode == OpCode.IF_EQ:  # 0x32: if-eq vA, vB, +CCCC
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            cccc = short(code, pc + 2)
            if frame.registers[a] == frame.registers[b]:
                return pc + (cccc * 2)
            return pc + 4
        
        elif opcode == OpCode.IF_NE:  # 0x33: if-ne vA, vB, +CCCC
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            cccc = short(code, pc + 2)
            if frame.registers[a] != frame.registers[b]:
                return pc + (cccc * 2)
            return pc + 4
        
        elif opcode == OpCode.IF_EQZ:  # 0x38: if-eqz vAA, +BBBB
            aa = ubyte(code, pc + 1)
            bbbb = short(code, pc + 2)
            val = frame.registers[aa]
            if val is None or val == 0 or val == False:
                return pc + (bbbb * 2)
            return pc + 4
        
        elif opcode in (OpCode.INVOKE_VIRTUAL, OpCode.INVOKE_DIRECT, OpCode.INVOKE_STATIC, OpCode.INVOKE_INTERFACE):
            # Method invocation - simplified
            # Format: op AA, BB, method@CCCC for 35c format
            a = nibble_high(code[pc + 1])
            g = nibble_low(code[pc + 1])
            bbbb = ushort(code, pc + 2)
            f = nibble_high(code[pc + 4])
            e = nibble_low(code[pc + 4])
            d = nibble_high(code[pc + 5])
            c = nibble_low(code[pc + 5])
            
            # Get method info
            if bbbb < len(self.dex.method_ids):
                method = self.dex.method_ids[bbbb]
                class_name = self.dex.types[method.class_idx]
                method_name = self.dex.strings[method.name_idx]
                
                # Build argument list
                args = []
                arg_regs = [d, e, f, g]
                for i in range(a):
                    if i < len(arg_regs):
                        args.append(frame.registers[arg_regs[i]])
                
                # Check for native method
                sig = f"{class_name}.{method_name}"
                result = self.jni.call(sig, args)
                
                if result is not None:
                    frame.result = result
                else:
                    # Not a native method - would need to find and execute bytecode
                    print(f"[!] Unimplemented method: {sig}")
                    frame.result = None
            
            return pc + 6
        
        elif opcode == OpCode.CHECK_CAST:  # 0x1f: check-cast vAA, type@BBBB
            aa = ubyte(code, pc + 1)
            bbbb = ushort(code, pc + 2)
            obj = frame.registers[aa]
            # In real implementation, would verify type
            return pc + 4
        
        elif opcode == OpCode.INSTANCE_OF:  # 0x20: instance-of vA, vB, type@CCCC
            a = nibble_high(code[pc + 1])
            b = nibble_low(code[pc + 1])
            cccc = ushort(code, pc + 2)
            obj = frame.registers[b]
            if cccc < len(self.dex.types):
                target_type = self.dex.types[cccc]
                if isinstance(obj, JavaObject):
                    frame.registers[a] = 1 if obj.class_name == target_type else 0
                else:
                    frame.registers[a] = 0
            return pc + 4
        
        elif opcode == OpCode.INT_TO_LONG:  # 0x81
            aa = ubyte(code, pc + 1)
            bb = ubyte(code, pc + 2)
            val = frame.registers[bb]
            frame.registers[aa] = int(val) if val is not None else 0
            return pc + 4
        
        else:
            print(f"[!] Unimplemented opcode: {hex(opcode)} at {pc}")
            return pc + 2  # Skip unknown instruction


if __name__ == "__main__":
    # Test with a simple DEX
    import sys
    from dex_interpreter import DEXLoader
    
    if len(sys.argv) < 2:
        print("Usage: python3 interpreter.py <classes.dex>")
        sys.exit(1)
    
    # Load DEX
    loader = DEXLoader(sys.argv[1])
    if not loader.load():
        print("[!] Failed to load DEX")
        sys.exit(1)
    
    # Create interpreter
    interp = Interpreter(loader)
    
    print("\n[*] Interpreter ready - would need method code to execute")
    print("[!] Full method code extraction not yet implemented")
