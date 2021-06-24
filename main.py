# from pydrive.auth import GoogleAuth
# from extGoogleDrive import extGoogleDrive as GoogleDrive
from helpers import mkdir, ignore, strip_aes, file_size, size_to_upload
from helpers import obfuscate, deobfuscate
from pprint import pprint
import hashlib
import pyAesCrypt
import io
import os


class DriveHandler:
    
    def __init__(self, local_root, drive, root_id="1YJkqN-qtRHXnL4GvT3icGyl05_dcYTE6", password = "foopassword", bufferSize=64*1024, cipher=True):
        self.root_id = root_id
        self.local_root = local_root
        self.cache = None
        self.bufferSize = bufferSize
        self.password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.drive = drive
        self.cipher = cipher
        self.local_folders = {}
        self.local_files = {}
        self.remote_folders = {}
        self.remote_files = {}
    
    def reset(self):
        self.local_folders = {}
        self.local_files = {}
        self.remote_folders = {}
        self.remote_files = {}
    

# d = DriveHandler("./mypydrive_1")
def search_droot(drive, folder):
    remote_folder_list = drive.ListFile({'q': "'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    return [{'title': f['title'], 'id': f['id']} for f in remote_folder_list if folder in f['title']]
    
    
## List local files
def get_local_folders(self, verbose=False):
    folder_list= {self.local_root: ""}
    def localListFolder(path_structure, verbose=verbose):
        local_folders = [d for d in os.listdir(path_structure) if os.path.isdir(os.path.join(path_structure, d))]
        for f in local_folders:
            if ignore(f):
                if verbose: print(f"{path_structure}/{f}")
                folder_list[f"{path_structure}/{f}"] = ""
                localListFolder(f"{path_structure}/{f}", verbose=verbose)
            
    localListFolder(self.local_root, verbose=verbose)
    self.local_folders = folder_list

def get_local_files(self):
    lfile_list = {}
    for fpath, _ in self.local_folders.items():
        lfile_list[fpath] = {d: "" for d in os.listdir(fpath) if ignore(d) and os.path.isfile(os.path.join(fpath, d))}
    self.local_files = lfile_list

## List remote
def get_remote_folders(self, decipher=True, verbose=True):
    folder_list= {"remote_root": self.root_id}
    if verbose: print(f"remote_root: '{self.root_id}'")
    
    def driveListFolder( parent, path_structure, verbose=verbose, decipher=decipher):
        remote_folders = self.drive.ListFile({'q': f"'{parent}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"}).GetList()
        for f in remote_folders:
            title = f['title']
            if decipher: title = deobfuscate(self.password, title)
            if verbose: print(f"{path_structure}/{title}: {f['id']}")
            folder_list[f"{path_structure}/{title}"] = f['id']
            driveListFolder(f['id'], f"{path_structure}/{title}", verbose, decipher)
        
    driveListFolder(self.root_id, "remote_root", decipher=decipher, verbose=verbose)
    self.remote_folders = folder_list

def get_remote_files(self, verbose=False):
    r_files = {}
    decipher = True
    for folder_name, folder_id in self.remote_folders.items():
        files = {}
        remote_files = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false and mimeType!='application/vnd.google-apps.folder'"}).GetList()
        for f in remote_files:
            title = f['title']
            if decipher: title = deobfuscate(self.password, strip_aes(title))
            files[f"{title}"] = f['id']
            if verbose: print(f'REMOTE LS: {folder_name} {title}')
        r_files[folder_name] = files
    self.remote_files = r_files

def _folders_to_create(self, verbose=False):
    to_create = []
    for folder in self.local_folders:
        rf = folder.replace(self.local_root, "remote_root")
        if rf not in self.remote_folders.keys():
            if verbose: print(f"TODO REMOTE CREATE: {rf}" )
            to_create.append(rf)
    return to_create

def create_remote_folder(self, cipher=True, verbose=True):
    to_create = _folders_to_create(self, verbose=verbose)
    for f in to_create:
        dirs = f.split("/")
        n = len(dirs)
        for i in range(n):
            remote_path = '/'.join(dirs[:i+1])
            if remote_path in self.remote_folders.keys():
                continue
            else:
                parent_id = self.remote_folders['/'.join(dirs[:i])]
                if cipher: child_name = obfuscate(self.password, dirs[i])
                child_folder = self.drive.CreateFile({'title': child_name, 
                                                  'parents':[{'id':parent_id}], 
                                                  'mimeType' : 'application/vnd.google-apps.folder'})
                child_folder.Upload()
                self.remote_folders[remote_path] = child_folder['id']
                if verbose: print(f"REMOTE CREATE FOLDER: {remote_path} | {child_name} | p:{parent_id} | c:{child_folder['id']}" )

def encript_and_upload(self, fpath, fname, parent_id):
    fIn = open(f"{fpath}/{fname}", "rb")
    fCiph = io.BytesIO()
    pyAesCrypt.encryptStream(fIn, fCiph, self.password, self.bufferSize)

    if self.cipher: fname = obfuscate(self.password, fname)
    file = self.drive.CreateFile({'title': f"{fname}.aes", 
                              'parents':[{'id': parent_id}]
                                 })
    file.SetContentBinary(fCiph)
    file.Upload() # Actual Upload

    fIn.close()
    return file['id']

def files_to_upload(self, verbose=False):
    to_upload = []
    for folder, files in self.local_files.items():
        lf = folder
        rf = folder.replace(self.local_root, "remote_root")
        items = self.remote_files.get(rf , {})
        
        for f in files:
            if f not in items.keys():
                fsize = file_size(f'{lf}/{f}', in_bytes=True)
#                 if fsize > 100*2**20:  # > 100Mb
#                     continue
                to_upload.append( (lf, f, self.remote_folders[rf]) )
                if verbose: print(f"TO UPLOAD: {lf}/{f} | Remote Folder ID: {self.remote_folders[rf]}")
                
    return to_upload


def upload_files(self, f2upload, verbose=False):
    total = size_to_upload(f2upload, in_bytes=True)
    print(f'Total to upload: {file_size(total)}')
    for fpath, fname, parent_id in f2upload:
        fsize = file_size(f'{fpath}/{fname}')
        print(f"{file_size(total):8} | ({fsize}) {fname} | {fpath}", end="")
        file_id = encript_and_upload(self, fpath, fname, parent_id)
        print(f" | {file_id}")
        
        r_path = fpath.replace(self.local_root, "remote_root") 
        rfiles = self.remote_files.get(r_path, {})
        rfiles[fname] = file_id
        self.remote_files[r_path] = rfiles
        
        total -= file_size(f'{fpath}/{fname}', in_bytes=True)