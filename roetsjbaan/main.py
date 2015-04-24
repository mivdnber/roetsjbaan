import argparse, sys, time, os
from tabulate import tabulate
import imp

import roetsjbaan
import roetsjbaan.messages as messages

sys.path.append(os.getcwd())
f, path, desc = imp.find_module('roetsjfile', [os.getcwd()])
roetsjfile = imp.load_module('roetsjfile', f, path, desc)

migrator = roetsjbaan.Migrator(roetsjfile.versioner,
    inject=roetsjfile.inject if hasattr(roetsjfile, 'inject') else {},
    directory=roetsjfile.directory if hasattr(roetsjfile, 'directory') else 'migrations'
)

migrator.reload()

def list(args):
    '''
    Shows a list of all migrations.
    '''
    print 'Migrations in %s:' % migrator.directory
    print pretty_migrations(migrator, long=args.long)
    if not migrator.versioner.get():
        print "Warning! I don't know the current version. Please set it with roetsj set."

def new(args):
    '''
    Create a migration with a given description and an optional issue number
    '''
    fn = migrator.create(args.description, args.issue)
    print 'Migration created as %s' % fn

def set(args):
    '''
    Set the current version. You shouldn't need this unless you screw up a
    migration
    '''
    hits = migrator.find(args.hash)
    if len(hits) > 1:
        print 'More than one migration corresponds to hash %s:' % args.hash
    else:
        migrator.versioner.set(hits[0].hash)
        print 'Current version set to:'
    print pretty_migrations(hits)

def up(args):
    '''
    Execute all pending migrations. You can specify op to which migration you
    wish to migrate with the -t <hash> or --to <hash> options.
    '''
    if not migrator.versioner.get():
        print 'Sorry, the current version is not set. Please set it with roetsj set.'
        return
    try:
        for message in migrator.up(args.to):
            print 'up', pretty_migrations([message.new], headers=[], format='plain')
    except roetsjbaan.MigrationError as e:
        print e.message

def down(args):
    '''
    Undo the current migration. You can undo multiple migrations at once by
    specifying the -t <hash> or --to <hash> options.
    '''
    if not migrator.versioner.get():
        print 'Sorry, the current version is not set. Please set it with roetsj set.'
        return
    try:
        for message in migrator.down(args.to):
            print 'down', pretty_migrations([message.old], headers=[], format='plain')
    except roetsjbaan.MigrationError as e:
        print e.message

def pretty_migrations(migrations, long=False, headers=['', 'Date', 'Hash', 'Description', 'Issue #'], format='simple'):
    '''
    Formats a list of migrations into a sexy ASCII table
    '''
    data = [
        [
            '>' if migrator.versioner.get() == m.hash else ' ',
            time.strftime('%Y-%m-%d', time.gmtime(m.timestamp)),
            m.hash[:len(m.hash) if long else 8], m.description, m.issue
        ]
        for m in migrations
    ]
    return tabulate(reversed(data), headers=headers, tablefmt=format)

def main():
    parser = argparse.ArgumentParser(description='Migrate stuff.')
    subparsers = parser.add_subparsers()

    new_parser = subparsers.add_parser('new', description=new.__doc__)
    new_parser.add_argument('description')
    new_parser.add_argument('--issue')
    new_parser.set_defaults(func=new)

    set_parser = subparsers.add_parser('set')
    set_parser.add_argument('hash')
    set_parser.set_defaults(func=set)

    list_parser = subparsers.add_parser('list', description=list.__doc__)
    list_parser.add_argument('-l', '--long', action='store_true', help='''
        Show the entire migration hash
    ''')
    list_parser.set_defaults(func=list)

    up_parser = subparsers.add_parser('up', description=up.__doc__)
    up_parser.add_argument('-t', '--to', type=str, help='''
        Hash of the migration up to which you wish to upgrade. Defaults to all
        more recent migrations.

    ''')
    up_parser.set_defaults(func=up)

    down_parser = subparsers.add_parser('down', description=down.__doc__)
    down_parser.add_argument('-t', '--to', type=str, help='''
        Hash of the migration up to which you wish to downgrade. Defaults to the
        previous migration.
    ''')
    down_parser.set_defaults(func=down)

    args = parser.parse_args()
    args.func(args)
