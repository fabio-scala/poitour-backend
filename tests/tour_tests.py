"""
Unit tests for structures.tour

:Author: Fabio Scala <fabio.scala@gmail.com>
"""
import unittest

from app.structures import tour
from tests.base import AppTestCase, requires_db
import json


# Zuerich HB
TEST_POINT = tour.Point.from_string('47.378058,8.5398226')


class PointTestCase(AppTestCase):

    def test_from_string(self):
        p = tour.Point.from_string('47.123,8.345')
        assert p.x == 8.345, 'Correct x coordinate'
        assert p.y == 47.123, 'Correct y coordinate'

    def test_point(self):
        p = tour.Point([8.345, 47.123], id='myId')
        assert p.x == 8.345, 'Correct x coordinate'
        assert p.y == 47.123, 'Correct y coordinate'

    def test_jsonable(self):
        p = tour.Point([1, 2], id='myId')
        result = json.loads(json.dumps(p.to_jsonable()))
        test_with = {'id': 'myId', 'properties': {}, 'type': 'Feature'}
        self.assertDictContainsSubset(test_with, result, 'Is a geojson feature')
        self.assertListEqual(result['geometry']['coordinates'], [1, 2], 'Correct coordinates')


class TourTestCase(AppTestCase):

    def setUp(self):
        super(TourTestCase, self).setUp()
        self.points = [
            tour.Point([1, 2]),
            tour.Point([3, 4]),
            tour.Point([5, 6]),
        ]

    def test_from_points(self):
        r = tour.Tour.from_points(self.points[0], self.points[0], 1000, 20, self.points)
        self.assertIsInstance(r, tour.Tour)

    @requires_db
    def test_from_categories(self):
        r = tour.Tour.from_categories(TEST_POINT, TEST_POINT, 1000, 20, ['attraction'], [5])
        self.assertIsInstance(r, tour.Tour)

    @requires_db
    def test_calculate(self):
        r = tour.Tour.from_categories(TEST_POINT, TEST_POINT, 3600, 60, ['attraction'], [5])
        rr = r.calculate()
        self.assertIsInstance(rr, tour.TourResult)


class TourResultTestCase(AppTestCase):

    @requires_db
    def test_jsonable(self):
        r = tour.Tour.from_categories(TEST_POINT, TEST_POINT, 3600, 60, ['attraction'], [5])
        rr = r.calculate()
        result = json.loads(json.dumps(rr.to_jsonable()))
        [self.assertIn(key, result) for key in ('time_s', 'distance_m', 'points', 'path')]


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
