import os 
import hashlib
from base64 import b64encode
from base64 import b64decode
from Crypto.Cipher import ChaCha20


def mkdir(folder_name):
    try: 
        os.mkdir(folder_name)
    except FileExistsError:
        pass


def strip_aes(fname):
    return fname[::-1].replace(".aes"[::-1],"",1)[::-1]

def driveList2localDict(dlist, id, parent, level=0, verbose=True, indent = "|---"):
    folder_dict={"isfolder": True, 
                 "id": id,
                 "title": parent,
                 "children": []}
    for f in dlist:
        if f["isfolder"]:
            if verbose: print(f"{indent*level}{parent}: FOLDER {f['title']}")
            folder_dict['children'].append(driveList2localDict(f['list'], f['id'], f['title'], level+1, verbose, indent))
        else:
            if verbose: print(f"{indent*level}{parent}: FILE   {f['title']}")
            folder_dict['children'].append({"isfolder": False, 
                                            "id": f["id"],
                                            "title": f['title']})
    return folder_dict


def ignore(fname):
    if fname in ['.git', ".ipynb_checkpoints", "__pycache__", "test"]:
        return False
    elif fname[0] == ".":
        return False
    else:
        return True


def obfuscate(password: str, plaintext: str) -> str:
    key = hashlib.sha256(password.encode('utf-8')).digest()
    cipher = ChaCha20.new(key=key)
    ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
    
    nonce = b64encode(cipher.nonce).decode('utf-8')
    ct = b64encode(ciphertext).decode('utf-8')
    return f"{nonce}{ct}"

def deobfuscate(password: str, ciphertext: str) -> str:
    key = hashlib.sha256(password.encode('utf-8')).digest()
    nonce = b64decode(ciphertext[:12])
    ct = b64decode(ciphertext[12:])
    cipher = ChaCha20.new(key=key, nonce=nonce)
    return cipher.decrypt(ct).decode('utf-8')