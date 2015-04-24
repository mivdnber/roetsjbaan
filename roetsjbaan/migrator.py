import os, sys, glob, time, hashlib, inspect
from slugify import slugify
import roetsjbaan.messages as messages
from roetsjbaan.datatypes import SliceableDict

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

class MigrationError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)

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

class InitialMigration(Migration):
    def __init__(self):
        self.timestamp = 0
        self.hash = '0' * 16
        self.description = 'Original state'
        self.issue = 'None'

    def up(self, inject):
        pass

    def down(self, inject):
        return False

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
        '''
        Migrate up to the latest migration. If <to> is specified, migrate up to
        <to> and stop.
        '''
        current = self.versioner.get()
        if to:
            to = self.unique(to).hash
        else:
            # Go up to the most recent migration
            to = self.all()[-1].hash

        migrations = self.migrations[current:to, 1]
        frm = migrations[0]

        if len(migrations) < 2:
            raise MigrationError('No migrations left to do.')

        for to in migrations[1:]:
            yield messages.Migrating(frm, to, 'up')
            to.up(self.inject)
            self.versioner.set(to.hash)
            frm = to

    def down(self, to=None):
        '''
        Migrate down to <to>. if <to> is not specified, migrate down one
        migration
        '''
        current = self.versioner.get()

        if to:
            to = self.unique(to).hash
            migrations = list(reversed(self.migrations[to:current, 1]))
            # pack it into (to => from pairs).
            from_to = zip(migrations[:-1], migrations[1:])
        else:
            migrations = self.migrations[current::-1][:2]

            if len(migrations) < 2:
                raise MigrationError('No migrations left to undo.')

            from_to = [migrations]

        for frm, to in from_to:
            yield messages.Migrating(frm, to, 'down')
            frm.down(self.inject)
            self.versioner.set(to.hash)

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

        initial = InitialMigration()
        migrations.append((initial.hash, initial))
        migrations.sort(key=lambda m: int(m[1].timestamp))
        self.migrations = SliceableDict(migrations)

    def __iter__(self):
        for m in self.migrations.values():
            yield m

    def all(self):
        return self.migrations.values()
