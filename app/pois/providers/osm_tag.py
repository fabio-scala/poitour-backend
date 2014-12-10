"""
Category providers based on OSM tags which are queried from EOSMDBOne.

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import geoalchemy2.shape

from ..providerbase import PoiProvider, Category, CategoryPoint
from app.utils.eosmdbone import Point, Polygon
from flask import current_app as app
import copy


class TagBasedCategory(Category):

    def __init__(self, **kw):
        self.tags = kw.pop('tags', [])
        self.includes = kw.pop('includes', [])
        kw['display_name'] = kw.get('display_name', False)
        super(TagBasedCategory, self).__init__(**kw)

    @classmethod
    def _from_config_entry(cls, entry, **kw):
        """ Returns an instance based on a category entry as dict from yaml config
        """
        return cls(**dict(kw.items() + entry.items()))

    def _get_condition(self, table):
        """ Returns an SQLAlchemy expression for querying this category
        """
        from sqlalchemy import not_
        expression = None

        for tag in self.tags:
            criterion = None
            # DO NOT USE Poi.tags['amenity'] == 'restaurant'), SLOW!
            contains_tags = {k: v for k, v in tag.items() if v[0] != '~'}
            not_tags = {k: v[1:] for k, v in tag.items() if v[0] == '~'}
            if contains_tags:
                contains_criterion = table.tags.contains(contains_tags)
                criterion = (criterion & contains_criterion) if criterion is not None else contains_criterion
            if not_tags:
                not_criterion = not_(table.tags.contains(not_tags))
                criterion = (criterion & not_criterion) if criterion is not None else not_criterion

            expression = (expression | criterion) if expression is not None else criterion

        assert expression is not None
        return expression


class OsmPoi(CategoryPoint):

    def __init__(self, category, name, lon, lat, osm_id, is_point, description=''):
        name = category.name + (u' "{}"'.format(name) if name else u' ohne Namen')
        CategoryPoint.__init__(self, category, name, lon, lat, description=description)
        self.osm_id = osm_id
        self.is_point = is_point

    def get_url(self):
        return app.config['OSM_BASE_URL'] + ('node' if self.is_point else 'way') + '/' + str(self.osm_id)


class OsmTagsProvider(PoiProvider):

    def __init__(self, config):
        super(OsmTagsProvider, self).__init__(config)
        self.config = config
        self.by_id = {}
        self.displayed_categories = []

    def get_categories(self):
        """ See PoiProvider.get_categories
        """
        self.by_id = {entry['id']: TagBasedCategory._from_config_entry(entry, belongs_to=self) for entry in self.config}
        self.displayed_categories = [c for c in self.by_id.itervalues() if c.display_name]

        return self.displayed_categories

    def expand_category(self, category):
        """ Expands a category that includes (groups) other categories into single category objects for building query
            and presents it to the PoiProvider to still be distinguishable
            Eg. "Weihnachten" should include christmas trees as well as markets, but we still want to know which POI is which in the frontend
        """
        q = [category]
        expanded = []
        root_id = category.id

        while q:
            cur = q.pop()
            q.extend([self.by_id[cat_id] for cat_id in cur.includes])
            cur_copy = copy.copy(cur)
            cur_copy.original_id = cur_copy.id
            cur_copy.id = root_id
            if cur_copy.tags:  # container has tags itself?
                cur_copy.includes = []  # avoid endless recursion
                expanded.append(cur_copy)
        return expanded

    def fast_query(self, categories, start, radius_m):
        """ Experimental fast sql query using only two CTE queries for all requested POIs
            This approach was tested (EXPLAIN ANALYZE) to be faster than using osm_poi because the osm_poi view uses UNION instead of UNION ALL (needs re-sort)
                WITH my_cte AS ( ... our cte with radius constraint on osm_point and osm_polygon with UNION ALL ) SELECT ... UNION SELECT ... UNION SELECT ...
        """

        from sqlalchemy import select, literal, union_all
        from app import db
        loc = geoalchemy2.shape.from_shape(start, 4326).ST_Transform(Point.SRID)
        lookup = {hash(c.original_id): c for c in categories}

        q_points = select([Point.name, Point.osm_id, Point.way, Point.tags, Point.way.ST_Transform(4326).ST_X().label(
            'lon'), Point.way.ST_Transform(4326).ST_Y().label('lat'), literal(True).label('is_point')]).where(Point.way.ST_DWithin(loc, radius_m))
        q_polygons = select([Polygon.name, Polygon.osm_id, Polygon.way, Polygon.tags, Polygon.way.ST_Transform(4326).ST_Centroid().ST_X().label(
            'lon'), Polygon.way.ST_Transform(4326).ST_Centroid().ST_Y().label('lat'), literal(False).label('is_point')]).where(Polygon.way.ST_DWithin(loc, radius_m))

        cte = union_all(q_points, q_polygons).cte()

        unions = []
        for id_hash, category in lookup.iteritems():
            cond = category._get_condition(cte.c)
            query = select([cte.c.name, cte.c.osm_id, cte.c.lon, cte.c.lat, cte.c.is_point, literal(id_hash).label('c_id')]).where(cond)
            unions.append(query)
        inner_query = union_all(*unions)
        results = db.session.execute(inner_query).fetchall()

        points = []
        for name, osm_id, lon, lat, is_point, cat_id in results:
            points.append(OsmPoi(lookup[cat_id], name, lon, lat, osm_id, is_point))

        return points

    def get_points_for_categories(self, categories, start, end, time_s, radius_m, speed_km_h):
        """ Fast all-in-one fetch for all categories """
        expanded = []
        for category in categories:
            expanded.extend(self.expand_category(category))

        return self.fast_query(expanded, start, radius_m)

    def get_points_for_category(self, category_obj, start, end, time_s, radius_m, speed_km_h):
        """ See PoiProvider.get_points_for_category
        """
        return self.get_points_for_categories([category_obj], start, end, time_s, radius_m, speed_km_h)
