#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import re

SINGLE_INITIAL_RE = re.compile('^\w\.$')


def tokenize(s):
    """Return the list of tokens in a name string.

    Returns list in form:
    [ (non-lastname names tuple),
      (lastname names tuple),
      (titles tuple)
    ]

    Ex:
    'Michael Peskin' -> ['Michael', 'Peskin']
    'Ibañez y Gracía, Maria Luisa, II., ed.
        [('Maria', 'Luisa'), ('Ibanez' 'y' 'Gracia'), ('II.', 'ed.')]

    NB: Multiple words before a comma will be considered a 'compound last name', 
    and kept together.
    """
    l = s.split(',')
    if len(l) < 2:
        # No commas means a simple name
        new = s.split(' ')
        if len(new) == 1:
            return [ (None,), (new[-1],) ] 
        else:
            return [ tuple(new[:-1]), (new[-1],) ] 
    elif len(l) > 2:
        # We have one or more titles
        titles = ' '.join(l[2:])
        l = [l[0], l[1]]
        l.append(titles)
    # Handle multiple names case
    new = l[1:]
    new.insert(1, l[0])
    new = [x.strip() for x in new]
    new = [x.split(' ') for x in new]
    new = [[x for x in y if x != ''] for y in new]    # filter empty strings
    new = [tuple(x) for x in new]
    return new

def variants(toks):
    """Return all the indexable variations on a token stream.

    This can be very many.
    """
    titles = []
    nonlast = toks[0]
    if len(toks) > 2:
        titles = list(toks[2])
        titles.append(', '.join(titles))

    expanded = []

    if nonlast[0] == None:                       # rare single-name case
        expanded = list(toks[1])

    for exp in _expand_nonlastnames(nonlast):
        lastname_parts = toks[1]
        if len(titles) > 0:
            for title in titles:
                if len(lastname_parts) > 1:
                    for lastname in lastname_parts:
                        expanded.append(exp + ' ' + lastname + ', ' + title)
                        expanded.append(lastname + ', ' + exp + ', ' + title)
                lastname = ' '.join(lastname_parts)
                expanded.append(exp + ' ' + lastname + ', ' + title)
                expanded.append(lastname + ', ' + exp + ', ' + title)

        if len(lastname_parts) > 1:
            for lastname in lastname_parts:
                expanded.append(exp + ' ' + lastname)
                expanded.append(lastname + ', ' + exp)
        lastname = ' '.join(lastname_parts)
        expanded.append(exp + ' ' + lastname)
        expanded.append(lastname + ', ' + exp)

    return sorted(list(set(expanded)))

def _expand_nonlastnames(toklist):
    """Generate every expansion of a series of non-last human names.

    Examples:
    "Michael Edward" -> "Michael Edward", "Michael E.", "Michael E", "M. Edward", "M Edward",
                        "M. E.", "M. E", "M E.", "M E", "M.E."
                ...but never:
                "ME"
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

    return _add_squashed(_expand_contract(toklist))


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    test_str = ''
    if len(args) == 0:
        test_str = "Michael Peskin"
    elif len(args) == 1:
        test_str = args[0]
    else:
        test_str = ' '.join(args)

    print "Tokenizes as:", tokenize(test_str)

