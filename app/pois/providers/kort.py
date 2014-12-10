"""
POI category provider for Kort API.

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import contextlib
import json
import urllib2

from flask import current_app as app
import geoalchemy2.shape

from ..providerbase import PoiProvider, Category, CategoryPoint


class KortPoi(CategoryPoint):

    def __init__(self, category, name, lon, lat, osm_id, osm_type, description=''):
        CategoryPoint.__init__(self, category, name, lon, lat, description=description)
        self.osm_id = osm_id
        self.osm_type = osm_type

    def get_url(self):
        return app.config['OSM_BASE_URL'] + self.osm_type + '/' + self.osm_id


class KortProvider(PoiProvider):

    DEFAULT_KORT_URL = 'http://play.kort.ch/server/webservices/mission/position/'

    def __init__(self, config):
        super(KortProvider, self).__init__(config)
        self.config = config
        self.categories = [Category(self, 'kort', 'Kort', 'Kort POIs <a href="http://www.kort.ch/" target="_blank">(Info)</a>', '')]

    def get_categories(self):
        """ See PoiProvider.get_categories
        """
        return self.categories

    def get_points_for_category(self, category_obj, start, end, time_in_s, radius_m, speed_km_h):
        """ See PoiProvider.get_points_for_category
        """
        url = self.DEFAULT_KORT_URL + '{},{}?lang=de&radius={}'.format(start.y, start.x, radius_m)
        with contextlib.closing(urllib2.urlopen(url)) as response:
            points = json.loads(response.read())['return']
            return [KortPoi(category_obj, u'Kort "{}"'.format(p['title']), float(p['longitude']), float(p['latitude']), p['osm_id'], p['osm_type'], p['description']) for p in points]
