#! /usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from nws_wwa import (
    get_all,
    get_hazards,
    get_warnings
)


class GeomacWildfiresUnitTest(unittest.TestCase):

    def test_all(self):
        get_all()

    def test_hazards(self):
        get_hazards()

    def test_warnings(self):
        get_warnings()


if __name__ == '__main__':
    unittest.main()
