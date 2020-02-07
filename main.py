# from pydrive.auth import GoogleAuth
# from extGoogleDrive import extGoogleDrive as GoogleDrive
from helpers import mkdir, driveList2localDict, ignore, strip_aes
from helpers import obfuscate, deobfuscate
from pprint import pprint
import hashlib
import pyAesCrypt
import io
import os


class DriveHandler:
    
    def __init__(self, drive, password = "foopassword", bufferSize=64*1024, cipher=True):
        self.root_id = "1YJkqN-qtRHXnL4GvT3icGyl05_dcYTE6"
        self.cache = None
        self.bufferSize = bufferSize
        self.password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.drive = drive
        self.cipher = cipher
    
    def create_dfolder(self, child_name=None, parent_id=None):
        if parent_id is None:
            parent_id = self.root_id
        if child_name is None:
            child_name = "New Folder"
        if self.cipher: child_name = obfuscate(self.password, child_name)
        child_folder = self.drive.CreateFile({'title': child_name, 
                                              'parents':[{'id':parent_id}], 
                                              'mimeType' : 'application/vnd.google-apps.folder'})
        child_folder.Upload()
        return child_folder['id']

    def driveListFolder(self, parent, level=0, verbose=True, indent = "|---", decipher=False):
        filelist=[]
        file_list = self.drive.ListFile({'q': f"'{parent}' in parents and trashed=false"}).GetList()
        for f in file_list:
            title = f['title']

            if f['mimeType']=='application/vnd.google-apps.folder': # if folder
                if decipher: title = deobfuscate(self.password, title)
                if verbose: print(f"{indent*level}{parent}: FOLDER {title}")
                filelist.append({"id": f['id'],
                                "isfolder": True,
                                "title": title,
                                "list": self.driveListFolder(f['id'], level+1, verbose, indent, decipher)
                                })
            else:
                if decipher: title = deobfuscate(self.password, strip_aes(title))
                if verbose: print(f"{indent*level}{parent}: FILE   {title}")
                filelist.append({"id": f["id"],
                                "title": title, 
                                "isfolder": False,
                                })
        if level != 0:
            return filelist
        else:
            return driveList2localDict(filelist, self.root_id, "root", verbose=False)
    
    def localListFolder(self, parent, level=0, verbose=False,
                        ignore=ignore):
        cwd = os.getcwd()  # restore cwd after recursion is finished
        os.chdir(parent) 
        indent = '    '
        folder_dict={"isfolder": True, 
                    "title": parent,
                    "children": []}
        file_list = [entry for entry in os.listdir(".") if ignore(entry)]
        for f in file_list:
            if os.path.isdir(f): # if folder
                if verbose: print(f"{indent*level}{parent}: folder {f}")
                folder_dict['children'].append(self.localListFolder(f, level=level+1, verbose=verbose))
            else:
                if verbose: print(f"{indent*level}{parent}: file   {f}")
                folder_dict['children'].append({"isfolder": False, 
                                                "title": f})

        os.chdir(cwd)
        return folder_dict
    
    def encript_and_upload(self, fname, parent_id):
        if parent_id is None:
            parent_id = self.root_id
        fIn = open(fname, "rb")
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

    def decript_stream_and_save(self, drive_file_id):
        fDec = io.BytesIO()
        dfile = self.drive.CreateFile({'id': drive_file_id})
        fname = strip_aes(dfile['title'])
        if self.cipher: fname = deobfuscate(self.password, fname)

        fCiph = io.BytesIO(dfile.GetContentBinary())
        pyAesCrypt.decryptStream(fCiph, fDec, self.password, self.bufferSize, len(fCiph.getvalue()))
        with open(fname, 'wb') as f:
            f.write(fDec.getvalue())
    
    def upload_folder_tree(self, tree, drive_id=None, level=0, verbose=True, indent = "|---"):
        cwd = os.getcwd()  # restore cwd after recursion is finished
        parent_folder = tree['title']
        os.chdir(parent_folder) 
            
        for f in tree['children']:
            if f['isfolder']:
                f['id'] = self.create_dfolder(f['title'], drive_id)
                if verbose: print(f"{indent*level}> {parent_folder}: FOLDER {f['title']} \t\t {f['id']}")
                self.upload_folder_tree(f, f['id'], level+1, verbose, indent)
            else:
                f['id'] = self.encript_and_upload(f['title'], drive_id)
                if verbose: print(f"{indent*level}> {parent_folder}: FILE {f['title']} \t\t {f['id']}")
        
        os.chdir(cwd)
        return tree
    
    def download_folder_tree(self, fsave, tree, ignore=ignore, level=0, verbose=True, indent = "|---"):
        cwd = os.getcwd()  # restore cwd after recursion is finished
        parent_folder = tree['title']
        os.chdir(fsave) 
        
        for f in tree['children']:
            if f['isfolder']:
                title = f['title']
                # if self.cipher: title = deobfuscate(self.password, title)
                mkdir(title)
                if verbose: print(f"{indent*level}> {parent_folder}: FOLDER {title} \t\t {f['id']}")
                self.download_folder_tree(f['title'], f, verbose=verbose, indent=indent, level=level+1)
            else:
                title = f['title']
                # if self.cipher: title = deobfuscate(self.password, strip_aes(title))
                self.decript_stream_and_save(f['id'])
                if verbose: print(f"{indent*level}> {parent_folder}: FILE {title} \t\t {f['id']}")
        
        os.chdir(cwd)

    def download_all(self, fsave, verbose=True):
        cwd = os.getcwd()  # restore cwd after recursion is finished
        try:
            remote = self.driveListFolder(self.root_id, decipher=True, verbose=verbose)
            self.download_folder_tree(fsave, remote)
            return remote
        except KeyboardInterrupt:
            os.chdir(cwd) 
    
