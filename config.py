"""
Parse configuration & init different behavior based on CONFIG_TYPE

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import os
import ConfigParser
import logging
basedir = os.path.abspath(os.path.dirname(__file__))

config_ini = ConfigParser.ConfigParser()
config_ini.read(os.path.join(basedir, 'config.ini'))


CONFIG_TYPE = config_ini.get('GENERAL', 'CONFIG_TYPE')


EOSMDBONE_SECTION = 'EOSMDBOne'
EOSMDBONE_DBNAME = config_ini.get(EOSMDBONE_SECTION, 'DB_NAME')
EOSMDBONE_HOST = config_ini.get(EOSMDBONE_SECTION, 'DB_HOST')
EOSMDBONE_USER = config_ini.get(EOSMDBONE_SECTION, 'DB_USER')
EOSMDBONE_PASSWORD = config_ini.get(EOSMDBONE_SECTION, 'DB_PASSWORD')

GA_SECTION = 'GA'


class Config(object):
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    SQLALCHEMY_POOL_RECYCLE = 30
    SQLALCHEMY_POOL_TIMEOUT = 20

    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}/{}'.format(EOSMDBONE_USER, EOSMDBONE_PASSWORD, EOSMDBONE_HOST, EOSMDBONE_DBNAME)

    APP_OSRM_URL = config_ini.get('OSRM', 'BASE_URL')
    APP_OSRM_CORRECTION_FACTOR = config_ini.getfloat('OSRM', 'CORRECTION_FACTOR')

    APP_GA_POPULATION_SIZE = config_ini.getint(GA_SECTION, 'POPULATION_SIZE')
    APP_GA_TOURNAMENT_SIZE = config_ini.getint(GA_SECTION, 'TOURNAMENT_SIZE')
    APP_GA_MIN_GENERATIONS = config_ini.getint(GA_SECTION, 'MIN_GENERATIONS')
    APP_GA_MAX_GENERATIONS = config_ini.getint(GA_SECTION, 'MAX_GENERATIONS')
    APP_GA_TERMINATION_THRESHOLD = config_ini.getfloat(GA_SECTION, 'TERMINATION_THRESHOLD')
    APP_GA_MAX_RUNTIME_MS = config_ini.getint(GA_SECTION, 'MAX_RUNTIME_MS')

    APP_WALKING_SPEED_KM_H = config_ini.getfloat('ROUTING', 'WALKING_SPEED_KM_H')

    OSM_BASE_URL = config_ini.get('GENERAL', 'OSM_BASE_URL')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = True

    APP_STATIC_FOLDER = '../frontend/app'

    @classmethod
    def init_app(self, app):
        from flask import Blueprint

        logging.getLogger().setLevel(logging.DEBUG)
        blueprint_bower = Blueprint('bower', __name__, static_url_path='/bower_components', static_folder='../frontend/bower_components')
        blueprint_node = Blueprint('node', __name__, static_url_path='/node_modules', static_folder='../frontend/node_modules')
        app.register_blueprint(blueprint_bower)
        app.register_blueprint(blueprint_node)

        @app.after_request
        def print_db_queries(response):
            from flask.ext.sqlalchemy import get_debug_queries
            for query in get_debug_queries():
                app.logger.warning("QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
                                   (query.statement, query.parameters, query.duration, query.context))

            return response

        @app.before_request
        def enable_pydev():
            # remove this if you used pydev and adjust the bath below
            import sys
            sys.path.append(r'C:\Users\root\Dropbox\HSR\skripte\SA\__SA\eclipse-standard-luna-R-win32-x86_64\eclipse\plugins\org.python.pydev_3.8.0.201409251235\pysrc')
            import pydevd
            pydevd.settrace(suspend=False, trace_only_current_thread=True)


class IntegrationConfig(Config):
    # use "built" JavaScript sources (concatenated & minified)
    APP_STATIC_FOLDER = '../frontend/dist'
    DEBUG = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(IntegrationConfig):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': DevelopmentConfig,
    'integration': IntegrationConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
