"""
Unit tests for provder base module (pluggable POI provider infrastructure)

:Author: Fabio Scala <fabio.scala@gmail.com>
"""
import unittest

import os
from app import pois
from app.pois.providerbase import Category, CategoryPoint, PoiProvider, PoiLookupService
from tests.base import BaseTestCase


original_providers = PoiProvider.__metaclass__._registered


class MockProvider(PoiProvider):

    def __init__(self, config):
        super(MockProvider, self).__init__(config)
        self.config = config

    def get_categories(self):
        self.categories = [Category(self, 'test_id', 'test_name', 'test_category', 'a category for testing purposes'),
                           Category(self, 'test_id2', 'test_name2', 'test_category2', 'a category for testing purposes2')]
        return self.categories

    def get_points_for_category(self, category_obj, start, end, time_in_s, radius_m, speed_km_h):
        assert start == 0
        assert end == 1
        assert time_in_s == 60
        return [CategoryPoint(category_obj, 'my_poi', 1, 2, 'my_poi_desc')]


class ProviderTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        basedir = os.path.abspath(os.path.dirname(__file__))
        yaml_file = os.path.join(basedir, 'mock_providers_config.yaml')
        self.service = PoiLookupService(yaml_file)
        PoiProvider.__metaclass__._registered = [c for c in original_providers if c.__name__ == 'MockProvider']

    def tearDown(self):
        BaseTestCase.tearDown(self)
        # restore
        PoiProvider.__metaclass__._registered = original_providers

    def test_registration(self):
        assert PoiProvider.__metaclass__._registered[0].__name__ == 'MockProvider', 'Should auto-register POI provider'

    def test_get_categories(self):
        categories = self.service.get_categories()
        assert len(categories) == 2
        for c in categories:
            self.assertIsInstance(c, Category, 'Returns Category instances')

    def test_get_points_for_category(self):
        categories = self.service.get_categories()
        self.service.get_points_for_categories(categories, 0, 1, 60, 1000, 3.6)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
