import os
import sys
import xmlrpclib
import textwrap
import time
import pkg_resources
from pip.basecommand import Command
from pip.util import get_terminal_size
from distutils.version import StrictVersion, LooseVersion

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

        pypi_hits = self.search(query, index_url)
        import ipdb; ipdb.set_trace()
        hits = translate_hits(pypi_hits)
        print_results(hits)

    def search(self, query, index_url):
        pypi = xmlrpclib.ServerProxy(index_url)
        hits = pypi.search({'name': query, 'summary': query}, 'or')
        return hits

def translate_hits(hits):
    """
    The list from pypi is really a list of versions. We want a list of
    packages with the list of versions stored inline. This converts the
    list from pypi into one we can use.
    """
    packages = {}
    for hit in hits:
        name = hit['name']
        summary = hit['summary']
        version = hit['version']
        score = hit['_pypi_ordering']

        if name not in packages.keys():
            packages[name] = {'name': name, 'summary': summary, 'versions': [version], 'score': score}
        else:
            packages[name]['versions'].append(version)

            # if this is the highest version, replace summary and score
            if version == highest_version(packages[name]['versions']):
                packages[name]['summary'] = summary
                packages[name]['score'] = score

    # each record has a unique name now, so we will convert the dict into a list sorted by score
    package_list = sorted(packages.values(), lambda x, y: cmp(y['score'], x['score']))
    return package_list

def print_results(hits, name_column_width=25):
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
        try:
            print line
        except UnicodeEncodeError:
            pass

def compare_versions(version1, version2):
    try:
        return cmp(StrictVersion(version1), StrictVersion(version2))
    # in case of abnormal version number, fall back to LooseVersion
    except ValueError:
        return cmp(LooseVersion(version1), LooseVersion(version2))

def highest_version(versions):
    return reduce((lambda v1, v2: compare_versions(v1, v2) == 1 and v1 or v2), versions)

SearchCommand()
