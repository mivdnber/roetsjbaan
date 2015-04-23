import argparse, sys, time
from tabulate import tabulate
import roetsjbaan
import roetsjfile

mig = roetsjbaan.Migrator(roetsjfile.versioner,
    inject=roetsjfile.inject if hasattr(roetsjfile, 'inject') else {},
    directory=roetsjfile.directory if hasattr(roetsjfile, 'directory') else 'migrations'
)

mig.reload()

def list(args):
    print pretty_migrations(mig, long=args.long)

def new(args):
    fn = mig.create(args.description, args.issue)
    print 'Migration created as %s' % fn

def set(args):
    hits = mig.find(args.hash)
    if len(hits) > 1:
        print 'More than one migration corresponds to hash %s:' % args.hash
    else:
        mig.versioner.set(hits[0].hash)
        print 'Current version set to:'
    print pretty_migrations(hits)

def up(args):
    for old, new in mig.up(args.to):
        print 'up', pretty_migrations([new], headers=[], format='plain')

def down(args):
    for old, new in mig.down(args.to):
        print 'down', pretty_migrations([old], headers=[], format='plain')

def pretty_migrations(migrations, long=False, headers=['', 'Date', 'Hash', 'Description', 'Issue #'], format='simple'):
    data = [
        [
            '>' if mig.versioner.get() == m.hash else ' ',
            time.strftime('%Y-%m-%d', time.gmtime(m.timestamp)),
            m.hash[:len(m.hash) if long else 8], m.description, m.issue
        ]
        for m in migrations
    ]
    return tabulate(reversed(data), headers=headers, tablefmt=format)

def main():
    parser = argparse.ArgumentParser(description='Migrate stuff.')
    subparsers = parser.add_subparsers()

    new_parser = subparsers.add_parser('new')
    new_parser.add_argument('description')
    new_parser.add_argument('--issue')
    new_parser.set_defaults(func=new)

    set_parser = subparsers.add_parser('set')
    set_parser.add_argument('hash')
    set_parser.set_defaults(func=set)

    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('-l', '--long', action='store_true', help='''
        Show the entire migration hash
    ''')
    list_parser.set_defaults(func=list)

    up_parser = subparsers.add_parser('up')
    up_parser.add_argument('-t', '--to', type=str, help='''
        Hash of the migration up to which you wish to upgrade. Defaults to all
        more recent migrations.

    ''')
    up_parser.set_defaults(func=up)

    down_parser = subparsers.add_parser('down')
    down_parser.add_argument('-t', '--to', type=str, help='''
        Hash of the migration up to which you wish to downgrade. Defaults to the
        previous migration.
    ''')
    down_parser.set_defaults(func=down)

    args = parser.parse_args()
    args.func(args)
