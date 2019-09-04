from src.crypt import encrypt, decrypt
import string


def check_data_pass(s: bytes, password: str):
    assert s == decrypt(encrypt(s, password), password)


def check_data(s: bytes):
    for pw in ["", "testpassword", string.printable]:
        check_data_pass(s, pw)


def test_crypt():
    check_data(b"")
    check_data(b"a")
    check_data(b'{"a": 3.14}')
    check_data(string.printable.encode())
    check_data(bytes(range(256)))


def test_crypt_error():
    try:
        decrypt(encrypt(b"xyz", "pass1"), "pass2")
    except:
        pass
    else:
        assert False, "Should have failed"
