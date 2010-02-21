import os
import sys
import xmlrpclib
import textwrap
import time
import pkg_resources
from pip.basecommand import Command
from pip.util import get_terminal_size

class SearchCommand(Command):
    name = 'search'
    usage = '%prog QUERY'
    summary = 'Search PyPI'

    def __init__(self):
        super(SearchCommand, self).__init__()
        self.parser.add_option(
            '--index',
            dest='index',
            metavar='URL',
            default='http://pypi.python.org/pypi',
            help='Base URL of Python Package Index (default %default)')

    def run(self, options, args):
        if not args:
            print >> sys.stderr, 'ERROR: Missing required argument (search query).'
            return
        query = args[0]
        index_url = options.index

        hits = self.search(query, index_url)

        self._print_results(hits)

    def search(self, query, index_url):
        pypi = xmlrpclib.ServerProxy(index_url)
        pypi_hits = pypi.search({'name': query, 'summary': query}, 'or')

        # remove duplicates
        seen_names = []
        hits = []
        for hit in pypi_hits:
            if hit['name'] not in seen_names:
                seen_names.append(hit['name'])
                hits.append(hit)
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

SearchCommand()
