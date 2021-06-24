import os 
import hashlib
import numpy as np
from base64 import urlsafe_b64encode
from base64 import urlsafe_b64decode
from Crypto.Cipher import ChaCha20  # pycrypto


def mkdir(folder_name):
    try: 
        os.mkdir(folder_name)
    except FileExistsError:
        pass


def strip_aes(fname):
    return fname[::-1].replace(".aes"[::-1],"",1)[::-1]


def ignore(fname):
    if fname in ['.git', ".ipynb_checkpoints", "__pycache__"]: # , "test"
        return False
    elif fname[0] == ".":
        return False
    else:
        return True


def obfuscate(password: str, plaintext: str) -> str:
    key = hashlib.sha256(password.encode('utf-8')).digest()
    cipher = ChaCha20.new(key=key)
    ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
    
    nonce = urlsafe_b64encode(cipher.nonce).decode('utf-8')
    ct = urlsafe_b64encode(ciphertext).decode('utf-8')
    return f"{nonce}{ct}"

def deobfuscate(password: str, ciphertext: str) -> str:
    key = hashlib.sha256(password.encode('utf-8')).digest()
    nonce = urlsafe_b64decode(ciphertext[:12])
    ct = urlsafe_b64decode(ciphertext[12:])
    cipher = ChaCha20.new(key=key, nonce=nonce)
    return cipher.decrypt(ct).decode('utf-8')


def size_to_upload(f2upload, in_bytes=False):
    total = sum([file_size(f"{f[0]}/{f[1]}", in_bytes=True) for f in f2upload])
    if in_bytes:
        return total
    return file_size(total)

def file_size(fname, in_bytes=False, true_bytes=True):
    if type(fname) is str:
        byte = os.stat(fname).st_size
    else:
        byte = fname
    if in_bytes:
        return byte
    if byte == 0:
        return "0"
    if true_bytes:
        power = np.log2(byte)
        if power < 10:
            return f"{byte}"
        elif power < 20:
            return f"{byte/2**10:.2f}Kb"
        elif power < 30:
            return f"{byte/2**20:.2f}Mb"
        else:
            return f"{byte/2**30:.2f}Gb"
    else:
        power = np.log10(byte)
        if power < 3:
            return f"{byte}"
        elif power < 6:
            return f"{byte/1e3:.2f}Kb"
        elif power < 9:
            return f"{byte/1e6:.2f}Mb"
        else:
            return f"{byte/1e9:.2f}Gb"

