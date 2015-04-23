import os, sys, glob, time, hashlib, collections, inspect
from slugify import slugify

migration_template = '''description = '%s'
hash = '%s'
issue = '%s'

def up():
    pass

def down():
    pass
'''

def module_name(path):
    _, filename = os.path.split(path)
    name, _ = os.path.splitext(filename)
    return name

class SliceableDict(collections.OrderedDict):
    def __getitem__(self, key):
        stop_offset = 0

        if isinstance(key, tuple):
            key, stop_offset = key

        if isinstance(key, slice):
            return self.values()[self.__calculate_slice(key, stop_offset)]

        return super(SliceableDict, self).__getitem__(key)

    def __calculate_slice(self, key, stop_offset=0):
        start, stop, step = key.start, key.stop, key.step

        if start:
            start = next(
                i for i, (k, v) in enumerate(self.items())
                if k == start
            )

        if stop:
            stop = next(
                i for i, (k, v) in enumerate(self.items())
                if k == stop
            ) + stop_offset


        return slice(start, stop, step)

class Migration(object):
    def __init__(self, module_name):
        self.module = __import__(module_name)
        self.timestamp = int(module_name.split('_')[0])
        self.hash = self.module.hash
        self.description = self.module.description
        self.issue = self.module.issue

    def up(self, inject):
        args = inspect.getargspec(self.module.up).args
        return self.module.up(*[inject[arg] for arg in args])

    def down(self, inject):
        args = inspect.getargspec(self.module.down).args
        return self.module.down(*[inject[arg] for arg in args])

class Migrator(object):
    def __init__(self, versioner, directory='migrations', inject={}):
        self.versioner = versioner
        self.directory = directory
        self.migrations = SliceableDict()
        self.inject = inject

        if directory not in sys.path:
            sys.path.append(directory)

        self.reload()

    def up(self, to=None):
        current = self.versioner.get()
        if to:
            to = self.unique(to).hash
        else:
            to = self.migrations.values()[-1].hash

        migrations = self.migrations[current:to, 1]
        old = migrations[0]
        for m in migrations[1:]:
            m.up(self.inject)
            self.versioner.set(m.hash)
            yield old, m
            old = m

    def down(self, to=None):
        current = self.versioner.get()

        if to:
            to = self.unique(to).hash
            migrations = list(reversed(self.migrations[to:current, 1]))

            for undo, new_current in zip(migrations[:-1], migrations[1:]):
                undo.down(self.inject)
                self.versioner.set(new_current.hash)
                yield undo, new_current

        else:
            undo, new_current = self.migrations[current::-1][:2]
            undo.down(self.inject)
            self.versioner.set(new_current.hash)
            yield undo, new_current

    def create(self, description, issue=None):
        timestamp = int(time.time())
        slug = slugify(unicode(description)).replace('-', '_')
        hash = hashlib.sha1('%d%s%s' % (timestamp, description, str(issue))).hexdigest()
        name = '%d_%s_%s.py' % (timestamp, hash[:8], slug)

        with open(os.path.join(self.directory, name), 'wb') as f:
            f.write(migration_template % (description, hash, str(issue)))


        return name

    def find(self, hash):
        return [
            m for m in self.migrations.values()
            if m.hash.startswith(hash)
        ]

    def unique(self, hash):
        hits = self.find(hash)

        if len(hits) > 1:
            raise IndexError('Multiple hashes found with prefix ' + hash)

        if not hits:
            raise IndexError('No hash found with prefix ' + hash)

        return hits[0]

    def reload(self):
        migrations = []
        for f in glob.glob(os.path.join(self.directory, '*.py')):
            m = Migration(module_name(f))
            migrations.append((m.hash, m))

        migrations.sort(key = lambda m: m[1].timestamp)
        self.migrations = SliceableDict(migrations)

    def __iter__(self):
        for m in self.migrations.values():
            yield m
