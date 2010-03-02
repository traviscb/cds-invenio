#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import unittest
import sys

import names


class TestNames(unittest.TestCase):
    """Test the perverse names under various conditions."""

    def setUp(self):
        self.tests = {
          'Madonna':                 ([(None,), ('Madonna',)],
                                      ['Madonna']),
          'Michael Peskin':          ([('Michael',), ('Peskin',)],
                                      ['Michael Peskin', 'M. Peskin', 'M Peskin',
                                       'Peskin, Michael', 'Peskin, M.', 'Peskin, M']),
          'Peskin, Michael':         ([('Michael',), ('Peskin',)],                
                                      ['Michael Peskin', 'M. Peskin', 'M Peskin',
                                       'Peskin, Michael', 'Peskin, M.', 'Peskin, M']),
          'Michael Edward Peskin':   ([('Michael', 'Edward'), ('Peskin',)],       
                                      ['Michael Edward Peskin', 'Michael Peskin', 'Edward Peskin', 
                                       'M Edward Peskin', 'M. Edward Peskin', 'Michael E. Peskin', 'Peskin, M. E',
                                       'Michael E Peskin', 'M.E. Peskin', 'M. E. Peskin', 'M E Peskin', 
                                       'Peskin, Michael Edward', 'Peskin, Michael', 'Peskin, Edward', 
                                       'Peskin, M Edward', 'Peskin, M. Edward', 'Peskin, Michael E.', 'M. E Peskin',
                                       'Peskin, Michael E', 'Peskin, M.E.', 'Peskin, M. E.', 'Peskin, M E',
                                       'E. Peskin', 'E Peskin', 'Peskin, E.', 'Peskin, E', 'M E. Peskin',
                                       'Peskin, M E.', 'M. Peskin', 'M Peskin', 'Peskin, M.', 'Peskin, M']),
          'Alvarez Gaume, Joachim':  ([('Joachim',), ('Alvarez', 'Gaume')],       
                                      ['Joachim Alvarez Gaume', 'Joachim Alvarez', 'Joachim Gaume',
                                       'J. Alvarez Gaume', 'J Alvarez Gaume', 'J. Alvarez', 'J Alvarez',
                                       'J. Gaume', 'J Gaume', 'Alvarez Gaume, Joachim', 'Alvarez, Joachim', 
                                       'Gaume, Joachim', 'Alvarez Gaume, J.', 'Alvarez Gaume, J', 'Alvarez, J.', 
                                       'Alvarez, J', 'Gaume, J.', 'Gaume, J']),
          'Thorn, Charles B., III.': ([('Charles', 'B.'), ('Thorn',), ('III.',)], 
                                      ['Charles B. Thorn, III.', 'Charles B Thorn, III.', 'Charles Thorn, III.',  
                                       'C. B. Thorn, III.', 'C B Thorn, III.',  'C.B. Thorn, III.', 'C Thorn, III.', 
                                       'Charles B. Thorn', 'Charles B Thorn', 'Charles Thorn', 'C. Thorn', 
                                       'C B. Thorn', 'C. B Thorn', 'Thorn, B', 'Thorn, B.', 'Thorn, C B.', 
                                       'Thorn, C. B', 'Thorn, C.', 'Thorn, C', 'Thorn, C B', 'Thorn, C. B.', 
                                       'Thorn, Charles', 'Thorn, Charles B.', 'Thorn, Charles B', 'Thorn, C.B.', 
                                       'C Thorn', 'C. B. Thorn', 'C B Thorn', 'C.B. Thorn', 'B Thorn', 'B. Thorn', 
                                       'B Thorn, III.',  'C B. Thorn, III.', 'C. B Thorn, III.', 'C. Thorn, III.', 
                                       'Thorn, B, III.', 'Thorn, B., III.', 'Thorn, C B, III.', 'Thorn, C B., III.', 
                                       'Thorn, C. B., III.', 'Thorn, C, III.', 'B. Thorn, III.', 
                                       'Thorn, C. B, III.', 'Thorn, C., III.', 'Thorn, C.B., III.', 
                                       'Thorn, Charles B, III.', 'Thorn, Charles B., III.', 'Thorn, Charles, III.',
                                       ]),
        }

        self.tokenize = names.tokenize
        self.variants = names.variants

    def testTokenizing(self):
        """Tokenization tests"""
        for name in self.tests:
            under_test = self.tokenize(name)
            expected = self.tests[name][0]
            sys.stdout.write("Testing: '%s' -> %s... " % (name, self.tests[name][0]))
            self.assertEqual(under_test, expected)
            sys.stdout.write("OK\n")

    def testVariantGeneration(self):
        """Variant generation tests"""
        for name in self.tests:
            under_test = self.variants(self.tests[name][0])
            expected = self.tests[name][1]
            sys.stdout.write("Testing: '%s' Expansion... " % (name))
            self.assertEqual(set(under_test), set(expected))
            sys.stdout.write("OK\n")


if __name__ == '__main__':
    unittest.main()
