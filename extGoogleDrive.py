from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
import mimetypes

class extGoogleDrive(GoogleDrive):

  def CreateFile(self, metadata=None):
    """Create an instance of GoogleDriveFile with auth of this instance.

    This method would not upload a file to GoogleDrive.

    :param metadata: file resource to initialize GoogleDriveFile with.
    :type metadata: dict.
    :returns: pydrive.files.GoogleDriveFile -- initialized with auth of this instance.
    """
    return extGoogleDriveFile(auth=self.auth, metadata=metadata)


class extGoogleDriveFile(GoogleDriveFile):

    def SetContentBinary(self, data):
        self.content = data
        if self.get('mimeType') is None:
            self['mimeType'] = mimetypes.guess_type(self.get('title'))[0]

    def GetContentBinary(self, mimetype=None, remove_bom=False):
        if self.content is None or \
                        type(self.content) is not io.BytesIO or \
                        self.has_bom == remove_bom:
            self.FetchContent(mimetype, remove_bom)
        return self.content.getvalue()


