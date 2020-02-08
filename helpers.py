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


# difference between two nested dict that represent file system structure
# difference(local, remote)   # return files that are local but not present on server we need to upload them
# difference(remote, local)   # return files that are present on server but not locally and we need to download them
def difference(d2, d1, level=0):  # d2 - d1
    d1_folders = {ch['title']: ch for ch in d1['children'] if ch['isfolder']}
    d1_files = [ch['title'] for ch in d1['children'] if not ch['isfolder']]

    d2_folders = {ch['title']: ch for ch in d2['children'] if ch['isfolder']}
    d2_files = [ch for ch in d2['children'] if not ch['isfolder']]

    # completely new folders
    diff_folders = [folder for folder in d2_folders.values() if folder['title'] not in d1_folders.keys()]
    # existing folder, but they are required to be checked reqursevely
    same_folders = [folder for folder in d2_folders.keys() if folder in d1_folders.keys()]

    diff_next = [difference(d2_folders[folder], d1_folders[folder], level+1) for folder in same_folders]
    diff_files = [file for file in d2_files if file['title'] not in d1_files]
    return {'title': d2['title'],
            'children': diff_folders + diff_files + diff_next}