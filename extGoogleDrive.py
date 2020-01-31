from pydrive.drive import GoogleDrive


class extGoogleDrive(GoogleDrive):

    def SetContentBinary(self, data, filename):
        self.content = data
        if self.get('title') is None:
            self['title'] = filename
        if self.get('mimeType') is None:
            self['mimeType'] = mimetypes.guess_type(filename)[0]

    def GetContentBinary(self, mimetype=None, remove_bom=False):
        if self.content is None or \
                        type(self.content) is not io.BytesIO or \
                        self.has_bom == remove_bom:
            self.FetchContent(mimetype, remove_bom)
        return self.content.getvalue()