#!/usr/bin/env python

from invenio.search_engine import search_pattern, print_record
from invenio.bibrecord import create_record, record_get_field_values


def search_forward(l, s):
    """Find the first item in l which contains a lowercase match for s"""
    for i in range(len(l)):
        if s.lower() in l[i].lower():
            return i
    return -1

def search_backward(l, ci, ti):
    """Search backward through list l, finding first tuple whose index != None"""
    for i in range(ci, -1, -1):
        if l[i] == None:
            continue
        if isinstance(l[i], type(tuple())):
            if l[i][ti] != None:
                return l[i][ti]
        continue
    return None

def suggestAffils(name):
    """Given an author name pattern, find all possible prior affiliations""" 

    search_results = sorted( search_pattern( p=search_for, ap=1 ), reverse=True )
    item_count = len(search_results)

    record_list = [create_record(print_record(x, 'xm'))[0] for x in search_results]

    pauth_affils = [None] * item_count
    for i in range(item_count):

        primary_authors = record_get_field_values(record_list[i], '100', '%', '%', '%')

        x = 2 * search_forward(primary_authors[::2], search_for)
        if x < 0:
            continue 

        try:
            pauth_affils[i] = (primary_authors[x+1], primary_authors[x])
        except IndexError, msg:
            pauth_affils[i] = (search_backward(pauth_affils, i, 0), primary_authors[x])

    return pauth_affils


if __name__ == "__main__":

    import sys

    search_for = 'ellis'
    if len(sys.argv) > 1:
        search_for = sys.argv[1]

    pauth_affils = suggestAffils(search_for)

    print search_for
    for i in range(len(pauth_affils)):
        if pauth_affils[i] != None:
            print '\t', pauth_affils[i]

