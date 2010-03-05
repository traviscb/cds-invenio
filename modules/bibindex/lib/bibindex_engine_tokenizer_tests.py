#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""bibindex_engine_tokenizer_tests - unit tests for bibindex_engine_tokenizer

There should always be at least one test class for each class in b_e_t.
"""

import unittest

from invenio.testutils import make_test_suite, run_test_suite

import bibindex_engine_tokenizer as tokenizer_lib


class TestBibIndexTokenizer(unittest.TestCase):
    """Test BibIndexTokenizer functionality."""

    def setUp(self):
        self.tokenizer = tokenizer_lib.BibIndexTokenizer()

    def test_bit_scan_space_delimited(self):
        """BibIndexTokenizer - scanning space-delimited string"""
        teststr  = "The quick brown fox jumped over the lazy dogs."
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['token_list'],
                       'token_list': ['The', 'quick', 'brown', 'fox', 'jumped', 'over', 'the', 'lazy', 'dogs.']}
        self.assertEqual(output, anticipated)

    def test_bit_scan_nospace_delimited(self):
        """BibIndexTokenizer - scanning non-spaced string"""
        teststr = "FinestGoldenTippyOrangePekoe"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['token_list'],
                       'token_list': ['FinestGoldenTippyOrangePekoe']}
        self.assertEqual(output, anticipated)

    def test_bit_tokens_space_delimited(self):
        """BibIndexTokenizer - tokens for space-delimited string"""
        teststr  = "The quick brown fox jumped over the lazy dogs."
        output = self.tokenizer._get_index_tokens(self.tokenizer._scan_and_tag(teststr))
        anticipated = ['The', 'quick', 'brown', 'fox', 'jumped', 'over', 'the', 'lazy', 'dogs.']
        self.assertEqual(output, anticipated)

    def test_bit_tokens_nospace_delimited(self):
        """BibIndexTokenizer - tokens for non-spaced string"""
        teststr = "FinestGoldenTippyOrangePekoe"
        output = self.tokenizer._get_index_tokens(self.tokenizer._scan_and_tag(teststr))
        anticipated = ['FinestGoldenTippyOrangePekoe']
        self.assertEqual(output, anticipated)


class TestFuzzyNameTokenizerScanning(unittest.TestCase):
    """Test BibIndex name tokenization"""

    def setUp(self):
        self.tokenizer = tokenizer_lib.BibIndexFuzzyNameTokenizer()

    def test_bifnt_scan_single(self):
        """BibIndexFuzzyNameTokenizer - scanning single names like 'Ronaldo'"""
        teststr = "Ronaldo"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'], 'lastnames': ['Ronaldo'], 'nonlastnames': [], 'titles': []}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_simple_western_forward(self):
        """BibIndexFuzzyNameTokenizer - scanning simple Western-style: first last"""
        teststr = "Ringo Starr"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'], 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': []}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_simple_western_reverse(self):
        """BibIndexFuzzyNameTokenizer - scanning simple Western-style: last, first"""
        teststr = "Starr, Ringo"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'], 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': []}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_multiname_forward(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: first middle last"""
        teststr = "Michael Edward Peskin"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                       'lastnames': ['Peskin'], 'nonlastnames': ['Michael', 'Edward'], 'titles': []}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_compound_lastname_reverse(self):
        """BibIndexFuzzyNameTokenizer - scanning compound last: last last, first"""
        teststr = "Alvarez Gaume, Joachim"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                       'lastnames': ['Alvarez', 'Gaume'], 'nonlastnames': ['Joachim'], 'titles': []}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_titled(self):
        """BibIndexFuzzyNameTokenizer - scanning title-bearing: last, first, title"""
        teststr = "Epstein, Brian, The Fifth Beatle"
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                       'lastnames': ['Epstein'], 'nonlastnames': ['Brian'], 'titles': ['The Fifth Beatle']}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_wildly_interesting(self):
        """BibIndexFuzzyNameTokenizer - scanning last last last, first first, title, title"""
        teststr = "Ibanez y Gracia, Maria Luisa, II., ed."
        output = self.tokenizer._scan_and_tag(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                       'lastnames': ['Ibanez', 'y', 'Gracia'], 'nonlastnames': ['Maria', 'Luisa'], 'titles': ['II.', 'ed.']}
        self.assertEqual(output, anticipated)


class TestFuzzyNameTokenizerTokens(unittest.TestCase):
    """Test BibIndex name variant token generation from scanned and tagged sets"""

    def setUp(self):
        self.tokenizer = tokenizer_lib.BibIndexFuzzyNameTokenizer()
        self.get_index_tokens = self.tokenizer._get_index_tokens

    def test_bifnt_tokenize_single(self):
        """BibIndexFuzzyNameTokenizer - tokens for single-word name

        Ronaldo
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Ronaldo'], 'nonlastnames': [], 'titles': []}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['Ronaldo']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_simple_forward(self):
        """BibIndexFuzzyNameTokenizer - tokens for first last

        Ringo Starr
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': []}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['R Starr', 'R. Starr', 'Ringo Starr', 'Starr, R', 'Starr, R.', 'Starr, Ringo']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_simple_reverse(self):
        """BibIndexFuzzyNameTokenizer - tokens for last, first

        Starr, Ringo
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': []}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['R Starr', 'R. Starr', 'Ringo Starr', 'Starr, R', 'Starr, R.', 'Starr, Ringo']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_twoname_forward(self):
        """BibIndexFuzzyNameTokenizer - tokens for first middle last

        Michael Edward Peskin
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Peskin'], 'nonlastnames': ['Michael', 'Edward'], 'titles': []}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['E Peskin', 'E. Peskin', 'Edward Peskin', 'M E Peskin', 'M E. Peskin', 'M Edward Peskin',
                       'M Peskin', 'M. E Peskin', 'M. E. Peskin', 'M. Edward Peskin', 'M. Peskin', 'M.E. Peskin',
                       'Michael E Peskin', 'Michael E. Peskin', 'Michael Edward Peskin', 'Michael Peskin', 'Peskin, E',
                       'Peskin, E.', 'Peskin, Edward', 'Peskin, M', 'Peskin, M E', 'Peskin, M E.', 'Peskin, M Edward',
                       'Peskin, M.', 'Peskin, M. E', 'Peskin, M. E.', 'Peskin, M. Edward', 'Peskin, M.E.',
                       'Peskin, Michael', 'Peskin, Michael E', 'Peskin, Michael E.', 'Peskin, Michael Edward']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_compound_last(self):
        """BibIndexFuzzyNameTokenizer - tokens for last last, first

        Alvarez Gaume, Joachim
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Alvarez', 'Gaume'], 'nonlastnames': ['Joachim'], 'titles': []}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['Alvarez Gaume, J', 'Alvarez Gaume, J.', 'Alvarez Gaume, Joachim', 'Alvarez, J', 'Alvarez, J.',
                       'Alvarez, Joachim', 'Gaume, J', 'Gaume, J.', 'Gaume, Joachim', 'J Alvarez', 'J Alvarez Gaume',
                       'J Gaume', 'J. Alvarez', 'J. Alvarez Gaume', 'J. Gaume', 'Joachim Alvarez',
                       'Joachim Alvarez Gaume', 'Joachim Gaume']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_titled(self):
        """BibIndexFuzzyNameTokenizer - tokens for last, first, title

        Epstein, Brian, The Fifth Beatle
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Epstein'], 'nonlastnames': ['Brian'], 'titles': ['The Fifth Beatle']}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['B Epstein', 'B Epstein, The Fifth Beatle', 'B. Epstein', 'B. Epstein, The Fifth Beatle',
                       'Brian Epstein', 'Brian Epstein, The Fifth Beatle', 'Epstein, B', 'Epstein, B, The Fifth Beatle',
                       'Epstein, B.', 'Epstein, B., The Fifth Beatle', 'Epstein, Brian',
                       'Epstein, Brian, The Fifth Beatle']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_wildly_interesting(self):
        """BibIndexFuzzyNameTokenizer - tokens for last last last, first first, title, title

        Ibanez y Gracia, Maria Luisa, II, (ed.)
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles'],
                 'lastnames': ['Ibanez', 'y', 'Gracia'], 'nonlastnames': ['Maria', 'Luisa'], 'titles': ['II', '(ed.)']}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['Gracia, L', 'Gracia, L.', 'Gracia, Luisa', 'Gracia, M',
            'Gracia, M L', 'Gracia, M L.', 'Gracia, M Luisa', 'Gracia, M.',
            'Gracia, M. L', 'Gracia, M. L.', 'Gracia, M. Luisa', 'Gracia, M.L.',
            'Gracia, Maria', 'Gracia, Maria L', 'Gracia, Maria L.', 'Gracia, Maria Luisa',
            'Ibanez y Gracia, L', 'Ibanez y Gracia, L, (ed.)', 'Ibanez y Gracia, L, II',
            'Ibanez y Gracia, L.', 'Ibanez y Gracia, L., (ed.)',
            'Ibanez y Gracia, L., II', 'Ibanez y Gracia, Luisa', 'Ibanez y Gracia, Luisa, (ed.)',
            'Ibanez y Gracia, Luisa, II', 'Ibanez y Gracia, M',
            'Ibanez y Gracia, M L', 'Ibanez y Gracia, M L, (ed.)', 'Ibanez y Gracia, M L, II',
            'Ibanez y Gracia, M L.', 'Ibanez y Gracia, M L., (ed.)',
            'Ibanez y Gracia, M L., II', 'Ibanez y Gracia, M Luisa',
            'Ibanez y Gracia, M Luisa, (ed.)', 'Ibanez y Gracia, M Luisa, II',
            'Ibanez y Gracia, M, (ed.)', 'Ibanez y Gracia, M, II', 'Ibanez y Gracia, M.',
            'Ibanez y Gracia, M. L', 'Ibanez y Gracia, M. L, (ed.)', 'Ibanez y Gracia, M. L, II',
            'Ibanez y Gracia, M. L.', 'Ibanez y Gracia, M. L., (ed.)',
            'Ibanez y Gracia, M. L., II', 'Ibanez y Gracia, M. Luisa', 'Ibanez y Gracia, M. Luisa, (ed.)',
            'Ibanez y Gracia, M. Luisa, II', 'Ibanez y Gracia, M., (ed.)', 'Ibanez y Gracia, M., II',
            'Ibanez y Gracia, M.L.', 'Ibanez y Gracia, M.L., (ed.)', 'Ibanez y Gracia, M.L., II',
            'Ibanez y Gracia, Maria', 'Ibanez y Gracia, Maria L', 'Ibanez y Gracia, Maria L, (ed.)',
            'Ibanez y Gracia, Maria L, II', 'Ibanez y Gracia, Maria L.', 'Ibanez y Gracia, Maria L., (ed.)',
            'Ibanez y Gracia, Maria L., II', 'Ibanez y Gracia, Maria Luisa',
            'Ibanez y Gracia, Maria Luisa, (ed.)', 'Ibanez y Gracia, Maria Luisa, II',
            'Ibanez y Gracia, Maria, (ed.)', 'Ibanez y Gracia, Maria, II',
            'Ibanez, L', 'Ibanez, L.', 'Ibanez, Luisa', 'Ibanez, M', 'Ibanez, M L',
            'Ibanez, M L.', 'Ibanez, M Luisa', 'Ibanez, M.', 'Ibanez, M. L',
            'Ibanez, M. L.', 'Ibanez, M. Luisa', 'Ibanez, M.L.', 'Ibanez, Maria',
            'Ibanez, Maria L', 'Ibanez, Maria L.', 'Ibanez, Maria Luisa', 'L Gracia', 'L Ibanez',
            'L Ibanez y Gracia', 'L Ibanez y Gracia, (ed.)',
            'L Ibanez y Gracia, II', 'L. Gracia', 'L. Ibanez', 'L. Ibanez y Gracia',
            'L. Ibanez y Gracia, (ed.)', 'L. Ibanez y Gracia, II', 'Luisa Gracia', 'Luisa Ibanez',
            'Luisa Ibanez y Gracia', 'Luisa Ibanez y Gracia, (ed.)', 'Luisa Ibanez y Gracia, II',
            'M Gracia', 'M Ibanez', 'M Ibanez y Gracia', 'M Ibanez y Gracia, (ed.)',
            'M Ibanez y Gracia, II', 'M L Gracia', 'M L Ibanez', 'M L Ibanez y Gracia',
            'M L Ibanez y Gracia, (ed.)', 'M L Ibanez y Gracia, II', 'M L. Gracia',
            'M L. Ibanez', 'M L. Ibanez y Gracia', 'M L. Ibanez y Gracia, (ed.)',
            'M L. Ibanez y Gracia, II', 'M Luisa Gracia', 'M Luisa Ibanez', 'M Luisa Ibanez y Gracia',
            'M Luisa Ibanez y Gracia, (ed.)', 'M Luisa Ibanez y Gracia, II', 'M. Gracia',
            'M. Ibanez', 'M. Ibanez y Gracia', 'M. Ibanez y Gracia, (ed.)',
            'M. Ibanez y Gracia, II', 'M. L Gracia', 'M. L Ibanez', 'M. L Ibanez y Gracia',
            'M. L Ibanez y Gracia, (ed.)', 'M. L Ibanez y Gracia, II', 'M. L. Gracia',
            'M. L. Ibanez', 'M. L. Ibanez y Gracia', 'M. L. Ibanez y Gracia, (ed.)', 'M. L. Ibanez y Gracia, II',
            'M. Luisa Gracia', 'M. Luisa Ibanez', 'M. Luisa Ibanez y Gracia', 'M. Luisa Ibanez y Gracia, (ed.)',
            'M. Luisa Ibanez y Gracia, II', 'M.L. Gracia', 'M.L. Ibanez', 'M.L. Ibanez y Gracia',
            'M.L. Ibanez y Gracia, (ed.)', 'M.L. Ibanez y Gracia, II', 'Maria Gracia', 'Maria Ibanez',
            'Maria Ibanez y Gracia', 'Maria Ibanez y Gracia, (ed.)', 'Maria Ibanez y Gracia, II',
            'Maria L Gracia', 'Maria L Ibanez', 'Maria L Ibanez y Gracia', 'Maria L Ibanez y Gracia, (ed.)',
            'Maria L Ibanez y Gracia, II', 'Maria L. Gracia', 'Maria L. Ibanez', 'Maria L. Ibanez y Gracia',
            'Maria L. Ibanez y Gracia, (ed.)', 'Maria L. Ibanez y Gracia, II', 'Maria Luisa Gracia',
            'Maria Luisa Ibanez', 'Maria Luisa Ibanez y Gracia', 'Maria Luisa Ibanez y Gracia, (ed.)',
            'Maria Luisa Ibanez y Gracia, II']
        self.assertEqual(output, anticipated)

    def test_tokenize(self):
        """BibIndexFuzzyNameTokenizer - check tokenize()

        Ringo Starr
        """
        teststr = "Ringo Starr"
        output = self.tokenizer.tokenize(teststr)
        anticipated = ['R Starr', 'R. Starr', 'Ringo Starr', 'Starr, R', 'Starr, R.', 'Starr, Ringo']
        self.assertEqual(output, anticipated)


TEST_SUITE = make_test_suite(TestBibIndexTokenizer, TestFuzzyNameTokenizerScanning, TestFuzzyNameTokenizerTokens)


if __name__ == '__main__':
    #unittest.main()
    run_test_suite(TEST_SUITE)

