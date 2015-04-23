class Versioner(object):
    def get(self):
        pass

    def set(self, version):
        pass

class FileVersioner(Versioner):
    def __init__(self, path='.roetsjbaan-version'):
        self.path = path
        self.version = None
        try:
            with open(self.path, 'r') as f:
                self.version = f.read().strip()
        except IOError:
            self.set('pristine')

    def get(self):
        return self.version or self.set('pristine')

    def set(self, version):
        self.version = version
        with open(self.path, 'wb') as f:
            f.write(self.version)
        return self.version
