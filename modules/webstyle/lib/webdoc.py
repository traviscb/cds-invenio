# -*- coding: utf-8 -*-
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

"""
WebDoc -- Transform webdoc sources into static html files
"""

__revision__ = \
    "$Id$"


from invenio.config import \
     CFG_PREFIX, \
     cdslang, \
     cdslangs, \
     cdsname, \
     supportemail, \
     adminemail, \
     weburl, \
     sweburl, \
     version, \
     cdsnameintl, \
     cachedir
from invenio.dateutils import convert_datestruct_to_dategui
from invenio.messages import \
     gettext_set_language, \
     wash_language

import re
import getopt
import os
import sys
import time

# List of (webdoc_source_dir, webdoc_cache_dir)
webdoc_dirs = [('%s/lib/webdoc/help' % CFG_PREFIX, \
                '%s/webdoc/help-pages' % cachedir),
               ('%s/lib/webdoc/admin' % CFG_PREFIX, \
                '%s/webdoc/admin-pages' % cachedir),
               ('%s/lib/webdoc/hacking' % CFG_PREFIX, \
                '%s/webdoc/hacking-pages' % cachedir)]

# Regular expression for finding text to be translated
translation_pattern = re.compile(r'_\((?P<word>.*?)\)_', \
                                 re.IGNORECASE | re.DOTALL | re.VERBOSE)

# # Regular expression for finding comments
comments_pattern = re.compile(r'^\s*#.*$', \
                                   re.MULTILINE)

# Regular expression for finding <lang:current/> tag
pattern_lang_current = re.compile(r'<lang \s*:\s*current\s*\s*/>', \
                                  re.IGNORECASE | re.DOTALL | re.VERBOSE)


# Regular expression for finding <lang:link/> tag
pattern_lang_link_current = re.compile(r'<lang \s*:\s*link\s*\s*/>', \
                                  re.IGNORECASE | re.DOTALL | re.VERBOSE)


# Regular expression for finding <!-- %s: %s --> tag
# where %s will be replaced at run time
pattern_tag = r'''
    <!--\s*(?P<tag>%s)   #<!-- %%s tag (no matter case)
    \s*:\s*
    (?P<value>.*?)         #description value. any char that is not end tag
    (\s*-->)            #end tag
    '''

# List of available tags in wml, and the pattern to find it
pattern_tags = {'WebDoc-Page-Title': '',
                'WebDoc-Page-Navtrail': '',
                'WebDoc-Page-Navbar-Name': '',
                'WebDoc-Page-Navbar-Select': '',
                'WebDoc-Page-Description': '',
                'WebDoc-Page-Keywords': '',
                'WebDoc-Page-Header-Add': '',
                'WebDoc-Page-Box-Left-Top-Add': '',
                'WebDoc-Page-Box-Left-Bottom-Add': '',
                'WebDoc-Page-Box-Right-Top-Add': '',
                'WebDoc-Page-Box-Right-Bottom-Add': '',
                'WebDoc-Page-Footer-Add': '',
                'WebDoc-Page-Revision': ''
                }
for tag in pattern_tags.keys():
    pattern_tags[tag] = re.compile(pattern_tag % tag, \
                                   re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <lang>...</lang> tag
pattern_lang = re.compile(r'''
    <lang              #<lang tag (no matter case)
    \s*
    (?P<keep>keep=all)*
    \s*                #any number of white spaces
    >                  #closing <lang> start tag
    (?P<langs>.*?)     #anything but the next group (greedy)
    (</lang\s*>)       #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Builds regular expression for finding each known language in <lang> tags
ln_pattern_text = r"<(?P<lang>"
ln_pattern_text += r"|".join(cdslangs)
ln_pattern_text += r')\s*(revision="[^"]"\s*)?>(?P<translation>.*?)</\1>'
ln_pattern =  re.compile(ln_pattern_text, re.IGNORECASE | re.DOTALL)

defined_tags = {'<CDSNAME>': cdsname,
                '<SUPPORTEMAIL>': supportemail,
                '<ADMINEMAIL>': adminemail,
                '<WEBURL>': weburl,
                '<SWEBURL>': sweburl,
                '<VERSION>': version,
                '<CDSNAMEINTL>': cdsnameintl}

def get_webdoc_parts(webdoc,
                     parts=['title', \
                            'keywords', \
                            'navtrail', \
                            'body',\
                            'navbar-name'],
                     update_cache_mode=1,
                     ln=cdslang,
                     verbose=0):
    """
    Returns the html of the specified 'webdoc' part(s).

    Also update the cache if 'update_cache' is True.

    Parameters:

                  webdoc - *string* the name of a webdoc that can be
                            found in standard webdoc dir, or a webdoc
                            filepath. Priority is given to filepath if
                            both match.

                   parts - *list(string)* the parts that should be
                            returned by this function. Can be in:
                            'title', 'keywords', 'navbar-name',
                            'navtrail', 'body'

       update_cache_mode - *int* update the cached version of the
                            given 'webdoc':
                               - 0 : do not update
                               - 1 : update if needed
                               - 2 : always update

    Returns : *dictionary* with keys being in 'parts' input parameter and values
              being the corresponsding html part.
    """
    html_parts = {}

    if update_cache_mode in [1, 2]:
        update_webdoc_cache(webdoc, update_cache_mode, verbose)

    for part in parts:
        for (_webdoc_source_dir, _web_doc_cache_dir) in webdoc_dirs:
            webdoc_cached_part_path = _web_doc_cache_dir + os.sep + webdoc + \
                                      os.sep + webdoc + '.' + part + '-' + \
                                      ln + '.html'

            if os.path.exists(webdoc_cached_part_path):
                webdoc_cached_part = file(webdoc_cached_part_path, 'r').read()
                html_parts[part] = webdoc_cached_part
                break
            elif ln != cdslang:
                # Get the part in the default language
                default_html_part = get_webdoc_parts(webdoc=webdoc,
                                                     parts=[part],
                                                     update_cache_mode=update_cache_mode,
                                                     ln=cdslang,
                                                     verbose=verbose)
                if default_html_part.has_key(part):
                    html_parts[part] = default_html_part[part]
                    break

    return html_parts

def update_webdoc_cache(webdoc, mode=1, verbose=0, languages=cdslangs):
    """
    Update the cache (on disk) of the given webdoc.

    Parameters:

            webdoc       - *string* the name of a webdoc that can be
                           found in standard webdoc dir, or a webdoc
                           filepath.

            mode         - *int* update cache mode:
                                - 0 : do not update
                                - 1 : only if necessary (webdoc source
                                      is newer than its cache)
                                - 2 : always update
    """
    if mode in [1, 2]:
        (webdoc_source_path, \
         webdoc_cache_dir, \
         webdoc_name,\
         webdoc_source_modification_date, \
         webdoc_cache_modification_date) = get_webdoc_info(webdoc)

        if mode == 1 and \
               webdoc_source_modification_date < webdoc_cache_modification_date and \
               get_mo_last_modification() < webdoc_cache_modification_date:
            # Cache was update after source. No need to update
            return
        (webdoc_source, \
         webdoc_cache_dir, \
         webdoc_name) = read_webdoc_source(webdoc)

        if webdoc_source is not None:
            htmls = transform(webdoc_source, languages=languages)
            for (lang, body, title, keywords, navbar_name, \
                 navtrail) in htmls:
                # Body
                if body is not None:
                    try:
                        write_cache_file('%(name)s.body%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         body,
                                         verbose)
                    except IOError, e:
                        print e
                    except OSError, e:
                        print e

                # Title
                if title is not None:
                    try:
                        write_cache_file('%(name)s.title%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         title,
                                         verbose)
                    except IOError, e:
                        print e
                    except OSError, e:
                        print e

                # Keywords
                if keywords is not None:
                    try:
                        write_cache_file('%(name)s.keywords%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         keywords,
                                         verbose)
                    except IOError, e:
                        print e
                    except OSError, e:
                        print e

                # Navtrail
                if navtrail is not None:
                    try:
                        write_cache_file('%(name)s.navtrail%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         navtrail,
                                         verbose)
                    except IOError, e:
                        print e
                    except OSError, e:
                        print e

                # Navbar name
                if navbar_name is not None:
                    try:
                        write_cache_file('%(name)s.navbar-name%(lang)s.html' % \
                                         {'name': webdoc_name,
                                          'lang': '-'+lang},
                                         webdoc_cache_dir,
                                         navbar_name,
                                         verbose)
                    except IOError, e:
                        print e
                    except OSError, e:
                        print e

                # Last updated file
                try:
                    write_cache_file('last_updated',
                                     webdoc_cache_dir,
                                     convert_datestruct_to_dategui(time.localtime()),
                                     verbose=0)
                except IOError, e:
                    print e
                except OSError, e:
                    print e

            if verbose > 0:
                print 'Written cache in %s' % webdoc_cache_dir

def read_webdoc_source(webdoc):
    """
    Returns the source of the given webdoc, along with the path to its
    cache directory.

    Returns (None, None, None) if webdoc cannot be found.

    Parameters:

            webdoc       - *string* the name of a webdoc that can be
                           found in standard webdoc dir, or a webdoc
                           filepath. Priority is given to filepath if
                           both match.

    Returns: *tuple* (webdoc_source, webdoc_cache_dir, webdoc_name)
    """

    (webdoc_source_path, \
     webdoc_cache_dir, \
     webdoc_name,\
     webdoc_source_modification_date, \
     webdoc_cache_modification_date) = get_webdoc_info(webdoc)

    if webdoc_source_path is not None:
        webdoc_source = file(webdoc_source_path, 'r').read()
    else:
        webdoc_source = None

    return (webdoc_source, webdoc_cache_dir, webdoc_name)

def get_webdoc_info(webdoc):
    """
    Locate the file corresponding to given webdoc and returns its
    path, the path to its cache directory (even if it does not exist
    yet), the last modification dates of the source and the cache, and
    the webdoc name (i.e. webdoc id)

    Parameters:

       webdoc - *string* the name of a webdoc that can be found in
                 standard webdoc dir, or a webdoc filepath. Priority
                 is given to filepath if both match.

    Returns: *tuple* (webdoc_source_path, webdoc_cache_dir,
                      webdoc_name webdoc_source_modification_date,
                      webdoc_cache_modification_date)
    """
    webdoc_source_path = None
    webdoc_cache_dir = None
    webdoc_name = None
    last_updated_date = None
    webdoc_source_modification_date = 1
    webdoc_cache_modification_date  = 0

    # Search at given path or in webdoc cache dir
    if os.path.exists(os.path.abspath(webdoc)):
        webdoc_source_path = os.path.abspath(webdoc)
        (webdoc_cache_dir, webdoc_name) = os.path.split(webdoc_source_path)
        (webdoc_name, extension) = os.path.splitext(webdoc_name)
        webdoc_source_modification_date = os.stat(webdoc_source_path).st_mtime
    else:
        for (_webdoc_source_dir, _web_doc_cache_dir) in webdoc_dirs:
            webdoc_source_path = _webdoc_source_dir + os.sep + \
                                 webdoc + '.webdoc'
            if os.path.exists(webdoc_source_path):
                webdoc_cache_dir = _web_doc_cache_dir + os.sep + webdoc
                webdoc_name = webdoc
                webdoc_source_modification_date = os.stat(webdoc_source_path).st_mtime
                break
            else:
                webdoc_source_path = None
                webdoc_name = None
                webdoc_source_modification_date = 1

    if webdoc_cache_dir is not None and \
           os.path.exists(webdoc_cache_dir + os.sep + 'last_updated'):
        webdoc_cache_modification_date = os.stat(webdoc_cache_dir + \
                                                os.sep + \
                                                 'last_updated').st_mtime

    return (webdoc_source_path, webdoc_cache_dir, webdoc_name,
            webdoc_source_modification_date, webdoc_cache_modification_date)

def transform(webdoc_source, verbose=0, req=None, languages=cdslangs):
    """
    Transform a WebDoc into html

    This is made through a serie of transformations, mainly substitutions.

    Parameters:

      - webdoc_source   :  *string* the WebDoc input to transform to HTML
    """
    parameters = {} # Will store values for specified parameters, such
                    # as 'Title' for <!-- WebDoc-Page-Title: Title -->

    def get_param_and_remove(match):
        """
        Analyses 'match', get the parameter and return empty string to
        remove it.

        Called by substitution in 'transform(...)', used to collection
        parameters such as <!-- WebDoc-Page-Title: Title -->

        @param match a match object corresponding to the special tag
        that must be interpreted
        """
        tag = match.group("tag")
        value = match.group("value")
        parameters[tag] = value
        if tag == 'WebDoc-Page-Revision':
            # Special case: print version
            try:
                (junk, filename, revision, date, junk, junk, junk, junk) = value.split(' ')
                parameters['WebDoc-Page-Last-Updated'] = date
                return revision + ', ' + date
            except ValueError:
                # Date is not correctly formatted. Nothing to do
                pass

        return ''

    def translate(match):
        """
        Translate matching values
        """
        word = match.group("word")
        translated_word = _(word)
        return translated_word

    # 1 step
    ## First filter, used to remove comments
    ## and <protect> tags
    uncommented_webdoc = ''
    for line in webdoc_source.splitlines(True):
        if not line.strip().startswith('#'):
            uncommented_webdoc += line
    webdoc_source = uncommented_webdoc.replace('<protect>', '')
    webdoc_source = webdoc_source.replace('</protect>', '')

    html_texts = {}
    # Language dependent filters
    for ln in languages:
        _ = gettext_set_language(ln)

        # Check if translation is really needed
        ## Just a quick check. Might trigger false negative, but it is
        ## ok.
        if ln != cdslang and \
           translation_pattern.search(webdoc_source) is None and \
           pattern_lang_link_current.search(webdoc_source) is None and \
           pattern_lang_current.search(webdoc_source) is None and \
           '<%s>' % ln not in webdoc_source and \
           ('_(') not in webdoc_source:
            continue

        # 2 step
        ## Filter used to translate string in _(..)_
        localized_webdoc = translation_pattern.sub(translate, webdoc_source)

        # 3 step
        ## Print current language 'en', 'fr', .. instead of
        ## <lang:current /> tags and '?ln=en', '?ln=fr', .. instead of
        ## <lang:link /> if ln is not default language
        if ln != cdslang:
            localized_webdoc = pattern_lang_link_current.sub('?ln=' + ln, localized_webdoc)
        else:
            localized_webdoc = pattern_lang_link_current.sub('', localized_webdoc)
        localized_webdoc = pattern_lang_current.sub(ln, localized_webdoc)

        # 4 step
        ## Filter out languages
        localized_webdoc = filter_languages(localized_webdoc, ln, defined_tags)

        # 5 Step
        ## Replace defined tags with their value from config file
        ## Eg. replace <weburl> with 'http://cdsweb.cern.ch/':
        for defined_tag, value in defined_tags.iteritems():
            if defined_tag.upper() == '<CDSNAMEINTL>':
                localized_webdoc = localized_webdoc.replace(defined_tag, \
                                                            value.get(ln, value['en']))
            else:
                localized_webdoc = localized_webdoc.replace(defined_tag, value)

        # 6 step
        ## Get the parameters defined in HTML comments, like
        ## <!-- WebDoc-Page-Title: My Title -->
        localized_body = localized_webdoc
        for tag, pattern in pattern_tags.iteritems():
            localized_body = pattern.sub(get_param_and_remove, localized_body)

        out = localized_body

        html_texts[ln] =(ln,
                         out,
                         parameters.get('WebDoc-Page-Title'),
                         parameters.get('WebDoc-Page-Keywords'),
                         parameters.get('WebDoc-Page-Navbar-Name'),
                         parameters.get('WebDoc-Page-Navtrail'))

    # Remove duplicates
    filtered_html_texts = []
    if html_texts.has_key(cdslang):
        filtered_html_texts = [(html_text[0], \
                                (html_text[1] != html_texts[cdslang][1] and html_text[1]) or None, \
                                (html_text[2] != html_texts[cdslang][2] and html_text[2]) or None, \
                                (html_text[3] != html_texts[cdslang][3] and html_text[3]) or None, \
                                (html_text[4] != html_texts[cdslang][4] and html_text[4]) or None, \
                                (html_text[5] != html_texts[cdslang][5] and html_text[5]) or None)
                               for html_text in html_texts.values() \
                               if html_text[0] != cdslang]
        filtered_html_texts.append(html_texts[cdslang])
    else:
        filtered_html_texts = html_texts.values()

    return filtered_html_texts

def mymkdir(newdir, mode=0777):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mymkdir(head, mode)
        if tail:
            os.umask(022)
            os.mkdir(newdir, mode)

def write_cache_file(filename, webdoc_cache_dir, filebody, verbose=0):
    """Write a file inside WebDoc cache dir.
    Raise an exception if not possible
    """
    # open file:
    mymkdir(webdoc_cache_dir)
    fullfilename = webdoc_cache_dir + os.sep + filename

    os.umask(022)
    f = open(fullfilename, "w")
    f.write(filebody)
    f.close()
    if verbose > 2:
        print 'Written %s' % fullfilename

def get_mo_last_modification():
    """
    Returns the timestamp of the most recently modified mo (compiled
    po) file
    """
    # Take one of the mo files. They are all installed at the same
    # time, so last modication date should be the same
    mo_file = '%s/share/locale/%s/LC_MESSAGES/cds-invenio.mo' % (CFG_PREFIX, cdslang)

    if os.path.exists(os.path.abspath(mo_file)):
        return os.stat(mo_file).st_mtime
    else:
        return 0

def filter_languages(text, ln='en', defined_tags=None):
    """
    Filters the language tags that do not correspond to the specified language.
    Eg: <lang><en>A book</en><de>Ein Buch</de></lang> will return
         - with ln = 'de': "Ein Buch"
         - with ln = 'en': "A book"
         - with ln = 'fr': "A book"

    Also replace variables such as <WEBURL> and <CDSNAMEINTL> inside
    <lang><..><..></lang> tags in order to print them with the correct
    language

    @param text the input text
    @param ln the language that is NOT filtered out from the input
    @return the input text as string with unnecessary languages filtered out
    @see bibformat_engine.py, from where this function was originally extracted
    """
    # First define search_lang_tag(match) and clean_language_tag(match), used
    # in re.sub() function
    def search_lang_tag(match):
        """
        Searches for the <lang>...</lang> tag and remove inner localized tags
        such as <en>, <fr>, that are not current_lang.

        If current_lang cannot be found inside <lang> ... </lang>, try to use 'cdslang'

        @param match a match object corresponding to the special tag that must be interpreted
        """
        current_lang = ln

        # If <lang keep=all> is used, keep all languages
        keep = False
        if match.group("keep") is not None:
            keep = True

        def clean_language_tag(match):
            """
            Return tag text content if tag language of match is output language.

            Called by substitution in 'filter_languages(...)'

            @param match a match object corresponding to the special tag that must be interpreted
            """
            if match.group('lang') == current_lang or \
                   keep == True:
                return match.group('translation')
            else:
                return ""
            # End of clean_language_tag(..)

        lang_tag_content = match.group("langs")
        # Try to find tag with current lang. If it does not exists,
        # then current_lang becomes cdslang until the end of this
        # replace
        pattern_current_lang = re.compile(r"<("+current_lang+ \
                                          r")\s*>(.*?)(</"+current_lang+r"\s*>)", re.IGNORECASE | re.DOTALL)

        if re.search(pattern_current_lang, lang_tag_content) is None:
            current_lang = cdslang

        cleaned_lang_tag = ln_pattern.sub(clean_language_tag, lang_tag_content)
        # Remove empty lines
        # Only if 'keep' has not been set
        if keep == False:
            stripped_text = ''
            for line in cleaned_lang_tag.splitlines(True):
                if line.strip():
                    stripped_text += line
            cleaned_lang_tag = stripped_text

        return cleaned_lang_tag
        # End of search_lang_tag(..)

    filtered_text = pattern_lang.sub(search_lang_tag, text)
    return filtered_text

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options] webdocfile\n" % sys.argv[0])
    sys.stderr.write("  -h,  --help                \t\t Print this help.\n")
    sys.stderr.write("  -V,  --version             \t\t Print version information.\n")
    sys.stderr.write("  -v,  --verbose=LEVEL       \t\t Verbose level (0=min,1=normal,9=max).\n")
    sys.stderr.write("  -l,  --language=LN1,LN2,.. \t\t Language(s) to process (default all)\n")
    sys.stderr.write("  -m,  --mode=MODE           \t\t Update cache mode(0=Never,1=if necessary,2=always) (default 2)\n")
    sys.stderr.write("\n")
    sys.stderr.write(" Example: webdoc help-pages\n")
    sys.stderr.write(" Example: webdoc -l en,fr help-pages\n")
    sys.stderr.write(" Example: webdoc -m 1 help-pages")
    sys.stderr.write("\n")

    sys.exit(exitcode)

def main():
    """
    main entry point for webdoc via command line
    """
    options = {'language':cdslangs, 'verbose':1, 'mode':2}

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hVv:l:m:",
                                   ["help",
                                    "version",
                                    "verbose=",
                                    "language=",
                                    "mode="])
    except getopt.GetoptError, err:
        usage(1, err)

    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)
            elif opt[0] in ["-V", "--version"]:
                print __revision__
                sys.exit(0)
            elif opt[0] in ["-v", "--verbose"]:
                options["verbose"]  = int(opt[1])
            elif opt[0] in ["-l", "--language"]:
                options["language"]  = [wash_language(lang.strip().lower()) \
                                        for lang in opt[1].split(',') \
                                        if lang in cdslangs]
            elif opt[0] in ["-m", "--mode"]:
                options["mode"] = opt[1]
    except StandardError, e:
        usage(e)

    try:
        options["mode"] = int(options["mode"])
    except ValueError:
        usage(1, "Mode must be an integer")

    options["webdoc"] = args[0]

    if not options.has_key("webdoc"):
        usage(0)

    # check if webdoc exists
    infos = get_webdoc_info(options["webdoc"])
    if infos[0] is None:
        usage(1, "Could not find %s" %  options["webdoc"])

    update_webdoc_cache(webdoc=options["webdoc"],
                        mode=options["mode"],
                        verbose=options["verbose"],
                        languages=options["language"])

if __name__ == "__main__":
    main()