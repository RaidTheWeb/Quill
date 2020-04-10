import sys
sys.path.append('../src')

import data
import errors
import hashlib

def sha256(*args):
    if len(args) != 1:
        errors.error(f'sha256 needs exactly 1 argument, got {len(args)}')
    val = str(args[0].val)
    return data.String(hashlib.sha256(bytes(val, 'utf-8')).hexdigest())

def sha512(*args):
    if len(args) != 1:
        errors.error(f'sha512 needs exactly 1 argument, got {len(args)}')
    val = str(args[0].val)
    return data.String(hashlib.sha512(bytes(val, 'utf-8')).hexdigest())

def sha128(*args):
    if len(args) != 1:
        errors.error(f'sha128 needs exactly 1 argument, got {len(args)}')
    val = str(args[0].val)
    return data.String(hashlib.sha128(bytes(val, 'utf-8')).hexdigest())

def md5(*args):
    if len(args) != 1:
        errors.error(f'md5 needs exactly 1 argument, got {len(args)}')
    val = str(args[0].val)
    return data.String(hashlib.md5(bytes(val, 'utf-8')).hexdigest())

def rot13(*args):
    if len(args) != 1:
        errors.error(f'rot13 needs exactly 1 argument, got {len(args)}')
    val = str(args[0].val)
    out = ''
    for char in val:
        if char.isalpha():
            add = 65 if char.isupper() else 97
            new = ord(char) - add
            out += chr(((new + 13) % 26) + add)
        else:
            out += char
    return data.String(out)

def xor(*args):
    if len(args) != 2:
        errors.error(f'xor needs exactly 2 arguments, got {len(args)}')
    val = str(args[0].val)
    key = str(args[1].val)
    out = ''
    for i in range(len(val)):
        out += chr(ord(val[i]) ^ ord(key[i % len(key)]))
    return data.String(out)

attrs = {
    'sha256':data.Method(sha256),
    'sha512':data.Method(sha512),
    'sha128':data.Method(sha128),
    'md5':data.Method(md5),
    'rot13':data.Method(rot13),
    'xor':data.Method(xor),
}
