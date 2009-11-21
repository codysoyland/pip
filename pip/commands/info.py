import xmlrpclib
import sys
from pip.basecommand import Command

class InfoCommand(Command):
    name = 'info'
    usage = '%prog PACKAGE'
    summary = 'Get package information'

    def run(self, options, args):
        if not args:
            print >> sys.stderr, 'ERROR: Missing required argument (package name).'
            return
        package = args[0]
        print 'Querying package database...'
        pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
        versions = pypi.package_releases(package)
        if not versions:
            print 'No matching packages.'
        else:
            data = pypi.release_data(package, versions[0])
            print 'Name:', data['name']
            print 'Version:', data['version']
            print 'Summary:', data['summary']
            print 'URL:', data['home_page']
            print 'Author:', data['author']
            print 'Author Email:', data['author_email']

InfoCommand()
