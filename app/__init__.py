"""
Flask App Setup

:Author: Fabio Scala <fabio.scala@gmail.com>
"""


import os
import sys
import config

basedir = config.basedir
appdir = os.path.abspath(os.path.dirname(__file__))


from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache


cache = Cache(config={'CACHE_TYPE': 'simple'})
db = SQLAlchemy()

from .routing import osrm
osrm = osrm.OsrmService()

category_service = None

from flask import Flask, Blueprint


def create_app(config_name):
    eff_config = config.config[config_name]
    app = Flask(__name__, static_folder=eff_config.APP_STATIC_FOLDER, static_url_path='')
    app.config.from_object(eff_config)
    eff_config.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    osrm.set_base_url(eff_config.APP_OSRM_URL)

    from app import pois
    pois.set_config_path(os.path.join(basedir, 'providers_config.yaml'))

    from .api import api as blueprint_api_v_1_0
    from .main import main as blueprint_main

    blueprint_main.static_folder = '../' + eff_config.APP_STATIC_FOLDER
    app.register_blueprint(blueprint_main)
    app.register_blueprint(blueprint_api_v_1_0, url_prefix='/api/v1.0')

    return app
