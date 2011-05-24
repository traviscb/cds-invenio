#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########+#########+#########+#########+#########+#########+#########+#########
# Copyright (C) 2010  SLAC National Accelerator Laboratory
#
#This program is free software: you can redistribute it and/or modify it under
#the terms of the GNU General Public License as published by the Free Software
#Foundation, either version 3 of the License, or (at your option) any later
#version.
#
#This program is distributed in the hope that it will be useful, but WITHOUT
#ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#details.
#
#You should have received a copy of the GNU General Public License along with
#this program.  If not, see <http://www.gnu.org/licenses/>.
"""cli: Load this into ipython to make interactive Invenio use nicer

cli is an Invenio module intended to make working with Invenio interactively
(for example, for exploratory bibliometrics) a lot more comfortable.
"""

import invenio
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_record, get_fieldvalues
from invenio.bibrank_citation_searcher import get_citation_dict
from invenio.bibformat import format_record
from invenio.bibformat import format_records
from invenio.intbitset import intbitset
from invenio.bibformat_dblayer import get_tags_from_name

FORWARD_CITATION_DICTIONARY = None


def get_cite_counts(query = None):
    """Generate the recid, citation count pairs for a given search

    If query is given, gives counts for recids in search results.
    If query is empty, gives counts for all recids with cites >=1.

    Sample Usage:
    [x for x in cli.get_cite_counts('recid:95')]
    results in:
    [(95, 2)]
    """
    global FORWARD_CITATION_DICTIONARY
    if FORWARD_CITATION_DICTIONARY == None:
        FORWARD_CITATION_DICTIONARY = get_citation_dict('citationdict')
    cites = FORWARD_CITATION_DICTIONARY
    if query != None:
        recids = perform_request_search(p=query)
        for recid in recids:
            if cites.has_key(recid):
                yield recid, len(cites[recid])
            else:
                yield recid, 0
    else:
        for recid in cites:
            yield recid, len(cites[recid])

def irn(recid):
    """Return the first (only) IRN of a given recid, or None"""
    irnlist = get_fieldvalues(recid, '970__a')
    if len(irnlist) > 0:
        return irnlist[0]
    else:
        return None

def field(recid, name):
    """Return the first value of the field corresponding to the given tag
    name in the given recid, or None"""
    datalist = fields(recid, name)
    if len(datalist) > 0:
        return datalist[0]
    else:
        return None

def fields(recid, name):
    """Return the list of values of the field corresponding to the given tag
    name in the given recid, or None"""
    fields = get_tags_from_name(name)
    if len(fields) > 0:
        return(get_fieldvalues(recid, fields[0]))
    else:
        return None


def add_field(recid, field, subfield):
    """ Add (append) a field/subfieldto the specified RECID.
    WARNING - this bypasses the bibupload queue and should only be used if
    you know the queue is clear.
    subfield is as in bibRecord record_add_field, a list of tuples
    [(subfield, value), (subf, value)]

    Returns None if fails to update record, or (err, recid)
    """
    from invenio.bibrecord import record_add_field
    from invenio.bibupload import bibupload

    tmp_rec = get_record(recid)
    if len(tmp_rec) == 0:
        print "Failed to find Record:" + recid
        return None
    if record_add_field(tmp_rec,field,subfields=subfield) > -1:
        err = bibupload(tmp_rec,opt_mode="replace")
        if err[0] == 0:
            print "updated " + str(err[1])
            return err
        else:
            print "error updating " + str(err[1]) + "  (error:" + err[0] + ")"
            return err
    else:
        print "error in adding field to record, no changes made"
        return None

def write_record(id, mode="a", format="xm", strip_control="False",
    filename="", file=None):
    """ print record to file
    if file and filename given as args, file takes precedence
    strip_control=True removes all control fields to make it easier to use
    output (in xm format) to bibupload (only works in xm)

    """

    if (file == None):
        f = open(filename,mode)
    else:
        f = file
    out = format_record(id,format)
    if strip_control:
        tmp = ''
        for line in out.split("\n"):
            if not line.startswith("  <controlfield"):
                tmp += line + " \n"
    f.write(out)
    if file == None:
        f.close()
    return(1)

def get_authors(record):
    '''return the author fields 100/700s in one list from a record

    @param record: a record object from get_record
    @return a list of author objects like record[100][0]
    '''
    authors = []
    if record.has_key('100'):
        authors.append(record['100'][0])
    if record.has_key('700'):
        authors.extend(record['700'])
    return(authors)


if __name__ == "__main__":
    """FIXME: As a command, cli should either run its unit tests, or invoke ipython"""
    pass
