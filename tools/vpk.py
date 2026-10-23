"""Read-only VPK v1/v2 inventory and entry CRC checks; Python standard library.

Format reference: ValveResourceFormat/ValvePak, Package.Read.cs.
This module does not extract, repack, or authenticate signatures.
"""

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib


MAGIC = 0x55AA1234
EMBEDDED = 0x7FFF
MAX_TREE_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 200_000


class VPKError(ValueError):
    """Malformed, missing, or unsupported package data."""


@dataclass(frozen=True)
class Entry:
    path: str
    crc32: int
    archive_index: int
    offset: int
    length: int
    preload: bytes

    @property
    def size(self):
        return len(self.preload) + self.length


class Package:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = {}
        with self.path.open("rb") as stream:
            file_size = self.path.stat().st_size
            header = stream.read(12)
            if len(header) != 12:
                raise VPKError("VPK header is truncated")
            magic, self.version, tree_size = struct.unpack("<III", header)
            if magic != MAGIC:
                raise VPKError("File is not a VPK (incorrect magic)")
            if self.version not in (1, 2):
                raise VPKError(f"Unsupported VPK version: {self.version}")
            self.header_size = 12
            self.signature_size = 0
            if self.version == 2:
                extra = stream.read(16)
                if len(extra) != 16:
                    raise VPKError("VPK v2 header is truncated")
                data_size, archive_hash_size, other_hash_size, self.signature_size = struct.unpack("<IIII", extra)
                self.header_size = 28
                if self.header_size + tree_size + data_size + archive_hash_size + other_hash_size + self.signature_size > file_size:
                    raise VPKError("VPK v2 sections extend beyond the file")
            else:
                data_size = file_size - self.header_size - tree_size
            if not 0 < tree_size <= MAX_TREE_BYTES or self.header_size + tree_size > file_size:
                raise VPKError("Invalid or excessive VPK directory size")
            self.data_offset = self.header_size + tree_size
            self.embedded_size = data_size
            tree = stream.read(tree_size)
        self._parse_tree(tree)

    def _parse_tree(self, tree):
        cursor = 0

        def word():
            nonlocal cursor
            end = tree.find(b"\0", cursor)
            if end < 0 or end-cursor > 8192:
                raise VPKError("Unterminated or excessive VPK directory string")
            try:
                value = tree[cursor:end].decode("utf-8")
            except UnicodeDecodeError as error:
                raise VPKError("VPK directory string is not UTF-8") from error
            cursor = end+1
            return value

        while extension := word():
            while directory := word():
                while name := word():
                    if cursor+18 > len(tree):
                        raise VPKError("VPK entry metadata is truncated")
                    crc, preload_size, archive, offset, length, terminator = struct.unpack_from("<IHHIIH", tree, cursor)
                    cursor += 18
                    if terminator != 0xFFFF:
                        raise VPKError("VPK entry has an invalid terminator")
                    if cursor+preload_size > len(tree):
                        raise VPKError("VPK preload data is truncated")
                    preload = tree[cursor:cursor+preload_size]
                    cursor += preload_size
                    filename = ("" if name == " " else name) + ("" if extension == " " else "."+extension)
                    path = filename if directory == " " else directory+"/"+filename
                    if not path or "\\" in path or ":" in path or any(part in ("", ".", "..") for part in path.split("/")):
                        raise VPKError(f"Invalid package path: {path!r}")
                    key = path.casefold()
                    if key in self.entries:
                        raise VPKError(f"Duplicate or case-colliding package path: {path}")
                    if len(self.entries) >= MAX_ENTRIES:
                        raise VPKError("VPK directory exceeds entry limit")
                    self.entries[key] = Entry(path, crc, archive, offset, length, preload)
        if any(tree[cursor:]):
            raise VPKError("Unexpected data after VPK directory terminator")

    def _location(self, entry):
        if entry.archive_index == EMBEDDED:
            path, base, available = self.path, self.data_offset, self.embedded_size
        else:
            if entry.archive_index > EMBEDDED:
                raise VPKError(f"Unsupported archive index for {entry.path}")
            stem = self.path.stem
            if stem.endswith("_dir"):
                stem = stem[:-4]
            path = self.path.with_name(f"{stem}_{entry.archive_index:03d}.vpk")
            base, available = 0, path.stat().st_size
        if entry.offset+entry.length > available:
            raise VPKError(f"Entry data extends beyond its archive: {entry.path}")
        return path, base+entry.offset

    def chunks(self, entry):
        if entry.preload:
            yield entry.preload
        if entry.length:
            path, offset = self._location(entry)
            with path.open("rb") as stream:
                stream.seek(offset)
                remaining = entry.length
                while remaining:
                    data = stream.read(min(1024*1024, remaining))
                    if not data:
                        raise VPKError(f"Truncated entry data: {entry.path}")
                    remaining -= len(data)
                    yield data

    def verify(self, entry):
        crc = 0
        for data in self.chunks(entry):
            crc = zlib.crc32(data, crc)
        if crc != entry.crc32:
            raise VPKError(f"CRC mismatch for {entry.path}")
        return True

    def read(self, entry, *, max_bytes=1024*1024):
        if entry.size > max_bytes:
            raise VPKError(f"Entry exceeds read limit: {entry.path}")
        data = b"".join(self.chunks(entry))
        if zlib.crc32(data) != entry.crc32:
            raise VPKError(f"CRC mismatch for {entry.path}")
        return data
