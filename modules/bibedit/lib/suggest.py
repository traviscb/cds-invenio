#!/usr/bin/env python

from invenio.search_engine import search_pattern, print_record
from invenio.bibrecord import create_record, record_get_field_values, record_get_field_value


def record_auPairs(recID):
    yieldedSomething = False
    record = create_record(print_record(recID, 'xm'))[0]
    
    def extract(l):
        a = None
        u = None
        for key, val in l:
            if key == 'a':
                a = val
            elif key == 'u':
                u = val
        return a, u

    try:
        yield extract( record['100'][0][0] )
        yieldedSomething = True
    except KeyError:
        pass

    try:
        fields = record['700']
    except KeyError:
        if not yieldedSomething:
            yield None, None
        return

    for fieldline in fields:
        tuplist = fieldline[0]
        yield extract( tuplist )

def suggestions(name):
    """Given an author name pattern, find all possible prior affiliations""" 

    previousGood = None

    search_results = sorted( search_pattern( p=search_for, ap=1 ), reverse=True )

    for recID in search_results:
        for author, affiliation in record_auPairs(recID):
            if name.lower() in author.lower():
                if affiliation != None:
                    previousGood = affiliation
                    yield recID, author, affiliation
                else:
                    yield recID, author, previousGood


if __name__ == "__main__":
    """Exploratory test harness"""

    import sys

    search_for = 'ellis'
    if len(sys.argv) > 1:
        search_for = sys.argv[1]

    print search_for
    for recID, auth, affil in suggestions(search_for):
        if affil != None:
            print '\t%5d %35s %35s' % (recID, '"'+auth+'"', '"'+affil+'"')

