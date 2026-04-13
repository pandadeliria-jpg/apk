#!/usr/bin/env python3
"""
DEX Class Data Item Parser
Parses class_data_item which contains method code
"""
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import IntEnum

class AccessFlags(IntEnum):
    """Method/field access flags."""
    PUBLIC = 0x1
    PRIVATE = 0x2
    PROTECTED = 0x4
    STATIC = 0x8
    FINAL = 0x10
    SYNCHRONIZED = 0x20
    BRIDGE = 0x40
    VARARGS = 0x80
    NATIVE = 0x100
    INTERFACE = 0x200
    ABSTRACT = 0x400
    STRICTFP = 0x800
    SYNTHETIC = 0x1000
    ANNOTATION = 0x2000
    ENUM = 0x4000
    CONSTRUCTOR = 0x10000
    DECLARED_SYNCHRONIZED = 0x20000


def read_uleb128(data: bytes, offset: int) -> tuple:
    """Read unsigned LEB128 value."""
    result = 0
    shift = 0
    count = 0
    while True:
        byte = data[offset + count]
        count += 1
        result |= (byte & 0x7f) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result, count


def read_sleb128(data: bytes, offset: int) -> tuple:
    """Read signed LEB128 value."""
    result = 0
    shift = 0
    count = 0
    while True:
        byte = data[offset + count]
        count += 1
        result |= (byte & 0x7f) << shift
        shift += 7
        if (byte & 0x80) == 0:
            if byte & 0x40:
                result |= -(1 << shift)
            break
    return result, count


@dataclass
class EncodedField:
    """Encoded field structure."""
    field_idx_diff: int  # uleb128 - index into field_ids
    access_flags: int    # uleb128
    
    # Resolved
    field_idx: int = 0
    name: str = ""
    type_desc: str = ""


@dataclass
class EncodedMethod:
    """Encoded method structure."""
    method_idx_diff: int  # uleb128 - index into method_ids
    access_flags: int     # uleb128
    code_off: int         # uleb128 - offset to code_item or 0
    
    # Resolved
    method_idx: int = 0
    name: str = ""
    class_name: str = ""
    proto_desc: str = ""
    is_direct: bool = False
    
    # Code item (if present)
    code_item: Optional['CodeItem'] = None


@dataclass
class TryItem:
    """Exception try item."""
    start_addr: int   # u4
    insn_count: int   # u2
    handler_off: int  # u2


@dataclass
class CatchHandler:
    """Exception catch handler."""
    size: int  # sleb128 - number of catch types (negative if catch-all present)
    handlers: List[tuple] = field(default_factory=list)  # (type_idx, addr) pairs
    catch_all_addr: Optional[int] = None


@dataclass
class CodeItem:
    """
    Method code item structure.
    This is the actual bytecode of a method!
    """
    registers_size: int  # u2
    ins_size: int        # u2
    outs_size: int       # u2
    tries_size: int      # u2
    debug_info_off: int  # u4
    insns_size: int      # u4 - number of 16-bit code units
    insns: bytes         # actual bytecode!
    
    # Optional try/catch
    tries: List[TryItem] = field(default_factory=list)
    catch_handlers: List[CatchHandler] = field(default_factory=list)
    
    def get_bytecode(self) -> bytes:
        """Get raw bytecode."""
        return self.insns
    
    def disassemble(self, dex_loader) -> List[str]:
        """Simple disassembly of bytecode."""
        from interpreter import OpCode
        
        result = []
        pc = 0
        while pc < len(self.insns):
            if pc + 1 >= len(self.insns):
                break
            
            opcode = self.insns[pc]
            opcode_name = OpCode(opcode).name if opcode in [o.value for o in OpCode] else f"UNK_{hex(opcode)}"
            
            # Determine instruction size (simplified)
            if opcode in [0x00, 0x01, 0x04, 0x07, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11]:
                size = 2
            elif opcode in [0x12, 0x21]:
                size = 2
            elif opcode in [0x13, 0x16, 0x1a, 0x1f, 0x22, 0x28]:
                size = 4
            elif opcode in [0x14, 0x17, 0x1b, 0x2a]:
                size = 6
            elif opcode in [0x23]:
                size = 4
            elif opcode in [0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d]:
                size = 4
            elif opcode in [0x6e, 0x6f, 0x70, 0x71, 0x72]:
                size = 6
            elif opcode in [0x90, 0x91, 0x92, 0x93]:
                size = 4
            else:
                size = 2
            
            # Get hex representation
            hex_bytes = ' '.join(f'{b:02x}' for b in self.insns[pc:pc+min(size, 8)])
            result.append(f"{pc:04x}: {opcode_name:20s} {hex_bytes}")
            
            pc += size
        
        return result


@dataclass
class ClassDataItem:
    """
    class_data_item structure.
    Contains all fields and methods for a class.
    """
    static_fields_size: int   # uleb128
    instance_fields_size: int # uleb128
    direct_methods_size: int  # uleb128
    virtual_methods_size: int # uleb128
    
    static_fields: List[EncodedField] = field(default_factory=list)
    instance_fields: List[EncodedField] = field(default_factory=list)
    direct_methods: List[EncodedMethod] = field(default_factory=list)
    virtual_methods: List[EncodedMethod] = field(default_factory=list)


class ClassDataParser:
    """Parse class_data_item from DEX."""
    
    def __init__(self, data: bytes, dex_loader):
        self.data = data
        self.dex = dex_loader
    
    def parse_class_data(self, offset: int) -> Optional[ClassDataItem]:
        """Parse class_data_item at given offset."""
        if offset == 0:
            return None
        
        pos = offset
        
        # Read sizes
        static_fields_size, count = read_uleb128(self.data, pos)
        pos += count
        
        instance_fields_size, count = read_uleb128(self.data, pos)
        pos += count
        
        direct_methods_size, count = read_uleb128(self.data, pos)
        pos += count
        
        virtual_methods_size, count = read_uleb128(self.data, pos)
        pos += count
        
        item = ClassDataItem(
            static_fields_size=static_fields_size,
            instance_fields_size=instance_fields_size,
            direct_methods_size=direct_methods_size,
            virtual_methods_size=virtual_methods_size
        )
        
        # Parse static fields
        prev_idx = 0
        for _ in range(static_fields_size):
            field, pos = self._parse_encoded_field(pos, prev_idx)
            item.static_fields.append(field)
            prev_idx = field.field_idx
        
        # Parse instance fields
        prev_idx = 0
        for _ in range(instance_fields_size):
            field, pos = self._parse_encoded_field(pos, prev_idx)
            item.instance_fields.append(field)
            prev_idx = field.field_idx
        
        # Parse direct methods
        prev_idx = 0
        for _ in range(direct_methods_size):
            method, pos = self._parse_encoded_method(pos, prev_idx, is_direct=True)
            item.direct_methods.append(method)
            prev_idx = method.method_idx
        
        # Parse virtual methods
        prev_idx = 0
        for _ in range(virtual_methods_size):
            method, pos = self._parse_encoded_method(pos, prev_idx, is_direct=False)
            item.virtual_methods.append(method)
            prev_idx = method.method_idx
        
        return item
    
    def _parse_encoded_field(self, offset: int, prev_idx: int) -> tuple:
        """Parse encoded_field."""
        idx_diff, count1 = read_uleb128(self.data, offset)
        access_flags, count2 = read_uleb128(self.data, offset + count1)
        
        field_idx = prev_idx + idx_diff
        
        field = EncodedField(
            field_idx_diff=idx_diff,
            access_flags=access_flags,
            field_idx=field_idx
        )
        
        # Resolve field info
        if field_idx < len(self.dex.field_ids):
            f = self.dex.field_ids[field_idx]
            field.name = self.dex.strings[f.name_idx] if f.name_idx < len(self.dex.strings) else f"<field_{f.name_idx}>"
            field.type_desc = self.dex.types[f.type_idx] if f.type_idx < len(self.dex.types) else f"<type_{f.type_idx}>"
        
        return field, offset + count1 + count2
    
    def _parse_encoded_method(self, offset: int, prev_idx: int, is_direct: bool) -> tuple:
        """Parse encoded_method."""
        idx_diff, count1 = read_uleb128(self.data, offset)
        access_flags, count2 = read_uleb128(self.data, offset + count1)
        code_off, count3 = read_uleb128(self.data, offset + count1 + count2)
        
        method_idx = prev_idx + idx_diff
        
        method = EncodedMethod(
            method_idx_diff=idx_diff,
            access_flags=access_flags,
            code_off=code_off,
            method_idx=method_idx,
            is_direct=is_direct
        )
        
        # Resolve method info
        if method_idx < len(self.dex.method_ids):
            m = self.dex.method_ids[method_idx]
            method.name = self.dex.strings[m.name_idx] if m.name_idx < len(self.dex.strings) else f"<method_{m.name_idx}>"
            method.class_name = self.dex.types[m.class_idx] if m.class_idx < len(self.dex.types) else f"<class_{m.class_idx}>"
            # Get prototype description
            if m.proto_idx < len(self.dex.proto_ids):
                proto = self.dex.proto_ids[m.proto_idx]
                param_types = proto.get('param_types', [])
                return_type = proto.get('return_type', 0)
                method.proto_desc = f"({','.join(self.dex.types[t] for t in param_types)}){self.dex.types[return_type]}"
        
        # Parse code item if present
        if code_off > 0:
            method.code_item = self._parse_code_item(code_off)
        
        return method, offset + count1 + count2 + count3
    
    def _parse_code_item(self, offset: int) -> CodeItem:
        """Parse code_item at given offset."""
        pos = offset
        
        registers_size = struct.unpack('<H', self.data[pos:pos+2])[0]
        pos += 2
        
        ins_size = struct.unpack('<H', self.data[pos:pos+2])[0]
        pos += 2
        
        outs_size = struct.unpack('<H', self.data[pos:pos+2])[0]
        pos += 2
        
        tries_size = struct.unpack('<H', self.data[pos:pos+2])[0]
        pos += 2
        
        debug_info_off = struct.unpack('<I', self.data[pos:pos+4])[0]
        pos += 4
        
        insns_size = struct.unpack('<I', self.data[pos:pos+4])[0]
        pos += 4
        
        # Read bytecode (insns_size is in 16-bit code units)
        bytecode_size = insns_size * 2
        insns = self.data[pos:pos+bytecode_size]
        pos += bytecode_size
        
        code_item = CodeItem(
            registers_size=registers_size,
            ins_size=ins_size,
            outs_size=outs_size,
            tries_size=tries_size,
            debug_info_off=debug_info_off,
            insns_size=insns_size,
            insns=insns
        )
        
        # Parse try/catch if present
        if tries_size > 0:
            # Align to 4 bytes
            if pos % 4 != 0:
                pos += 4 - (pos % 4)
            
            # Parse try_items
            for _ in range(tries_size):
                start_addr = struct.unpack('<I', self.data[pos:pos+4])[0]
                insn_count = struct.unpack('<H', self.data[pos+4:pos+6])[0]
                handler_off = struct.unpack('<H', self.data[pos+6:pos+8])[0]
                code_item.tries.append(TryItem(start_addr, insn_count, handler_off))
                pos += 8
            
            # Parse catch handlers
            handlers_size, count = read_uleb128(self.data, pos)
            pos += count
            
            for _ in range(abs(handlers_size)):
                handler = CatchHandler(size=handlers_size)
                # Parse handler items...
                code_item.catch_handlers.append(handler)
        
        return code_item


# Need to add proto_ids parsing to DEXLoader
# Add this to dex_interpreter.py
