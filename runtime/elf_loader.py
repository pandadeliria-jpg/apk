#!/usr/bin/env python3
"""
ELF Loader for ARM64 Android Native Libraries on M1 macOS
Loads .so files and bridges to macOS Mach-O / Darwin libc
"""
import os
import sys
import ctypes
import struct
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import IntEnum


class ELFConstants:
    """ELF format constants."""
    # Magic
    ELFMAG = b'\x7fELF'
    
    # Classes
    ELFCLASS64 = 2
    
    # Data encoding
    ELFDATA2LSB = 1  # Little endian
    
    # OS/ABI
    ELFOSABI_NONE = 0
    ELFOSABI_LINUX = 3
    
    # Types
    ET_REL = 1    # Relocatable
    ET_EXEC = 2   # Executable
    ET_DYN = 3    # Shared object
    
    # Machines
    EM_AARCH64 = 183
    
    # Section types
    SHT_NULL = 0
    SHT_PROGBITS = 1
    SHT_SYMTAB = 2
    SHT_STRTAB = 3
    SHT_RELA = 4
    SHT_HASH = 5
    SHT_DYNAMIC = 6
    SHT_NOTE = 7
    SHT_NOBITS = 8
    SHT_REL = 9
    SHT_SHLIB = 10
    SHT_DYNSYM = 11
    
    # Dynamic tag types
    DT_NULL = 0
    DT_NEEDED = 1
    DT_PLTRELSZ = 2
    DT_PLTGOT = 3
    DT_HASH = 4
    DT_STRTAB = 5
    DT_SYMTAB = 6
    DT_RELA = 7
    DT_RELASZ = 8
    DT_RELAENT = 9
    DT_STRSZ = 10
    DT_SYMENT = 11
    DT_INIT = 12
    DT_FINI = 13
    DT_SONAME = 14
    DT_RPATH = 15
    DT_SYMBOLIC = 16
    DT_REL = 17
    DT_RELSZ = 18
    DT_RELENT = 19
    DT_PLTREL = 20
    DT_DEBUG = 21
    DT_TEXTREL = 22
    DT_JMPREL = 23
    DT_BIND_NOW = 24
    DT_INIT_ARRAY = 25
    DT_FINI_ARRAY = 26
    DT_INIT_ARRAYSZ = 27
    DT_FINI_ARRAYSZ = 28
    
    # Relocation types for AArch64
    R_AARCH64_NONE = 0
    R_AARCH64_ABS64 = 257
    R_AARCH64_COPY = 1024
    R_AARCH64_GLOB_DAT = 1025
    R_AARCH64_JUMP_SLOT = 1026
    R_AARCH64_RELATIVE = 1027


@dataclass
class ELFHeader:
    """ELF header structure."""
    e_ident: bytes      # Magic and identification
    e_type: int         # Object file type
    e_machine: int      # Machine type
    e_version: int      # Object file version
    e_entry: int        # Entry point address
    e_phoff: int        # Program header offset
    e_shoff: int        # Section header offset
    e_flags: int        # Processor-specific flags
    e_ehsize: int       # ELF header size
    e_phentsize: int    # Size of program header entry
    e_phnum: int        # Number of program header entries
    e_shentsize: int    # Size of section header entry
    e_shnum: int        # Number of section header entries
    e_shstrndx: int     # Section name string table index


@dataclass
class ELFSection:
    """ELF section header."""
    sh_name: int        # Section name (string table index)
    sh_type: int        # Section type
    sh_flags: int       # Section flags
    sh_addr: int        # Virtual address
    sh_offset: int      # File offset
    sh_size: int        # Section size
    sh_link: int        # Link to another section
    sh_info: int        # Additional section information
    sh_addralign: int   # Address alignment
    sh_entsize: int     # Entry size
    name: str = ""      # Resolved name
    data: bytes = b''   # Section data


@dataclass
class ELFSymbol:
    """ELF symbol table entry."""
    st_name: int        # Symbol name (string table index)
    st_info: int        # Symbol type and binding
    st_other: int       # Symbol visibility
    st_shndx: int       # Section index
    st_value: int       # Symbol value
    st_size: int        # Symbol size
    name: str = ""      # Resolved name
    
    @property
    def is_function(self):
        return (self.st_info & 0x0f) == 2  # STT_FUNC
    
    @property
    def is_object(self):
        return (self.st_info & 0x0f) == 1  # STT_OBJECT


@dataclass
class ELFDynamic:
    """Dynamic section entry."""
    d_tag: int          # Dynamic entry type
    d_val: int          # Integer/pointer value


class BionicToDarwin:
    """
    Translates Android Bionic libc calls to macOS Darwin libc.
    This is the compatibility layer for native library functions.
    """
    
    def __init__(self):
        self.symbols: Dict[str, Callable] = {}
        self._init_symbols()
    
    def _init_symbols(self):
        """Initialize Bionic → Darwin symbol mappings."""
        # Standard C library functions (mostly compatible)
        self.symbols.update({
            # Memory
            'malloc': ctypes.CDLL(None).malloc,
            'free': ctypes.CDLL(None).free,
            'calloc': ctypes.CDLL(None).calloc,
            'realloc': ctypes.CDLL(None).realloc,
            'memcpy': ctypes.CDLL(None).memcpy,
            'memmove': ctypes.CDLL(None).memmove,
            'memset': ctypes.CDLL(None).memset,
            'memcmp': ctypes.CDLL(None).memcmp,
            'strlen': ctypes.CDLL(None).strlen,
            'strcpy': ctypes.CDLL(None).strcpy,
            'strncpy': ctypes.CDLL(None).strncpy,
            'strcmp': ctypes.CDLL(None).strcmp,
            'strncmp': ctypes.CDLL(None).strncmp,
            'strcat': ctypes.CDLL(None).strcat,
            'strchr': ctypes.CDLL(None).strchr,
            'strstr': ctypes.CDLL(None).strstr,
            'strdup': ctypes.CDLL(None).strdup,
            'strerror': ctypes.CDLL(None).strerror,
            
            # I/O
            'fopen': ctypes.CDLL(None).fopen,
            'fclose': ctypes.CDLL(None).fclose,
            'fread': ctypes.CDLL(None).fread,
            'fwrite': ctypes.CDLL(None).fwrite,
            'fseek': ctypes.CDLL(None).fseek,
            'ftell': ctypes.CDLL(None).ftell,
            'fflush': ctypes.CDLL(None).fflush,
            'printf': ctypes.CDLL(None).printf,
            'sprintf': ctypes.CDLL(None).sprintf,
            'snprintf': ctypes.CDLL(None).snprintf,
            'fprintf': ctypes.CDLL(None).fprintf,
            'puts': ctypes.CDLL(None).puts,
            'putchar': ctypes.CDLL(None).putchar,
            'getchar': ctypes.CDLL(None).getchar,
            
            # Math
            'sin': ctypes.CDLL(None).sin,
            'cos': ctypes.CDLL(None).cos,
            'tan': ctypes.CDLL(None).tan,
            'sqrt': ctypes.CDLL(None).sqrt,
            'pow': ctypes.CDLL(None).pow,
            'log': ctypes.CDLL(None).log,
            'exp': ctypes.CDLL(None).exp,
            'floor': ctypes.CDLL(None).floor,
            'ceil': ctypes.CDLL(None).ceil,
            'fabs': ctypes.CDLL(None).fabs,
            'atan2': ctypes.CDLL(None).atan2,
            'fmod': ctypes.CDLL(None).fmod,
            
            # Time
            'time': ctypes.CDLL(None).time,
            'gettimeofday': ctypes.CDLL(None).gettimeofday,
            'clock_gettime': ctypes.CDLL(None).clock_gettime,
            'nanosleep': ctypes.CDLL(None).nanosleep,
            'usleep': ctypes.CDLL(None).usleep,
            
            # Threading
            'pthread_create': ctypes.CDLL(None).pthread_create,
            'pthread_join': ctypes.CDLL(None).pthread_join,
            'pthread_mutex_init': ctypes.CDLL(None).pthread_mutex_init,
            'pthread_mutex_lock': ctypes.CDLL(None).pthread_mutex_lock,
            'pthread_mutex_unlock': ctypes.CDLL(None).pthread_mutex_unlock,
            'pthread_cond_init': ctypes.CDLL(None).pthread_cond_init,
            'pthread_cond_wait': ctypes.CDLL(None).pthread_cond_wait,
            'pthread_cond_signal': ctypes.CDLL(None).pthread_cond_signal,
        })
        
        # Android-specific functions that need emulation
        self.symbols.update({
            '__android_log_print': self._android_log_print,
            '__android_log_write': self._android_log_write,
            'AAssetManager_fromJava': self._asset_manager_from_java,
            'AAssetManager_open': self._asset_manager_open,
            'AAsset_read': self._asset_read,
            'AAsset_close': self._asset_close,
            'ANativeWindow_fromSurface': self._native_window_from_surface,
            'ANativeWindow_acquire': self._native_window_acquire,
            'ANativeWindow_release': self._native_window_release,
            'ANativeWindow_getWidth': self._native_window_get_width,
            'ANativeWindow_getHeight': self._native_window_get_height,
        })
    
    # Android-specific function implementations
    def _android_log_print(self, prio, tag, fmt, *args):
        """Redirect Android logs to NSLog."""
        tag_str = ctypes.cast(tag, ctypes.c_char_p).value or b'unknown'
        fmt_str = ctypes.cast(fmt, ctypes.c_char_p).value or b'%s'
        print(f"[Android/{tag_str.decode()}] {fmt_str.decode() % args}")
    
    def _android_log_write(self, prio, tag, msg):
        """Write Android log message."""
        tag_str = ctypes.cast(tag, ctypes.c_char_p).value or b'unknown'
        msg_str = ctypes.cast(msg, ctypes.c_char_p).value or b''
        print(f"[Android/{tag_str.decode()}] {msg_str.decode()}")
    
    def _asset_manager_from_java(self, env, asset_manager):
        """Create native asset manager from Java."""
        # Return a dummy handle
        return 1
    
    def _asset_manager_open(self, mgr, filename, mode):
        """Open an asset file."""
        name = ctypes.cast(filename, ctypes.c_char_p).value
        if name:
            # Try to open from APK assets
            path = os.path.join('assets', name.decode())
            if os.path.exists(path):
                return id(open(path, 'rb'))
        return 0
    
    def _asset_read(self, asset, buf, count):
        """Read from asset."""
        # Simplified - in reality need proper file handle tracking
        return count
    
    def _asset_close(self, asset):
        """Close asset file."""
        pass
    
    def _native_window_from_surface(self, env, surface):
        """Get native window from Surface."""
        # Return a dummy window handle
        return 1
    
    def _native_window_acquire(self, window):
        """Acquire native window reference."""
        pass
    
    def _native_window_release(self, window):
        """Release native window reference."""
        pass
    
    def _native_window_get_width(self, window):
        """Get native window width."""
        return 800  # Default
    
    def _native_window_get_height(self, window):
        """Get native window height."""
        return 600  # Default
    
    def resolve(self, name: str) -> Optional[int]:
        """Resolve a symbol name to address."""
        if name in self.symbols:
            sym = self.symbols[name]
            if callable(sym):
                return id(sym)  # Return Python object ID as fake address
            return sym
        return None


class ELFLoader:
    """
    ELF file loader for ARM64 Android shared libraries.
    Parses ELF structure and prepares for loading on M1 macOS.
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.data: bytes = b''
        self.header: Optional[ELFHeader] = None
        self.sections: List[ELFSection] = []
        self.symbols: Dict[str, ELFSymbol] = {}
        self.dynamic: List[ELFDynamic] = []
        self.strtab: bytes = b''
        self.symtab: List[ELFSymbol] = []
        self.loaded_base: int = 0
        self.bionic = BionicToDarwin()
        
        # Memory segments
        self.segments: List[Dict] = []
    
    def load(self) -> bool:
        """Load and parse ELF file."""
        print(f"[*] Loading ELF: {self.filename}")
        
        try:
            with open(self.filepath, 'rb') as f:
                self.data = f.read()
        except Exception as e:
            print(f"[!] Failed to read file: {e}")
            return False
        
        # Parse header
        if not self._parse_header():
            return False
        
        # Parse sections
        self._parse_sections()
        
        # Parse symbols
        self._parse_symbols()
        
        # Parse dynamic section
        self._parse_dynamic()
        
        print(f"[+] ELF loaded: {self.header.e_type} machine={self.header.e_machine}")
        print(f"    Sections: {len(self.sections)}")
        print(f"    Symbols: {len(self.symbols)}")
        return True
    
    def _parse_header(self) -> bool:
        """Parse ELF header."""
        data = self.data
        
        # Check magic
        if data[:4] != ELFConstants.ELFMAG:
            print("[!] Not a valid ELF file")
            return False
        
        # Check 64-bit
        if data[4] != ELFConstants.ELFCLASS64:
            print("[!] Not 64-bit ELF")
            return False
        
        # Check little endian
        if data[5] != ELFConstants.ELFDATA2LSB:
            print("[!] Not little endian")
            return False
        
        # Parse header fields
        self.header = ELFHeader(
            e_ident=data[:16],
            e_type=struct.unpack('<H', data[16:18])[0],
            e_machine=struct.unpack('<H', data[18:20])[0],
            e_version=struct.unpack('<I', data[20:24])[0],
            e_entry=struct.unpack('<Q', data[24:32])[0],
            e_phoff=struct.unpack('<Q', data[32:40])[0],
            e_shoff=struct.unpack('<Q', data[40:48])[0],
            e_flags=struct.unpack('<I', data[48:52])[0],
            e_ehsize=struct.unpack('<H', data[52:54])[0],
            e_phentsize=struct.unpack('<H', data[54:56])[0],
            e_phnum=struct.unpack('<H', data[56:58])[0],
            e_shentsize=struct.unpack('<H', data[58:60])[0],
            e_shnum=struct.unpack('<H', data[60:62])[0],
            e_shstrndx=struct.unpack('<H', data[62:64])[0],
        )
        
        # Check ARM64
        if self.header.e_machine != ELFConstants.EM_AARCH64:
            print(f"[!] Not ARM64: machine={self.header.e_machine}")
            return False
        
        return True
    
    def _parse_sections(self):
        """Parse section headers."""
        if self.header.e_shoff == 0:
            return
        
        # Get section name string table
        shstrtab_offset = self.header.e_shoff + self.header.e_shstrndx * self.header.e_shentsize
        shstrtab_hdr = self._read_section_header(shstrtab_offset)
        shstrtab_data = self.data[shstrtab_hdr.sh_offset:shstrtab_hdr.sh_offset + shstrtab_hdr.sh_size]
        
        # Parse each section
        for i in range(self.header.e_shnum):
            offset = self.header.e_shoff + i * self.header.e_shentsize
            sec = self._read_section_header(offset)
            
            # Resolve name
            if sec.sh_name < len(shstrtab_data):
                name_end = shstrtab_data.find(b'\x00', sec.sh_name)
                if name_end < 0:
                    name_end = len(shstrtab_data)
                sec.name = shstrtab_data[sec.sh_name:name_end].decode('utf-8', errors='ignore')
            
            # Load section data
            if sec.sh_type != ELFConstants.SHT_NOBITS and sec.sh_size > 0:
                sec.data = self.data[sec.sh_offset:sec.sh_offset + sec.sh_size]
            
            self.sections.append(sec)
    
    def _read_section_header(self, offset: int) -> ELFSection:
        """Read section header at given offset."""
        data = self.data
        return ELFSection(
            sh_name=struct.unpack('<I', data[offset:offset+4])[0],
            sh_type=struct.unpack('<I', data[offset+4:offset+8])[0],
            sh_flags=struct.unpack('<Q', data[offset+8:offset+16])[0],
            sh_addr=struct.unpack('<Q', data[offset+16:offset+24])[0],
            sh_offset=struct.unpack('<Q', data[offset+24:offset+32])[0],
            sh_size=struct.unpack('<Q', data[offset+32:offset+40])[0],
            sh_link=struct.unpack('<I', data[offset+40:offset+44])[0],
            sh_info=struct.unpack('<I', data[offset+44:offset+48])[0],
            sh_addralign=struct.unpack('<Q', data[offset+48:offset+56])[0],
            sh_entsize=struct.unpack('<Q', data[offset+56:offset+64])[0],
        )
    
    def _parse_symbols(self):
        """Parse symbol table."""
        # Find .dynsym and .symtab sections
        for sec in self.sections:
            if sec.sh_type == ELFConstants.SHT_DYNSYM or sec.sh_type == ELFConstants.SHT_SYMTAB:
                self._parse_symtab(sec)
    
    def _parse_symtab(self, sec: ELFSection):
        """Parse symbol table section."""
        # Get string table
        strtab_sec = self.sections[sec.sh_link] if sec.sh_link < len(self.sections) else None
        strtab = strtab_sec.data if strtab_sec else b''
        
        # Parse each symbol (each entry is 24 bytes for 64-bit)
        entry_size = 24
        for i in range(0, len(sec.data), entry_size):
            if i + entry_size > len(sec.data):
                break
            
            data = sec.data[i:i+entry_size]
            sym = ELFSymbol(
                st_name=struct.unpack('<I', data[0:4])[0],
                st_info=data[4],
                st_other=data[5],
                st_shndx=struct.unpack('<H', data[6:8])[0],
                st_value=struct.unpack('<Q', data[8:16])[0],
                st_size=struct.unpack('<Q', data[16:24])[0],
            )
            
            # Resolve name
            if sym.st_name < len(strtab):
                name_end = strtab.find(b'\x00', sym.st_name)
                if name_end < 0:
                    name_end = len(strtab)
                sym.name = strtab[sym.st_name:name_end].decode('utf-8', errors='ignore')
            
            self.symtab.append(sym)
            if sym.name:
                self.symbols[sym.name] = sym
    
    def _parse_dynamic(self):
        """Parse dynamic section."""
        for sec in self.sections:
            if sec.sh_type == ELFConstants.SHT_DYNAMIC:
                entry_size = 16  # Each entry is 16 bytes for 64-bit
                for i in range(0, len(sec.data), entry_size):
                    if i + entry_size > len(sec.data):
                        break
                    
                    data = sec.data[i:i+entry_size]
                    dyn = ELFDynamic(
                        d_tag=struct.unpack('<Q', data[0:8])[0],
                        d_val=struct.unpack('<Q', data[8:16])[0],
                    )
                    self.dynamic.append(dyn)
    
    def find_symbol(self, name: str) -> Optional[ELFSymbol]:
        """Find symbol by name."""
        return self.symbols.get(name)
    
    def list_exports(self) -> List[str]:
        """List exported symbols (functions)."""
        exports = []
        for name, sym in self.symbols.items():
            if sym.is_function and sym.st_shndx != 0:  # Defined, not undefined
                exports.append(name)
        return exports
    
    def get_dependencies(self) -> List[str]:
        """Get list of required shared libraries."""
        deps = []
        # Find .dynstr section
        dynstr = None
        for sec in self.sections:
            if sec.sh_type == ELFConstants.SHT_STRTAB and sec.name == '.dynstr':
                dynstr = sec.data
                break
        
        if not dynstr:
            return deps
        
        # Parse DT_NEEDED entries
        for dyn in self.dynamic:
            if dyn.d_tag == ELFConstants.DT_NEEDED:
                if dyn.d_val < len(dynstr):
                    name_end = dynstr.find(b'\x00', dyn.d_val)
                    if name_end < 0:
                        name_end = len(dynstr)
                    lib = dynstr[dyn.d_val:name_end].decode('utf-8', errors='ignore')
                    deps.append(lib)
        
        return deps
    
    def call_symbol(self, name: str, *args) -> Any:
        """Call an exported function by name."""
        sym = self.find_symbol(name)
        if not sym:
            print(f"[!] Symbol not found: {name}")
            return None
        
        # Check if this is a Bionic function we can redirect
        darwin_addr = self.bionic.resolve(name)
        if darwin_addr:
            print(f"[*] Redirecting {name} to Darwin implementation")
            # Create ctypes function pointer
            func = ctypes.CFUNCTYPE(ctypes.c_int)(darwin_addr)
            return func(*args)
        
        print(f"[!] Cannot call {name}: no implementation available")
        return None
    
    def dump_info(self):
        """Dump ELF information."""
        print(f"\nELF File: {self.filename}")
        print(f"  Type: {self.header.e_type}")
        print(f"  Machine: ARM64 ({self.header.e_machine})")
        print(f"  Entry: 0x{self.header.e_entry:x}")
        print(f"  Sections: {len(self.sections)}")
        
        # Important sections
        for sec in self.sections:
            if sec.name in ['.text', '.data', '.rodata', '.dynsym', '.dynamic']:
                print(f"  Section {sec.name}: 0x{sec.sh_addr:x} ({sec.sh_size} bytes)")
        
        # Exported functions (first 20)
        exports = self.list_exports()
        print(f"  Exported functions: {len(exports)}")
        for name in exports[:20]:
            print(f"    {name}")
        if len(exports) > 20:
            print(f"    ... and {len(exports) - 20} more")
        
        # Dependencies
        deps = self.get_dependencies()
        if deps:
            print(f"  Dependencies:")
            for dep in deps:
                print(f"    {dep}")


class NativeLibraryManager:
    """
    Manages loading of Android native libraries on macOS.
    """
    
    def __init__(self):
        self.loaded_libs: Dict[str, ELFLoader] = {}
        self.native_path = None
        self.bionic = BionicToDarwin()
    
    def set_native_path(self, path: str):
        """Set path to extracted native libraries."""
        self.native_path = path
    
    def load_library(self, lib_name: str) -> Optional[ELFLoader]:
        """Load a native library by name."""
        if lib_name in self.loaded_libs:
            return self.loaded_libs[lib_name]
        
        # Find library file
        lib_path = None
        if self.native_path:
            for root, dirs, files in os.walk(self.native_path):
                for f in files:
                    if f == lib_name or f == lib_name.replace('.so', '.dylib'):
                        lib_path = os.path.join(root, f)
                        break
        
        if not lib_path:
            print(f"[!] Library not found: {lib_name}")
            return None
        
        # Load ELF
        loader = ELFLoader(lib_path)
        if loader.load():
            self.loaded_libs[lib_name] = loader
            print(f"[+] Loaded native library: {lib_name}")
            return loader
        
        return None
    
    def resolve_symbol(self, name: str) -> Optional[int]:
        """Resolve a symbol across all loaded libraries."""
        # Check Bionic functions first
        addr = self.bionic.resolve(name)
        if addr:
            return addr
        
        # Search loaded libraries
        for loader in self.loaded_libs.values():
            sym = loader.find_symbol(name)
            if sym and sym.st_shndx != 0:
                # Return fake address based on symbol value
                return sym.st_value
        
        return None
    
    def call_function(self, lib_name: str, func_name: str, *args) -> Any:
        """Call a function in a specific library."""
        loader = self.loaded_libs.get(lib_name)
        if not loader:
            print(f"[!] Library not loaded: {lib_name}")
            return None
        
        return loader.call_symbol(func_name, *args)


# Export
__all__ = ['ELFLoader', 'NativeLibraryManager', 'BionicToDarwin', 'ELFConstants']
