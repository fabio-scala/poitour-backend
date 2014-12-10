"""
Test Base

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import app
import os
import unittest
import functools
import nose

IS_TRAVIS = os.getenv('IS_TRAVIS')


def requires_db(test):
    """ Decorator for skipping tests that require EOSDMDBOne """
    @functools.wraps(test)
    def wrapper(*a, **k):
        if not IS_TRAVIS:
            return test(*a, **k)
        raise nose.SkipTest

    return wrapper


class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        app.db.session.remove()
        self.ctx.pop()


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
