from Crypto.Cipher import AES
from base64 import urlsafe_b64encode, urlsafe_b64decode
import hashlib
import struct


def sha256(data: bytes) -> bytes:
    m = hashlib.sha256()
    m.update(data)
    return m.digest()


def encrypt(data: bytes, password: str) -> str:
    c = AES.new(sha256(password.encode()), AES.MODE_EAX)
    ciphertext, tag = c.encrypt_and_digest(data)
    return ".".join(urlsafe_b64encode(p).decode() for p in [c.nonce, ciphertext, tag])


def decrypt(data: str, password: str) -> bytes:
    nonce, ciphertext, tag = [urlsafe_b64decode(p.encode()) for p in data.split(".")]
    c = AES.new(sha256(password.encode()), AES.MODE_EAX, nonce=nonce)
    plaintext = c.decrypt(ciphertext)
    c.verify(tag)
    return plaintext
