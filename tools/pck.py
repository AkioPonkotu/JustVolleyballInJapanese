"""Read encrypted Godot v4 packs and append replacements without re-exporting assets."""
import hashlib
import hmac
import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def decrypt_blob(data, offset, key):
    digest = data[offset:offset + 16]
    size = struct.unpack_from('<Q', data, offset + 16)[0]
    end = offset + 40 + ((size + 15) // 16) * 16
    if end > len(data):
        raise ValueError('Encrypted resource exceeds pack bounds')
    decryptor = Cipher(algorithms.AES(key), modes.CFB(data[offset + 24:offset + 40])).decryptor()
    plain = (decryptor.update(data[offset + 40:end]) + decryptor.finalize())[:size]
    if hashlib.md5(plain).digest() != digest:
        raise ValueError('PCK decryption/checksum failed; unsupported executable or pack')
    return plain


def encrypt_blob(data, key, domain):
    iv = hmac.new(key, b'jvja-v1/' + domain.encode() + b'/' + data, hashlib.sha256).digest()[:16]
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    padded = data + bytes((-len(data)) % 16)
    return hashlib.md5(data).digest() + struct.pack('<Q', len(data)) + iv + encryptor.update(padded) + encryptor.finalize()


@dataclass
class Entry:
    path: str
    offset: int
    size: int
    md5: bytes
    flags: int


class Pack:
    def __init__(self, data, key):
        self.data, self.key = data, key
        magic, version, major, minor, patch, flags = struct.unpack_from('<6I', data)
        if magic != 0x43504447 or version != 4 or flags != 3:
            raise ValueError('Only the verified standalone encrypted v4 pack is supported')
        self.file_base, directory = struct.unpack_from('<QQ', data, 24)
        count = struct.unpack_from('<I', data, directory)[0]
        table = decrypt_blob(data, directory + 4, key)
        self.entries = {}
        cursor = 0
        for _ in range(count):
            length = struct.unpack_from('<I', table, cursor)[0]
            cursor += 4
            path = table[cursor:cursor + length].rstrip(b'\0').decode('utf-8')
            cursor += length
            offset, size = struct.unpack_from('<QQ', table, cursor)
            digest = table[cursor + 16:cursor + 32]
            file_flags = struct.unpack_from('<I', table, cursor + 32)[0]
            cursor += 36
            if path in self.entries or file_flags & ~1:
                raise ValueError('Duplicate entry or unsupported PCK file flags')
            self.entries[path] = Entry(path, offset, size, digest, file_flags)
        if cursor != len(table):
            raise ValueError('Unexpected trailing directory data')

    def read(self, path):
        entry = self.entries[path]
        offset = self.file_base + entry.offset
        result = decrypt_blob(self.data, offset, self.key) if entry.flags & 1 else self.data[offset:offset + entry.size]
        if len(result) != entry.size or hashlib.md5(result).digest() != entry.md5:
            raise ValueError(f'Resource checksum mismatch: {path}')
        return result

    def write_patched(self, output, replacements):
        entries = dict(self.entries)
        with Path(output).open('wb') as stream:
            stream.write(self.data)
            for path, contents in sorted(replacements.items()):
                stream.write(bytes((-stream.tell()) % 16))
                offset = stream.tell() - self.file_base
                stream.write(encrypt_blob(contents, self.key, path))
                entries[path] = Entry(path, offset, len(contents), hashlib.md5(contents).digest(), 1)
            stream.write(bytes((-stream.tell()) % 16))
            directory = stream.tell()
            table = bytearray()
            for path, entry in sorted(entries.items()):
                encoded = path.encode('utf-8')
                encoded += bytes((-len(encoded)) % 4)
                table.extend(struct.pack('<I', len(encoded)) + encoded)
                table.extend(struct.pack('<QQ', entry.offset, entry.size) + entry.md5 + struct.pack('<I', entry.flags))
            stream.write(struct.pack('<I', len(entries)))
            stream.write(encrypt_blob(bytes(table), self.key, 'pack-directory'))
            stream.seek(32)
            stream.write(struct.pack('<Q', directory))
