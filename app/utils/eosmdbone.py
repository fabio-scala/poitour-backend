"""
SQLAlchemy OR Mapping for osm_poi view of geometa labs EOSMDBOne database

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

from geoalchemy2 import Geometry

from app import db
import sqlalchemy.dialects.postgresql as psql


class BaseModel(db.Model):
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    # SRID of the database
    SRID = 900913


class Poi(BaseModel):
    __tablename__ = 'osm_poi'

    osm_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    tags = db.Column(psql.HSTORE)
    gtype = db.Column(db.Text)
    osm_version = db.Column(db.Text)
    way = db.Column(Geometry(geometry_type='POINT', srid=BaseModel.SRID))

    # calculated properties
    lon = db.column_property(way.ST_Transform(4326).ST_X())
    lat = db.column_property(way.ST_Transform(4326).ST_Y())


class Point(BaseModel):
    __tablename__ = 'osm_point'

    osm_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    tags = db.Column(psql.HSTORE)
    way = db.Column(Geometry(geometry_type='POINT', srid=BaseModel.SRID))

    # calculated properties
    lon = db.column_property(way.ST_Transform(4326).ST_X())
    lat = db.column_property(way.ST_Transform(4326).ST_Y())


class Polygon(BaseModel):
    __tablename__ = 'osm_polygon'

    osm_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    tags = db.Column(psql.HSTORE)
    way = db.Column(Geometry(geometry_type='POLYGON', srid=BaseModel.SRID))


if __name__ == '__main__':
    import app
    appl = app.create_app('default')
    appl.app_context().push()

    from geoalchemy2 import WKTElement
    here = WKTElement('POINT({} {})'.format(8.53917, 47.377431), srid=4326).ST_Transform(Poi.SRID)

    # cte = select([Point.name, Point.osm_id, Point.way, Point.tags, literal(True).label('is_point')]).where(Point.way.ST_DWithin(here, 1000)).cte()
