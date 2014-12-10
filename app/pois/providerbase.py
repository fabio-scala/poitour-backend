"""
Category provider infrastructure / base classes for pluggable category providers

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import itertools
import operator
import os
import sys

import shapely.geometry
import yaml

from app.structures import tour


class Category(object):

    """ Represents a POI category shown in the front end.

    :param belongs_to: CategoryProvider instance it belongs to. Required in order to request concrete points for this category
    :type  belongs_to: CategoryProvider

    :param id: Unique identifier for this category. Is also used for communication between server and client.
    :type  id: str

    :param name: Name of the category. Not currently used but might be some time in the future.
    :type name: str

    :param display_name: Name of the category like it is displayed in the client. Usually the name of the category in plural.
    :type display_name: str

    :param description: A description for this category. Also not currently used, but might be in there future.
    :type description: str
    """

    def __init__(self, belongs_to, id, name, display_name, description):
        self.belongs_to = belongs_to
        self.id = id
        self.name = name
        self.display_name = display_name
        self.description = description


class CategoryPoint(tour.Point):

    """ Represents a concrete point which belongs to a POI category.
    """

    def __init__(self, category, name, lon, lat, url=None, description=''):
        super(CategoryPoint, self).__init__([lon, lat])
        self.category = category
        self.name = name
        self.lon = lon
        self.lat = lat
        self.url = url
        self.description = description

    def get_url(self):
        return self.url

    def get_properties(self):
        return {'name': self.name, 'description': self.description, 'url': self.get_url()}


class _ProviderMeta(type):

    """ Metaclass is used for automagical registration of POI providers (plugins) as soon as the subclass CategoryProvider
    """

    _registered = []

    def __init__(C, name, t, d):
        type.__init__(C, name, t, d)
        if C.__module__ != globals()['__name__']:
            C.__metaclass__._registered.append(C)

    @classmethod
    def get_providers(cls):
        """ Returns the currently registered providers classes
        :rtype: list
        """
        return cls._registered


class PoiLookupService(object):

    """ Service class / helper for fetching categories and points from the available/registered providers

    :param yaml_path: Absolute or relative path to provider configuration YAML file
    :type  yaml_path: str
    """

    def __init__(self, yaml_path=None):
        self.set_config_path(yaml_path)
        self.providers = {}
        self.categories = {}

    def set_config_path(self, yaml_path):
        if not yaml_path:
            root_dir = os.path.realpath(os.path.dirname(sys.argv[0]))
            yaml_path = os.path.join(root_dir, 'providers_config.yaml')

        self.yaml_path = yaml_path

    def _init_providers(self):
        """ Instantiate providers with the corresponding configurations from the YAML file
        """
        if not self.providers:
            with open(self.yaml_path, 'r') as f:
                config = yaml.load(f)

            for provider_class in PoiProvider.__metaclass__.get_providers():
                self.providers[provider_class.__name__] = provider_class(config.get(provider_class.__name__))

    def _init_categories(self):
        """ Fetch all categories form the instantiated providers
        """
        self._init_providers()
        if not self.categories:
            self.categories = {c.id: c for p in self.providers.values() for c in p.get_categories()}

    def get_categories(self):
        """ Returns all registered and available categories
        :rtype: list of Category
        """
        self._init_categories()
        return self.categories.values()

    def by_id(self, id):
        """ Retrieve a category object by its unique id
        :param id: Unique category identifier
        :type id: str
        """
        self._init_categories()
        return self.categories[id]

    def get_points_for_categories(self, categories, start, end, time_s, radius_m, speed_km_h):
        """ Returns all possible points for the given categories and constraints (parameters)
        :param categories: A list of categories to retrieve the points for
        :type categories: list of Category

        :param start: Start point of the tour
        :type start: shapely.geometry.Point

        :param end: End point of the tour. Not currently used by any built-in providers but might be in the future.
        :type end: shapely.geometry.Point

        :param time_s: Desired travel time in seconds
        :param time_s: int

        :param radius_m: Which radius from start to search points
        :type radius_m: float

        :param speed_km_h: Desired walking speed of the tour
        :type speed_km_h: float

        """
        points = []
        for provider, group in itertools.groupby(categories, operator.attrgetter('belongs_to')):
            points += provider.get_points_for_categories(list(group), start, end, time_s, radius_m, speed_km_h)
        return points


class PoiProvider(object):

    """ Abstract parent class for custom POI (category) providers.

    :param config: Configuration for the provider
    :type config: dict
    """

    __metaclass__ = _ProviderMeta

    def __init__(self, config):
        self.config = config

    def get_categories(self):
        """ Returns the categories provided by this provider
        :rtype: list of Category
        """
        raise NotImplementedError

    def get_points_for_category(self, category, start, end, time_s, radius_m, speed_km_h):
        """ Returns all possible points for the given category and constraints.
        :param categoriy: Category to retrieve points for
        :type categories: Category

        :param start: Start point of the tour
        :type start: shapely.geometry.Point

        :param end: End point of the tour. Not currently used by any built-in providers but might be in the future.
        :type end: shapely.geometry.Point

        :param time_s: Desired travel time in seconds
        :param time_s: int
        """
        raise NotImplementedError

    def get_points_for_categories(self, categories, start, end, time_s, radius_m, speed_km_h):
        """ Returns all possible points for the given categories and constraints (parameters).

        :note: This should only be overridden it's possible to fetch multiple categories faster than individually. Otherwise the indivdidual
            fetching is handled by this (parent) class.

        :param categories: A list of categories to retrieve the points for
        :type categories: list of Category

        :param start: Start point of the tour
        :type start: shapely.geometry.Point

        :param end: End point of the tour. Not currently used by any built-in providers but might be in the future.
        :type end: shapely.geometry.Point

        :param time_s: Desired travel time in seconds
        :param time_s: int
        """
        return [p for c in categories for p in self.get_points_for_category(c, start, end, time_s, radius_m, speed_km_h)]


if __name__ == '__main__':
    import app
    appl = app.create_app('default')
    appl.app_context().push()

    cs = PoiLookupService('C:/Users/root/git/poinavi/provider_config.yaml')
    ca = cs.get_categories()
    pr = cs.providers.values()[0]
    points = pr.get_points_for_category(ca[0], start=shapely.geometry.Point(8.53917, 47.377431), end=None, time_in_s=2000)
