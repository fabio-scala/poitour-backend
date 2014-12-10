"""
Helper classes for dealing with tours and tour calculation

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

from flask import current_app as app
import geojson
import numpy
import shapely.geometry

from app import osrm, basedir
from app.routing import stsp
from app.utils import polyline


class Point(shapely.geometry.Point):

    """ Subclass of shapely.point with support for GeoJSON serialization with properties
    """

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id', None)
        super(Point, self).__init__(*args, **kwargs)

    @classmethod
    def from_string(cls, string, **kw):
        """ Returns an instance of Point given a string representation of a point

        :param string: Latitude and longitude (e.g. 47.123,8.345)
        :param *kw: Additional parameters passed to the constructor
        :rtype: Point
        """
        return cls(map(float, string.split(',')[1::-1]), **kw)

    def __str__(self):
        """ Returns a string representation of the point as lat,lon
        """
        return '{},{}'.format(self.x, self.x)

    def get_properties(self):
        """ To be overridden in subclass which has specific properties
        """
        return {}

    def to_jsonable(self):
        """ Returns a json-serializable python object
        """
        return geojson.Feature(id=self.id, geometry=geojson.Point([self.x, self.y]), properties=self.get_properties())


class TourResult(object):

    """ Represents the result of a tour calculation

    :param time: Total travel time in seconds
    :param distance: Total travel distance in meters
    :param points: Ordered points that are visited
    :type points: list of Point
    :param path: List of coordinates representing the polyline (path)
    :type path: list of list([lon, lat])
    :param total_time: Total time of the tour in seconds including stops (stay_time)
    :type total_time: int
    """

    def __init__(self, time, distance, points, path, total_time):
        self.time = time
        self.distance = distance
        self.points = points
        self.path = path
        self.total_time = total_time

    @classmethod
    def from_osrm_route(cls, points, route, total_time):
        """ Creates a TourResult instance from an OSRM viaroute result dictionary
        :param point: List of Point objects that are visited
        :param route: Deserialized OSRM viaroute result
        :param total_time: Total time of the route in seconds including stops (stay_time)
        :type total_time: int
        """
        # flip lat,lon -> lon,lat & decode
        path = numpy.fliplr(polyline.decode_line(route['route_geometry'])).tolist()
        route_summary = route['route_summary']
        return cls(route_summary['total_time'], route_summary['total_distance'], points, path, total_time)

    def to_jsonable(self):
        """ Returns a json serializable python object
        """
        return {
            'time_s': self.time,
            'time_total_s': self.total_time,
            'distance_m': self.distance,
            'points': geojson.FeatureCollection([p.to_jsonable() for p in self.points]),
            'path': geojson.LineString(self.path),
        }


class Tour(object):

    """ Helper class for calculating a tour result from given input parameters
    """

    def __init__(self, start, end, time, stay_time, points, osrm_correction_factor=None, weights=None):
        self.start = start
        self.end = end
        self.time = time
        self.stay_time = stay_time
        self.points = points
        self.weights = weights
        self.osrm_correction_factor = osrm_correction_factor

    def calculate(self):
        """ Calculates a possible tour and returns a TourResult object
        """
        if not self.points:
            osrm_route = osrm.viaroute([[self.start.y, self.start.x], [self.end.y, self.end.x]], z=0)
            return TourResult.from_osrm_route([self.start, self.end], osrm_route, 0)

        end_ix = int(not self.start.equals(self.end))
        all_points = [self.start] + end_ix * [self.end] + self.points
        weights = numpy.array([0] * (end_ix + 1) + self.weights) if self.weights else None

        osrm_points = [[p.y, p.x] for p in all_points]

        distances = numpy.array(osrm.distance_matrix(osrm_points), dtype=float)
        distances /= 10  # convert to seconds

        # check factor first, we don't want to waste precious time ;-)
        if self.osrm_correction_factor and self.osrm_correction_factor != 1:
            distances *= self.osrm_correction_factor

        # add stay_time as penalty except from/to start/end points (obviously we don't need to wait
        # before starting)
        # distances[end_ix + 1:, end_ix + 1:] += self.stay_time

        # penalty for all except start->anything (oterhwise we would get a tour with stay_time > time)
        distances[1:] += self.stay_time

        ga = stsp.GaSolver(
            start=0, end=end_ix, distances=distances, max_cost=self.time, profits=weights,
            population_size=app.config['APP_GA_POPULATION_SIZE'],
            tournament_size=app.config['APP_GA_TOURNAMENT_SIZE'],
            min_generations=app.config['APP_GA_MIN_GENERATIONS'],
            max_generations=app.config['APP_GA_MAX_GENERATIONS'],
            termination_threshold=app.config['APP_GA_TERMINATION_THRESHOLD'],
            max_runtime=app.config['APP_GA_MAX_RUNTIME_MS']
        )

        path, cost = ga.calc_tour()
        points_tour = numpy.take(numpy.array(all_points, dtype=object), path)

        # no tour found within those constraints, just route from A to B
        points_viaroute = points_tour if len(points_tour) else [all_points[0], all_points[end_ix]]

        # zoom level = 0 prevents from getting stuck if no OSRM route is found
        osrm_route = osrm.viaroute([[p.y, p.x] for p in points_viaroute], z=0)

        # TODO: when OSRM viaroute() and table() use the same algorithm (currently they don't) use this to calculate the total time:
        # self.time + max(0, len(self.points) - 2) * self.stay_time
        total_time = int(cost)
        return TourResult.from_osrm_route(points_tour, osrm_route, total_time)

    @classmethod
    def from_points(cls, start, end, time, stay_time, points):
        """ Factory given single points to be visited (e.g. from API)
        """
        return cls(start, end, time, stay_time, points)

    @classmethod
    def from_categories(cls, start, end, time, stay_time, category_names, weights):
        """ Factory method given category id's to be visited (e.g. from Webapp)
        """
        # xxx
        from app import pois
        categories = [pois.by_id(c) for c in category_names]
        weights_by_category = dict(zip(category_names, weights))
        speed_km_h = app.config['APP_WALKING_SPEED_KM_H']
        radius_m = time * (speed_km_h / 3.6)
        points = pois.get_points_for_categories(categories, start, end, time, radius_m=radius_m, speed_km_h=speed_km_h)
        # equal weights -> no weights
        weights_for_points = [weights_by_category[p.category.id] for p in points] if len(set(weights)) > 1 else None
        return cls(start, end, time, stay_time, points, weights=weights_for_points)
