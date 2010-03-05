#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import re

SINGLE_INITIAL_RE = re.compile('^\w\.$')
# LASTNAME_STOPWORDS describes terms which should not be used for indexing,
# in multiple-word last names.  These are purely conjunctions, serving the
# same function as the American hyphen, but using linguistic constructs.
LASTNAME_STOPWORDS = set(['y', 'of', 'and'])


class BibIndexTokenizer(object):
    """Base class for the tokenizers

    Tokenizers act as filters which turn input strings into lists of strings
    which represent the idexable components of that string.
    """

    def _scan_and_tag(self, s):
        """Return s split on spaces, drop excess whitespace.

        Every tokenizer should have a _scan_and_tag function, which scans the
        input string and lexically tags its components.  These units are
        grouped together in sequences.  The output of _scan_and_tag is usually
        something like:
        {
            'TOKEN_TAG_LIST' : a list of valid keys in this output set,
            'key1' : [val1, val2, val3] - where key describes the in some
                      meaningful way
        }

        @param s: the input to be lexically tagged
        @type s: string

        @return: dict of lexically tagged input items
            In this base-class, _scan_and_tag does nothing more than split on
            spaces.  Its output for "Assam and Darjeeling" should be:
            {
                'TOKEN_TAG_LIST' : 'token_list',
                'token_list'     : ['Assam', 'and', 'Darjeeling']
            }
        @rtype: dict
        """
        retval = {'TOKEN_TAG_LIST': ['token_list'], 'token_list': []}
        retval['token_list'] = s.strip().split(' ')
        return retval

    def _get_index_tokens(self, t):
        """Return token list from tagged token dictionary t.

        Normally this would do interesting computation over the output of
        _scan_and_tag(); this base class is trivial, however.

        @param t: a dictionary with a 'token_list' key
        @type t: dict

        @return: the token items from 'token_list'
        @rtype: list of string
        """
        return t['token_list']

    def tokenize(self, s):
        """Return token list from input string s.

        Simply combines the functionality of the above.

        @param s: the input to be lexically tagged
        @type s: string

        @return: the token items derived from s
        @rtype: list of string
        """
        return self._get_index_tokens(self._scan_and_tag(s))

class BibIndexFuzzyNameTokenizer(object):
    """Human name tokenizer.

    Human names are divided into three classes of tokens:
    'lastnames', i.e., family, tribal or group identifiers,
    'nonlastnames', i.e., personal names distinguishing individuals,
    'titles', both incidental and permanent, e.g., 'VIII', '(ed.)', 'Msc'
    """

    def _scan_and_tag(self, s):
        """Return the token dictionary for a name string.

        @param s: the input to be lexically tagged
        @type s: string

        @return: dict of lexically tagged input items.

            Sample output for the name 'Jingleheimer Schmitt, John Jacob, XVI.' is:
            {
                'TOKEN_TAG_LIST' : ['lastnames', 'nonlastnames', 'titles'],
                'lastnames'      : ['Jingleheimer', 'Schmitt'],
                'nonlastnames'   : ['John', 'Jacob'],
                'titles'         : ['XVI.']
            }
        @rtype: dict
        """
        retval = {'TOKEN_TAG_LIST' : ['lastnames', 'nonlastnames', 'titles'],
                  'lastnames'      : [],
                  'nonlastnames'   : [],
                  'titles'         : []}
        l = s.split(',')
        if len(l) < 2:
            # No commas means a simple name
            new = s.strip()
            new = s.split(' ')
            if len(new) == 1:
                retval['lastnames'] = new        # rare single-name case
            else:
                retval['lastnames'] = new[-1:]
                retval['nonlastnames'] = new[:-1]
        else:
            # Handle lastname-first multiple-names case
            retval['titles'] = l[2:]             # no titles? no problem
            retval['nonlastnames'] = l[1]
            retval['lastnames'] = l[0]
            for tag in ['lastnames', 'nonlastnames']:
                retval[tag] = retval[tag].strip()
                retval[tag] = retval[tag].split(' ')
                    # filter empty strings
                retval[tag] = [x for x in retval[tag] if x != '']
            retval['titles'] = [x.strip() for x in retval['titles'] if x != '']

        return retval

    def _get_index_tokens(self, tokdict):
        """Return all the indexable variations for a tagged token dictionary.

	    Does this via the combinatoric expansion of the following rules:
	    - Expands first names as name, first initial with period, first initial
            without period.
	    - Expands compound last names as each of their non-stopword subparts.
	    - Titles are treated literally, but applied serially.

	    Please note that titles will be applied to complete last names only.
	    So for example, if there is a compound last name of the form,
	    "Ibanez y Gracia", with the title, "(ed.)", then only the combination
	    of those two strings will do, not "Ibanez" and not "Gracia".

        @param tokdict: lexically tagged input items in the form of the output
            from _scan_and_tag()
        @type tokdict: dict

        @return: combinatorically expanded list of strings for indexing
        @rtype: list of string
        """

        def _fully_expanded_last_name(first, lastlist, title = None):
            """Return a list of all of the first / last / title combinations.

            @param first: one possible non-last name
            @type first: string

            @param lastlist: the strings of the tokens in the (possibly compound) last name
            @type lastlist: list of string

            @param title: one possible title
            @type title: string
            """
            retval = []
            title_word = ''
            if title != None:
                title_word = ', ' + title

            last = ' '.join(lastlist)
            retval.append(first + ' ' + last + title_word)
            retval.append(last + ', ' + first + title_word)
            for last in lastlist:
                if last in LASTNAME_STOPWORDS:
                    continue
                retval.append(first + ' ' + last + title_word)
                retval.append(last + ', ' + first + title_word)

            return retval

        last_parts = tokdict['lastnames']
        first_parts = tokdict['nonlastnames']
        titles = tokdict['titles']

        if len(first_parts) == 0:                       # rare single-name case
            return tokdict['lastnames']

        expanded = []
        for exp in self.__expand_nonlastnames(first_parts):
            expanded.extend(_fully_expanded_last_name(exp, last_parts, None))
            for title in titles:
                # XXX: remember to document that titles can only be applied to complete last names
                expanded.extend(_fully_expanded_last_name(exp, [' '.join(last_parts)], title))

        return sorted(list(set(expanded)))

    def __expand_nonlastnames(self, namelist):
        """Generate every expansion of a series of human non-last names.

        Example:
        "Michael Edward" -> "Michael Edward", "Michael E.", "Michael E", "M. Edward", "M Edward",
                            "M. E.", "M. E", "M E.", "M E", "M.E."
                    ...but never:
                    "ME"

        @param namelist: a collection of names
        @type namelist: list of string

        @return: a greatly expanded collection of names
        @rtype: list of string
        """

        def _expand_name(name):
            """Lists [name, dotted initial, initial, empty]"""
            if name == None:
                return []
            return [name, name[0] + '.', name[0] + '']

        def _pair_items(head, tail):
            """Lists every combination of head with each and all of tail"""
            if len(tail) == 0:
                return [head]
            l = []
            l.extend([head + ' ' + tail[0]])
            l.extend(_pair_items(head, tail[1:]))
            return l

        def _collect(head, tail):
            """Brings together combinations of things"""
            if len(tail) == 0:
                return [head]
            l = []
            l.extend(_pair_items(head, _expand_name(tail[0])))
            l.extend(_collect(head, tail[1:]))
            return l

        def _expand_contract(namelist):
            """Runs collect with every head in namelist and its tail"""
            val = []
            for i  in range(len(namelist)):
                name = namelist[i]
                for expansion in _expand_name(name):
                    val.extend(_collect(expansion, namelist[i+1:]))
            return val

        def _add_squashed(namelist):
            """Finds cases like 'M. E.' and adds 'M.E.'"""
            val = namelist

            def __check_parts(parts):
                if len(parts) < 2:
                    return False
                for part in parts:
                    if not SINGLE_INITIAL_RE.match(part):
                        return False
                return True

            for name in namelist:
                parts = name.split(' ')
                if not __check_parts(parts):
                    continue
                val.extend([''.join(parts)])

            return val

        return _add_squashed(_expand_contract(namelist))

    def tokenize(self, s):
        """Given a string, output a list of strings expanding it.

	    Does this via the combinatoric expansion of the following rules:
	    - Expands first names as name, first initial with period, first initial
            without period.
	    - Expands compound last names as each of their non-stopword subparts.
	    - Titles are treated literally, but applied serially.

	    Please note that titles will be applied to complete last names only.
	    So for example, if there is a compound last name of the form,
	    "Ibanez y Gracia", with the title, "(ed.)", then only the combination
	    of those two strings will do, not "Ibanez" and not "Gracia".

        @param s: the input to be lexically tagged
        @type s: string

        @return: combinatorically expanded list of strings for indexing
        @rtype: list of string

        @note: A simple wrapper around _scan_and_tag and _get_index_tokens.
        """
        return self._get_index_tokens(self._scan_and_tag(s))


if __name__ == "__main__":
    """Trivial manual test framework"""
    import sys
    args = sys.argv[1:]

    test_str = ''
    if len(args) == 0:
        test_str = "Michael Peskin"
    elif len(args) == 1:
        test_str = args[0]
    else:
        test_str = ' '.join(args)

    tokenizer = BibIndexFuzzyNameTokenizer()
    print "Tokenizes as:", tokenizer.tokenize(test_str)

