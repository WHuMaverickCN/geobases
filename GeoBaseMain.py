#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
This module is a launcher for GeoBase.
'''



from GeoBases.GeoBaseModule import GeoBase

import os
import os.path as op
import argparse

from datetime import datetime
from termcolor import colored
import colorama

import sys


def getTermSize():

    size  = os.popen('stty size', 'r').read()

    if not size:
        return (80, 160)

    return tuple(int(d) for d in size.split())



class RotatingColors(object):

    def __init__(self):

        self._availables = [
             ('white', None),
             ('cyan', 'on_grey')
        ]

        self._current = 0


    def next(self):

        self._current += 1

        if self._current == len(self._availables):
            self._current = 0

        return self


    def get(self):

        return self._availables[self._current]


    def getEmph(self):

        return ('grey', 'on_green')


    def getHeader(self):

        return ('grey', 'on_yellow')


def display(geob, list_of_things, omit, show):

    if show is None:
        show = geob._headers

    # Different behaviour given
    # number of results
    # We adapt the width between 25 and 40 
    #given number of columns and term width
    n = len(list_of_things)

    lim = min(40, max(25, int(getTermSize()[1] / float(n+1))))

    if n == 1:
        # We do not truncate names if only one result
        truncate = None
    else:
        truncate = lim

    # Highlighting some rows
    important = set(['code', 'name'])

    c = RotatingColors()
    col = c.getHeader()

    sys.stdout.write('\n' + fixed_width('ref', col, lim, truncate))

    for (h, k) in list_of_things:
        sys.stdout.write(fixed_width(h, col, lim, truncate))

    for f in show:
        if f not in omit:

            if f in important:
                col = c.getEmph()
            else:
                col = c.get()

            sys.stdout.write('\n' + fixed_width(f, col, lim, truncate))

            for (h, k) in list_of_things:
                sys.stdout.write(fixed_width(geob.get(k, f), col, lim, truncate))

            c.next()

    sys.stdout.write('\n')



def fixed_width(s, col, lim=25, truncate=None):

    if truncate is None:
        truncate = 1000

    return colored((('%-' + str(lim) + 's') % s)[0:truncate], *col)



def scan_coords(u_input, geob):

    try:
        coords = tuple(float(l) for l in u_input.split(',', 1))

    except ValueError:

        if u_input in geob:
            return geob.getLocation(u_input)
        else:
            return None

    else:
        return coords





def main():

    # Filter colored signals on terminals.
    # Necessary for Windows CMD
    colorama.init()

    #
    # COMMAND LINE MANAGEMENT
    #
    parser = argparse.ArgumentParser(description='Provide POR information.')

    parser.epilog = 'Example: python %s ORY' % parser.prog

    '''parser.add_argument('keys',
        help = 'Keys',
        nargs = '+',
        default='-'
    )'''

    parser.add_argument('keys',
                        #type=argparse.FileType('r'),
                        default='-',
                        nargs='+')

    parser.add_argument('-b', '--base',
        help = '''Choose a different base, default is ori_por. Also available are
                        stations, stations_nls, airports, airports_csv, countries.''',
        default = 'ori_por'
    )

    parser.add_argument('-f', '--fuzzy',
        help = '''Rather than looking up a key, this mode will search the best
                        match from the field given by --field option.''',
        action='store_true'
    )

    parser.add_argument('-F', '--field',
        help = '''When performing a fuzzy search, specify the field to be chosen.
                        Default is "name".''',
        default='name'
    )

    parser.add_argument('-l', '--limit',
        help = '''Specify a limit when performing fuzzy searches, or geographical
                        searches. May be a radius in km or a number of results
                        given the context of the search (see --near, --closest and
                       --fuzzy). Default is 3''',
        default = 3
    )

    parser.add_argument('-n', '--near',
        help = '''Rather than looking up a key, this mode will search the entries
                        in a radius from a geocode or a key. Radius is given by --limit option,
                        and geocode is passed as main argument.''',
        action='store_true'
    )

    parser.add_argument('-c', '--closest',
        help = '''Rather than looking up a key, this mode will search the closest entries
                        from a geocode or a key. Number of results is limited by --limit option,
                        and geocode is passed as main argument.''',
        action='store_true'
    )

    parser.add_argument('-w', '--without_grid',
        help = '''When performing a geographical search, a geographical index is used.
                        This may lead to inaccurate results in some (rare) cases. Adding this
                        option will disable the index, and browse the full data set to
                        look for the results.''',
        action='store_true'
    )

    parser.add_argument('-q', '--quiet',
        help = '''Does not provide the verbose output.''',
        action='store_true'
    )

    parser.add_argument('-o', '--omit',
        help = '''Does not print some characteristics of POR in stdout.
                        May help to get cleaner output.''',
        nargs = '+',
        default = []
    )

    parser.add_argument('-s', '--show',
        help = '''Only print some characterics of POR in stdout.
                        May help to get cleaner output.''',
        nargs = '+',
        default = None
    )

    args = vars(parser.parse_args())



    #
    # ARGUMENTS
    #
    limit = float(args['limit'])



    #
    # FETCHING
    #
    if not args['quiet']:
        print 'Loading GeoBase...'

    g = GeoBase(data=args['base'], verbose=False)

    if args['fuzzy'] or args['near'] or args['closest']:
        key = args['keys'][0]
    else:
        key = args['keys']


    if not args['quiet']:

        before = datetime.now()

        if isinstance(key, str):
            print 'Looking for matches from "%s"...' % key
        else:
            print 'Looking for matches from %s...' % ', '.join(key)


    if args['fuzzy']:

        res = g.fuzzyGet(key, args['field'], approximate=int(limit))

    elif args['near']:

        coords = scan_coords(key, g)

        if coords is None:
            print 'Key %s was not in GeoBase, for data "%s" and source %s' % \
                (key, g._data, g._source)
            exit(1)

        if args['without_grid']:
            res = sorted(g.findNearPoint(*coords, radius=limit))
        else:
            res = sorted(g.gridFindNearPoint(*coords, radius=limit))


    elif args['closest']:

        coords = scan_coords(key, g)

        if coords is None:
            print 'Key %s was not in GeoBase, for data "%s" and source %s' % \
                (key, g._data, g._source)
            exit(1)

        if args['without_grid']:
            res = g.findClosestFromPoint(*coords, N=int(limit))
        else:
            res = g.gridFindClosestFromPoint(*coords, N=int(limit))

    else:
        res = [(i, k) for i, k in enumerate(key)]


    #
    # DISPLAY
    #
    for (h, k) in res:
        if k not in g:
            print 'Key %s was not in GeoBase, for data "%s" and source %s' % \
                (k, g._data, g._source)
            exit(1)

    if not args['quiet']:

        display(g, res, set(args['omit']), args['show'])

        print '\nDone in %s' % (datetime.now() - before)
    else:
        for (h, k) in res:
            print '%s^%.5f' % (k, h)


if __name__ == '__main__':

    main()

