## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""Function for archiving files"""

__revision__ = "$Id$"

from invenio.file import BibRecDocs
import os
import re
from invenio.websubmit_config import InvenioWebSubmitFunctionWarning
from invenio.websubmit_functions.Shared_Functions import get_dictionary_from_string, \
     createRelatedFormats, \
     createIcon

def Move_Files_to_Storage(parameters, curdir, form):
    """
    The function moves files received from the standard submission's form through
    file input element(s).
    Websubmit_engine built the following file organization in the directory curdir/files
    
                  curdir/files
                        |
      _______________________________________________________________________________
            |                                   |                          |
      ./file input 1 element's name      ./file input 2 element's name    ....
         |                                     |
      test1.pdf                             test2.pdf
    
    
    There is only one instance of all possible extension(pdf, gz...) in each part
    otherwise we may encount problems when renaming files.
    +parameters['rename']: if given, all the files in curdir/files are renamed.
     parameters['rename'] is of the form: <PA>elemfilename[re]</PA>* where re is
     an regexp to select(using re.sub) what part of the elem file has
     to be selected.e.g <PA>file:TEST_FILE_RN</PA>
    +parameters['documenttype']: if given, other formats are created.
     It has 2 possible values: - if "picture" icon in gif format is created
                               - if "fulltext" ps, gz .... formats are created
    +parameters['paths_and_suffixes']: directories to look into and corresponding
    suffix to add to every file inside. It must have the same structure as a
     python dictionnary of the following form
     {'FrenchAbstract':'french', 'EnglishAbstract':''}
     The keys are the file input element name from the form <=> directories in curdir/files
     The values associated are the suffixes which will be added to all the files
     in e.g. curdir/files/FrenchAbstract
    +parameters['iconsize'] need only if "icon" is selected in parameters['documenttype']
    """
    global sysno
    paths_and_suffixes = parameters['paths_and_suffixes']
    rename = parameters['rename']
    documenttype = parameters['documenttype']
    iconsize = parameters['iconsize']

    ## Create an instance of BibRecDocs for the current recid(sysno)
    bibrecdocs = BibRecDocs(sysno)

    paths_and_suffixes = get_dictionary_from_string(paths_and_suffixes)
        
    ## Go through all the directory specified in the keys
    ## of parameters['paths_and_suffixes']
    for path in paths_and_suffixes.keys():
        ## Check if there is a directory for the current path
        if os.path.exists("%s/files/%s" % (curdir, path)):
            mybibdoc = None
            ## Check if there is no document with the same status (status=path)
            ## already associated with the current recid
            existing_with_same_status = bibrecdocs.listBibDocs(path)
            ## If yes, use the existing docid 
            if existing_with_same_status:
                mybibdoc = existing_with_same_status[0]
            ## Go through all the files in curdir/files/path
            for current_file in os.listdir("%s/files/%s" % (curdir, path)):
                ## retrieve filename and extension 
                filename, extension = os.path.splitext(current_file)
                if len(paths_and_suffixes[path]) != 0:
                    extension = "_%s%s" % (paths_and_suffixes[path], extension)
                ## Build the new file name if rename paramter has been given
                if rename:
                    filename = re.sub('<PA>(?P<content>[^<]*)</PA>', \
                                      get_pa_tag_content, \
                                      parameters['rename'])
                if rename or len(paths_and_suffixes[path]) != 0:
                    ## Rename the file 
                    try:
                        # Write the log rename_cmd
                        fd = open("%s/rename_cmd" % curdir, "a+")
                        fd.write("%s/files/%s/%s" % (curdir, path, current_file) + " to " +\
                                  "%s/files/%s/%s%s" % (curdir, path, filename, extension) + "\n\n")
                        ## Rename
                        os.rename("%s/files/%s/%s" % (curdir, path, current_file), \
                                  "%s/files/%s/%s%s" % (curdir, path, filename, extension))
                        fd.close()
                        ## Save the new name in a text file in curdir so that
                        ## the new filename can be used by templates to created the recmysl 
                        fd = open("%s/%s_RENAMED" % (curdir, path), "w")
                        fd.write("%s%s" % (filename, extension))
                        fd.close()
                    except OSError, err:
                        msg = "Cannot rename the file.[%s]"
                        msg %= str(err)
                        raise InvenioWebSubmitFunctionWarning(msg)
                fullpath = "%s/files/%s/%s%s" % (curdir, path, filename, extension)
                ## Check if there is any existing similar file
                if not bibrecdocs.checkFileExists(fullpath, path):
                    if not mybibdoc:
                        ## New docid is created
                        mybibdoc = bibrecdocs.addNewFile(fullpath, path)
                    else:
                        ## No new docid created but the file
                        ## is archive in /bibdoc ID/ directory 
                        mybibdoc = bibrecdocs.addNewFormat(fullpath, mybibdoc.getId()) 
                ## Create related formats
                if mybibdoc:
                    ## Fulltext
                    if documenttype == "fulltext":
                        additionalformats = createRelatedFormats(fullpath)
                        if len(additionalformats) > 0:
                            mybibdoc.addFilesNewFormat(additionalformats)
                    ## Icon
                    elif documenttype == "picture":
                        iconpath = createIcon(fullpath, iconsize)
                        if iconpath is not None and mybibdoc is not None:
                            mybibdoc.addIcon(iconpath)
                            ## Save the new icon filename in a text file in curdir so that
                            ## it can be used by templates to created the recmysl 
                            try:
                                fd = open("%s/%s_ICON" % (curdir, path), "w")
                                fd.write(os.path.basename(iconpath))
                                fd.close()
                            except OSError, err:
                                msg = "Cannot store icon filename.[%s]"
                                msg %= str(err)
                                raise InvenioWebSubmitFunctionWarning(msg)
                        elif mybibdoc is not None:
                            mybibdoc.deleteIcon()

    return ""

def get_pa_tag_content(pa_content):
    """Get content for <PA>XXX</PA>.
    @param pa_content: MatchObject for <PA>(.*)</PA>.
    return: the content of the file possibly filtered by an regular expression  
    if pa_content=file[re]:a_file => first line of file a_file matching re
    if pa_content=file*p[re]:a_file => all lines of file a_file, matching re,
    separated by - (dash) char.
    """
    pa_content = pa_content.groupdict()['content']
    sep = '-'
    out = ''
    if pa_content.startswith('file'):
        filename = ""
        regexp = ""
        if "[" in pa_content:
            split_index_start = pa_content.find("[")
            split_index_stop =  pa_content.rfind("]")
            regexp = pa_content[split_index_start+1:split_index_stop]
            filename = pa_content[split_index_stop+2:]## ]:
        else :
            filename = pa_content.split(":")[1]
        if os.path.exists(os.path.join(curdir, filename)):
            fp = open(os.path.join(curdir, filename), 'r')
            if pa_content[:5] == "file*":
                out = sep.join(map(lambda x: re.split(regexp, x.strip())[-1], fp.readlines()))
            else:
                out = re.split(regexp, fp.readline().strip())[-1]
            fp.close()
    return out  
    