#!/usr/bin/env python3
"""
DEX Bytecode Interpreter
Minimal Dalvik bytecode execution for Android→macOS compatibility
"""
import struct
import mmap
from enum import IntEnum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

class OpCode(IntEnum):
    """Dalvik bytecode opcodes (subset)."""
    # Constants
    CONST_4 = 0x12  # const/4 vA, #+B
    CONST_16 = 0x13  # const/16 vAA, #+BBBB
    CONST = 0x14  # const vAA, #+BBBBBBBB
    CONST_STRING = 0x1a  # const-string vAA, string@BBBB
    
    # Moves
    MOVE = 0x01  # move vA, vB
    MOVE_RESULT = 0x0a  # move-result vAA
    MOVE_RESULT_OBJECT = 0x0c  # move-result-object vAA
    
    # Returns
    RETURN_VOID = 0x0e  # return-void
    RETURN = 0x0f  # return vAA
    RETURN_OBJECT = 0x11  # return-object vAA
    
    # Invokes
    INVOKE_VIRTUAL = 0x6e  # invoke-virtual {vD, vE, vF, vG, vA}, meth@CCCC
    INVOKE_SUPER = 0x6f
    INVOKE_DIRECT = 0x70
    INVOKE_STATIC = 0x71
    INVOKE_INTERFACE = 0x72
    
    # Field access
    IGET_OBJECT = 0x52  # iget-object vA, vB, field@CCCC
    IPUT_OBJECT = 0x5c  # iput-object vA, vB, field@CCCC
    SGET_OBJECT = 0x62  # sget-object vAA, field@BBBB
    
    # Object creation
    NEW_INSTANCE = 0x22  # new-instance vAA, type@BBBB
    
    # Array operations
    NEW_ARRAY = 0x23  # new-array vA, vB, type@CCCC
    AGET_OBJECT = 0x46  # aget-object vAA, vBB, vCC
    APUT_OBJECT = 0x4e  # aput-object vAA, vBB, vCC
    
    # Int operations
    ADD_INT = 0x90  # add-int vAA, vBB, vCC
    SUB_INT = 0x91
    MUL_INT = 0x92
    DIV_INT = 0x93
    
    # Comparisons
    IF_EQ = 0x32  # if-eq vA, vB, +CCCC
    IF_NE = 0x33
    IF_LT = 0x34
    IF_GE = 0x35
    IF_GT = 0x36
    IF_LE = 0x37
    
    # Goto
    GOTO = 0x28  # goto +AA
    GOTO_16 = 0x29  # goto/16 +AAAA
    GOTO_32 = 0x2a  # goto/32 +AAAAAAAA
    
    # Conversions
    INT_TO_LONG = 0x81
    INT_TO_FLOAT = 0x82
    INT_TO_DOUBLE = 0x83
    
    # Check
    CHECK_CAST = 0x1f  # check-cast vAA, type@BBBB
    INSTANCE_OF = 0x20  # instance-of vA, vB, type@CCCC
    
    # Monitor
    MONITOR_ENTER = 0x1d
    MONITOR_EXIT = 0x1e


@dataclass
class DexHeader:
    """DEX file header structure."""
    magic: bytes
    checksum: int
    signature: bytes
    file_size: int
    header_size: int
    endian_tag: int
    link_size: int
    link_off: int
    map_off: int
    string_ids_size: int
    string_ids_off: int
    type_ids_size: int
    type_ids_off: int
    proto_ids_size: int
    proto_ids_off: int
    field_ids_size: int
    field_ids_off: int
    method_ids_size: int
    method_ids_off: int
    class_defs_size: int
    class_defs_off: int
    data_size: int
    data_off: int


@dataclass
class ClassDef:
    """Class definition."""
    class_idx: int
    access_flags: int
    superclass_idx: int
    interfaces_off: int
    source_file_idx: int
    annotations_off: int
    class_data_off: int
    static_values_off: int


@dataclass
class Method:
    """Method definition."""
    class_idx: int
    proto_idx: int
    name_idx: int
    code_off: int = 0
    access_flags: int = 0


@dataclass
class Field:
    """Field definition."""
    class_idx: int
    type_idx: int
    name_idx: int


@dataclass  
class CodeItem:
    """Method code item."""
    registers_size: int
    ins_size: int
    outs_size: int
    tries_size: int
    debug_info_off: int
    insns_size: int
    insns: bytes


class DEXLoader:
    """Load and parse DEX files."""
    
    def __init__(self, dex_path: str):
        self.dex_path = dex_path
        self.data: bytes = b''
        self.header: Optional[DexHeader] = None
        self.string_ids: List[int] = []
        self.strings: List[str] = []
        self.type_ids: List[int] = []
        self.types: List[str] = []
        self.proto_ids: List = []
        self.field_ids: List[Field] = []
        self.method_ids: List[Method] = []
        self.class_defs: List[ClassDef] = []
        self.loaded_classes: Dict[str, Any] = {}
        
    def load(self) -> bool:
        """Load and parse DEX file."""
        print(f"[*] Loading DEX: {self.dex_path}")
        
        try:
            with open(self.dex_path, 'rb') as f:
                self.data = f.read()
        except Exception as e:
            print(f"[!] Failed to load DEX: {e}")
            return False
        
        if len(self.data) < 0x70:
            print("[!] DEX file too small")
            return False
        
        # Parse header
        if not self._parse_header():
            return False
        
        # Parse string table
        self._parse_strings()
        
        # Parse type table
        self._parse_types()
        
        # Parse proto table
        self._parse_protos()
        
        # Parse field table
        self._parse_fields()
        
        # Parse method table
        self._parse_methods()
        
        # Parse class definitions
        self._parse_class_defs()
        
        # Parse class data (method code)
        self._parse_class_data()
        
        print(f"[+] DEX loaded: {len(self.strings)} strings, {len(self.types)} types, {len(self.method_ids)} methods, {len(self.class_defs)} classes")
        return True
    
    def _parse_protos(self):
        """Parse prototype table."""
        self.proto_ids = []
        
        off = self.header.proto_ids_off
        for i in range(self.header.proto_ids_size):
            shorty_idx = struct.unpack('<I', self.data[off:off+4])[0]
            return_type_idx = struct.unpack('<I', self.data[off+4:off+8])[0]
            # Parameters offset points to type_list
            params_off = struct.unpack('<I', self.data[off+8:off+12])[0]
            
            param_types = []
            if params_off != 0:
                # Parse type_list
                size = struct.unpack('<I', self.data[params_off:params_off+4])[0]
                for j in range(size):
                    type_idx = struct.unpack('<H', self.data[params_off+4+j*2:params_off+6+j*2])[0]
                    if type_idx < len(self.types):
                        param_types.append(type_idx)
            
            shorty = self.strings[shorty_idx] if shorty_idx < len(self.strings) else ""
            
            self.proto_ids.append({
                'shorty': shorty,
                'return_type': return_type_idx,
                'param_types': param_types
            })
            off += 12
    
    def _parse_fields(self):
        """Parse field table."""
        self.field_ids = []
        
        off = self.header.field_ids_off
        for i in range(self.header.field_ids_size):
            class_idx = struct.unpack('<H', self.data[off:off+2])[0]
            type_idx = struct.unpack('<H', self.data[off+2:off+4])[0]
            name_idx = struct.unpack('<I', self.data[off+4:off+8])[0]
            
            self.field_ids.append(Field(
                class_idx=class_idx,
                type_idx=type_idx,
                name_idx=name_idx
            ))
            off += 8
    
    def _parse_class_data(self):
        """Parse class data items (method code)."""
        from class_data import ClassDataParser
        
        self.class_data_items = {}
        
        for class_def in self.class_defs:
            if class_def.class_data_off > 0:
                parser = ClassDataParser(self.data, self)
                data_item = parser.parse_class_data(class_def.class_data_off)
                if data_item:
                    class_name = self.types[class_def.class_idx]
                    self.class_data_items[class_name] = data_item
                    
                    # Update method_ids with code_off
                    for method in data_item.direct_methods + data_item.virtual_methods:
                        if method.method_idx < len(self.method_ids):
                            self.method_ids[method.method_idx].code_off = method.code_off
                            self.method_ids[method.method_idx].access_flags = method.access_flags
        
        # Count methods with code
        methods_with_code = sum(1 for m in self.method_ids if m.code_off > 0)
        print(f"[*] {methods_with_code} methods have code")
    
    def _parse_header(self) -> bool:
        """Parse DEX header."""
        d = self.data
        
        # Magic - accept multiple DEX versions
        magic = d[0:8]
        valid_magics = [b'dex\n035\x00', b'dex\n037\x00', b'dex\n038\x00', b'dex\n039\x00']
        if magic not in valid_magics:
            print(f"[!] Invalid DEX magic: {magic}")
            return False
        
        # Checksum (adler32)
        checksum = struct.unpack('<I', d[8:12])[0]
        
        # SHA-1 signature
        signature = d[12:32]
        
        # File size
        file_size = struct.unpack('<I', d[32:36])[0]
        
        # Header size (should be 0x70)
        header_size = struct.unpack('<I', d[36:40])[0]
        
        # Endian tag
        endian_tag = struct.unpack('<I', d[40:44])[0]
        if endian_tag != 0x12345678:
            print("[!] Unsupported endianness")
            return False
        
        # Link section
        link_size = struct.unpack('<I', d[44:48])[0]
        link_off = struct.unpack('<I', d[48:52])[0]
        
        # Map section
        map_off = struct.unpack('<I', d[52:56])[0]
        
        # String IDs
        string_ids_size = struct.unpack('<I', d[56:60])[0]
        string_ids_off = struct.unpack('<I', d[60:64])[0]
        
        # Type IDs
        type_ids_size = struct.unpack('<I', d[64:68])[0]
        type_ids_off = struct.unpack('<I', d[68:72])[0]
        
        # Proto IDs
        proto_ids_size = struct.unpack('<I', d[72:76])[0]
        proto_ids_off = struct.unpack('<I', d[76:80])[0]
        
        # Field IDs
        field_ids_size = struct.unpack('<I', d[80:84])[0]
        field_ids_off = struct.unpack('<I', d[84:88])[0]
        
        # Method IDs
        method_ids_size = struct.unpack('<I', d[88:92])[0]
        method_ids_off = struct.unpack('<I', d[92:96])[0]
        
        # Class defs
        class_defs_size = struct.unpack('<I', d[96:100])[0]
        class_defs_off = struct.unpack('<I', d[100:104])[0]
        
        # Data
        data_size = struct.unpack('<I', d[104:108])[0]
        data_off = struct.unpack('<I', d[108:112])[0]
        
        self.header = DexHeader(
            magic=magic, checksum=checksum, signature=signature,
            file_size=file_size, header_size=header_size, endian_tag=endian_tag,
            link_size=link_size, link_off=link_off, map_off=map_off,
            string_ids_size=string_ids_size, string_ids_off=string_ids_off,
            type_ids_size=type_ids_size, type_ids_off=type_ids_off,
            proto_ids_size=proto_ids_size, proto_ids_off=proto_ids_off,
            field_ids_size=field_ids_size, field_ids_off=field_ids_off,
            method_ids_size=method_ids_size, method_ids_off=method_ids_off,
            class_defs_size=class_defs_size, class_defs_off=class_defs_off,
            data_size=data_size, data_off=data_off
        )
        
        return True
    
    def _parse_strings(self):
        """Parse string table."""
        self.string_ids = []
        self.strings = []
        
        off = self.header.string_ids_off
        for i in range(self.header.string_ids_size):
            str_off = struct.unpack('<I', self.data[off:off+4])[0]
            self.string_ids.append(str_off)
            off += 4
            
            # Read string at offset
            # MUTF-8 encoded, first byte is length
            if str_off < len(self.data):
                try:
                    # Find null terminator
                    end = str_off
                    while end < len(self.data) and self.data[end] != 0:
                        end += 1
                    
                    # Decode (simplified - real MUTF-8 needs special handling)
                    s = self.data[str_off:end].decode('utf-8', errors='ignore')
                    self.strings.append(s)
                except:
                    self.strings.append("")
            else:
                self.strings.append("")
    
    def _parse_types(self):
        """Parse type table."""
        self.type_ids = []
        self.types = []
        
        off = self.header.type_ids_off
        for i in range(self.header.type_ids_size):
            type_idx = struct.unpack('<I', self.data[off:off+4])[0]
            self.type_ids.append(type_idx)
            # Lookup string
            if type_idx < len(self.strings):
                self.types.append(self.strings[type_idx])
            else:
                self.types.append(f"<unknown_{i}>")
            off += 4
    
    def _parse_methods(self):
        """Parse method table."""
        self.method_ids = []
        
        off = self.header.method_ids_off
        for i in range(self.header.method_ids_size):
            class_idx = struct.unpack('<H', self.data[off:off+2])[0]
            proto_idx = struct.unpack('<H', self.data[off+2:off+4])[0]
            name_idx = struct.unpack('<I', self.data[off+4:off+8])[0]
            
            name = self.strings[name_idx] if name_idx < len(self.strings) else f"<method_{i}>"
            class_name = self.types[class_idx] if class_idx < len(self.types) else f"<class_{class_idx}>"
            
            self.method_ids.append(Method(
                class_idx=class_idx,
                proto_idx=proto_idx,
                name_idx=name_idx
            ))
            off += 8
    
    def _parse_class_defs(self):
        """Parse class definitions."""
        self.class_defs = []
        
        off = self.header.class_defs_off
        for i in range(self.header.class_defs_size):
            class_idx = struct.unpack('<I', self.data[off:off+4])[0]
            access_flags = struct.unpack('<I', self.data[off+4:off+8])[0]
            superclass_idx = struct.unpack('<I', self.data[off+8:off+12])[0]
            interfaces_off = struct.unpack('<I', self.data[off+12:off+16])[0]
            source_file_idx = struct.unpack('<I', self.data[off+16:off+20])[0]
            annotations_off = struct.unpack('<I', self.data[off+20:off+24])[0]
            class_data_off = struct.unpack('<I', self.data[off+24:off+28])[0]
            static_values_off = struct.unpack('<I', self.data[off+28:off+32])[0]
            
            self.class_defs.append(ClassDef(
                class_idx=class_idx,
                access_flags=access_flags,
                superclass_idx=superclass_idx,
                interfaces_off=interfaces_off,
                source_file_idx=source_file_idx,
                annotations_off=annotations_off,
                class_data_off=class_data_off,
                static_values_off=static_values_off
            ))
            off += 32
    
    def get_method_code(self, method_idx: int) -> Optional[CodeItem]:
        """Get code for a method."""
        if method_idx >= len(self.method_ids):
            return None
        
        method = self.method_ids[method_idx]
        if method.code_off == 0:
            return None
        
        # Parse code item at code_off
        # Code item format is complex, this is simplified
        return None  # TODO: Implement
    
    def dump_info(self):
        """Dump DEX information."""
        print("\n=== DEX File Info ===")
        print(f"File size: {self.header.file_size} bytes")
        print(f"Strings: {len(self.strings)}")
        print(f"Types: {len(self.types)}")
        print(f"Methods: {len(self.method_ids)}")
        print(f"Classes: {len(self.class_defs)}")
        
        print("\n=== Classes ===")
        for i, cls in enumerate(self.class_defs[:10]):  # First 10
            class_name = self.types[cls.class_idx] if cls.class_idx < len(self.types) else f"<type_{cls.class_idx}>"
            super_name = self.types[cls.superclass_idx] if cls.superclass_idx < len(self.types) else "java/lang/Object"
            print(f"  {i}: {class_name} extends {super_name}")
        
        print("\n=== Methods (first 20) ===")
        for i, method in enumerate(self.method_ids[:20]):
            class_name = self.types[method.class_idx] if method.class_idx < len(self.types) else f"<type_{method.class_idx}>"
            method_name = self.strings[method.name_idx] if method.name_idx < len(self.strings) else f"<name_{method.name_idx}>"
            print(f"  {i}: {class_name}.{method_name}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        loader = DEXLoader(sys.argv[1])
        if loader.load():
            loader.dump_info()
    else:
        print("Usage: python3 dex_interpreter.py <classes.dex>")
