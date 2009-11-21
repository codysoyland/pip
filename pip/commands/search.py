import os
import sys
import xmlrpclib
import shelve
import textwrap
import time
import pkg_resources
from pip.basecommand import Command
from pip.locations import default_config_dir
from pip.util import get_terminal_size

class SearchCommand(Command):
    name = 'search'
    usage = '%prog QUERY'
    summary = 'Search PyPI'

    def __init__(self):
        super(SearchCommand, self).__init__()
        self.parser.add_option(
            '-r', '--reindex',
            dest='reindex',
            action='store_true',
            help='Re-index local search cache.')
        self.parser.add_option(
            '-d', '--direct',
            dest='direct',
            action='store_true',
            help='Search PyPI directly instead local cache.')

    def run(self, options, args):
        if options.reindex:
            action = self.reindex
        else:
            action = self.search
        action(options, args)

    def search(self, options, args):
        if not args:
            print >> sys.stderr, 'ERROR: Missing required argument (search query).'
            return
        query = args[0]

        if options.direct:
            hits = self.direct_search(query)
        else:
            hits = self.local_search(query)

        self._print_results(hits)

    def direct_search(self, query):
        pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
        pypi_hits = pypi.search({'name': query, 'summary': query}, 'or')

        # remove duplicates
        seen_names = []
        hits = []
        for hit in pypi_hits:
            if hit['name'] not in seen_names:
                seen_names.append(hit['name'])
                hits.append(hit)
        return hits

    def local_search(self, query):
        if not os.path.exists(self._index_file()):
            print >> sys.stderr, 'ERROR: Search index does not exist. Run "pip search --reindex" to create it.'
            return []
        if os.path.getmtime(self._index_file()) < time.time() - 2592000:
            print >> sys.stderr, 'NOTICE: Search index is more than 30 days old. Run "pip search --reindex" to update it.'

        hits = []
        query = query.lower()
        db = shelve.open(self._index_file())
        pkgs = db['search-index']
        hits = [pkg for pkg in pkgs
                if query in pkg['name'].lower()
                or (pkg['summary'] is not None
                    and query in pkg['summary'].lower())]
        db.close()
        return hits

    def _print_results(self, hits, name_column_width=25):
        installed_packages = [p.project_name for p in pkg_resources.working_set]
        terminal_size = get_terminal_size()
        terminal_width = terminal_size[0]
        for hit in hits:
            name = hit['name']
            summary = hit['summary'] or ''
            summary = textwrap.wrap(summary, terminal_width - name_column_width - 5)
            installed = name in installed_packages
            if installed:
                flag = 'i'
            else:
                flag = 'n'
            line = '%s %s - %s' % (
                flag,
                name.ljust(name_column_width),
                ('\n' + ' ' * (name_column_width + 5)).join(summary),
            )
            print line

    def _index_file(self):
        return os.path.join(default_config_dir, 'index.db')

    def reindex(self, options, args):
        print 'Downloading and updating local search index...'
        pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
        pkgs = pypi.search({})
        index_file = self._index_file()
        if not os.path.exists(os.path.dirname(index_file)):
            os.makedirs(os.path.dirname(index_file))
        db = shelve.open(index_file)
        currently_indexed = [pkg['name'] for pkg in db.get('search-index', [])]
        new_pkg_count = 0
        for pkg in pkgs:
            if pkg['name'] not in currently_indexed:
                new_pkg_count += 1
        db['search-index'] = pkgs
        db['version'] = 1
        db.close()
        print '%s new packages indexed successfully in "%s"' % (new_pkg_count, index_file)

SearchCommand()
