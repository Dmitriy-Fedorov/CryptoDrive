from pydrive.auth import GoogleAuth
import extGoogleDrive
import main

gauth = GoogleAuth()
gauth.LocalWebserverAuth() # client_secrets.json need to be in the same directory as the script
drive =extGoogleDrive.extGoogleDrive(gauth)

d = main.DriveHandler(drive)
d.download_all('test')
