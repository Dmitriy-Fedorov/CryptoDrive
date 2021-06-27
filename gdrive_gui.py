from main import *
from pydrive.auth import GoogleAuth
import extGoogleDrive as extGoogleDrive
import pyAesCrypt
import io
import os
import hashlib
import PySimpleGUI as sg
# import PySimpleGUIQt as sg
import os.path
from PIL import Image, ImageOps
import base64
import hashlib
import json
import sys

from helpers import mkdir, ignore, strip_aes, file_size, size_to_upload
from helpers import obfuscate, deobfuscate


def gui_password():
    # determine if a password matches the secret password by comparing SHA1 hash codes
    def PasswordMatches(password, a_hash):
        password_utf = password.encode('utf-8')
        sha1hash = hashlib.sha1()
        sha1hash.update(password_utf)
        password_hash = sha1hash.hexdigest()
        return password_hash == a_hash

    login_password_hash = "c1313ff3f3625e04a3c709563663616325e4e682"
    password = sg.popup_get_text('Decryption password:', password_char='*', title="GDrive login", size=(50, 10))
    
    if password and PasswordMatches(password, login_password_hash):
        
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth() # client_secrets.json need to be in the same directory as the script
        drive = extGoogleDrive.extGoogleDrive(gauth)
        rf = search_droot(drive, "Photo backup test")[0]
        d = DriveHandler("D:/Фото", drive, root_id=rf['id'], password=password)
        
        print('Login SUCCESSFUL')
        return d
    else:
        print('Login FAILED!!')
        sys.exit(0)

d = gui_password()

# with open("remote_folders.json", "w") as f:
#     json.dump(d.remote_folders, f, indent = 2)
# with open("remote_files.json", "w") as f:
#     json.dump(d.remote_files, f, indent = 2)

with open("remote_folders.json", "r") as f:
    d.remote_folders = json.load(f)
with open("remote_files.json", "r") as f:
    d.remote_files = json.load(f)
    
    
treedata = sg.TreeData()

folder_icon = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABnUlEQVQ4y8WSv2rUQRSFv7vZgJFFsQg2EkWb4AvEJ8hqKVilSmFn3iNvIAp21oIW9haihBRKiqwElMVsIJjNrprsOr/5dyzml3UhEQIWHhjmcpn7zblw4B9lJ8Xag9mlmQb3AJzX3tOX8Tngzg349q7t5xcfzpKGhOFHnjx+9qLTzW8wsmFTL2Gzk7Y2O/k9kCbtwUZbV+Zvo8Md3PALrjoiqsKSR9ljpAJpwOsNtlfXfRvoNU8Arr/NsVo0ry5z4dZN5hoGqEzYDChBOoKwS/vSq0XW3y5NAI/uN1cvLqzQur4MCpBGEEd1PQDfQ74HYR+LfeQOAOYAmgAmbly+dgfid5CHPIKqC74L8RDyGPIYy7+QQjFWa7ICsQ8SpB/IfcJSDVMAJUwJkYDMNOEPIBxA/gnuMyYPijXAI3lMse7FGnIKsIuqrxgRSeXOoYZUCI8pIKW/OHA7kD2YYcpAKgM5ABXk4qSsdJaDOMCsgTIYAlL5TQFTyUIZDmev0N/bnwqnylEBQS45UKnHx/lUlFvA3fo+jwR8ALb47/oNma38cuqiJ9AAAAAASUVORK5CYII='
file_icon = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABU0lEQVQ4y52TzStEURiHn/ecc6XG54JSdlMkNhYWsiILS0lsJaUsLW2Mv8CfIDtr2VtbY4GUEvmIZnKbZsY977Uwt2HcyW1+dTZvt6fn9557BGB+aaNQKBR2ifkbgWR+cX13ubO1svz++niVTA1ArDHDg91UahHFsMxbKWycYsjze4muTsP64vT43v7hSf/A0FgdjQPQWAmco68nB+T+SFSqNUQgcIbN1bn8Z3RwvL22MAvcu8TACFgrpMVZ4aUYcn77BMDkxGgemAGOHIBXxRjBWZMKoCPA2h6qEUSRR2MF6GxUUMUaIUgBCNTnAcm3H2G5YQfgvccYIXAtDH7FoKq/AaqKlbrBj2trFVXfBPAea4SOIIsBeN9kkCwxsNkAqRWy7+B7Z00G3xVc2wZeMSI4S7sVYkSk5Z/4PyBWROqvox3A28PN2cjUwinQC9QyckKALxj4kv2auK0xAAAAAElFTkSuQmCC'

for path in d.remote_folders.keys():
    if path == "remote_root":
        treedata.Insert("", "remote_root", "remote_root", values=[], icon=folder_icon)
        continue
    
    parent = "/".join(path.split('/')[:-1])
    text = path.split('/')[-1]
    treedata.Insert(parent, path, text, values=[], icon=folder_icon)
    

def decript_stream_and_save(self, fpath, drive_file_id, verbose=True):
    fDec = io.BytesIO()
    dfile = self.drive.CreateFile({'id': drive_file_id})
    fname = strip_aes(dfile['title'])
    if self.cipher: fname = deobfuscate(self.password, fname)
    if verbose:
        dfile.FetchMetadata()
        fSize = int(dfile.metadata["fileSize"])
        print(f"Downloading {file_size(fSize):8} | {fpath}/{fname}")
    
    fCiph = io.BytesIO(dfile.GetContentBinary())
    pyAesCrypt.decryptStream(fCiph, fDec, self.password, self.bufferSize, len(fCiph.getvalue()))
    return fDec
#     with open(f"{fpath}/{fname}", 'wb') as f:
#         f.write(fDec.getvalue())

def gdive_convert_to_bytes(drive_file_id, resize=None):
    bdata = decript_stream_and_save(d, "fpath", drive_file_id, verbose=True)
    img = Image.open(bdata)
    img = ImageOps.exif_transpose(img)
    
    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), Image.ANTIALIAS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()
    
# --------------------------------- Define Layout ---------------------------------

# First the window layout...2 columns

left_col = [
            [sg.Tree(data=treedata,
                   headings=['Size', ],
                   auto_size_columns=True,
                   num_rows=20,
                   col0_width=40,
                   key='-FOLDER-',
                   show_expanded=False,
                   enable_events=True),
           ],
#             [sg.Text('Folder'), sg.In(size=(25,1), enable_events=True ,key='-FOLDER-')],
            [sg.Listbox(values=[], enable_events=True, size=(40,20), key='-FILE LIST-')],
            [sg.Text('Resize to'), sg.In(key='-W-', size=(5,1)), sg.In(key='-H-', size=(5,1))]]

# For now will only show the name of the file that was chosen
images_col = [[sg.Text('You choose from the list:')],
              [sg.Text(size=(40,1), key='-TOUT-')],
              [sg.Image(key='-IMAGE-')]]

# ----- Full layout -----
layout = [[sg.Column(left_col, element_justification='c'), sg.VSeperator(),sg.Column(images_col, element_justification='c')]]

# --------------------------------- Create Window ---------------------------------
window = sg.Window('Multiple Format Image Viewer', layout, resizable=True)

# ----- Run the Event Loop -----
# --------------------------------- Event Loop ---------------------------------
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == '-FOLDER-':                         # Folder name was filled in, make a list of files in the folder
        try:
            folder = values['-FOLDER-'][0]
            print('-FOLDER-', folder)
            if folder in d.remote_folders.keys():
                file_list = [v for v in d.remote_files[folder].keys()]
            else:
                file_list = []
            fnames = [f for f in file_list]
            window['-FILE LIST-'].update(fnames)
        except Exception as E:
            print(f'** Error {E} **')
            pass        # something weird happened making the full filename
        
    elif event == '-FILE LIST-':    # A file was chosen from the listbox
        try:
            
            filename = os.path.join(values['-FOLDER-'][0], values['-FILE LIST-'][0])
            drive_file_id = d.remote_files[values['-FOLDER-'][0]][values['-FILE LIST-'][0]]
            print(f"{values['-FILE LIST-'][0]}: {drive_file_id}")
            
            window['-TOUT-'].update(f"{filename}: {drive_file_id}")
            
            if values['-W-'] and values['-H-']:
                new_size = int(values['-W-']), int(values['-H-'])
            else:
                new_size = 500, 500
            window['-IMAGE-'].update(data=gdive_convert_to_bytes(drive_file_id, resize=new_size))
#             window['-IMAGE-'].update(data=convert_to_bytes(filename, resize=new_size))
        except Exception as E:
            print(f'** Error {E} **')
            pass        # something weird happened making the full filename
# --------------------------------- Close & Exit ---------------------------------
window.close()