"""
HTTP endpoints for the web application

:Author: Fabio Scala <fabio.scala@gmail.com>
"""
import os
import sys

from flask import jsonify

from app import cache, basedir
from app import pois
from config import config_ini

from . import main


@main.route('/')
def root():
    return main.send_static_file('index.html')


@main.route('/config')
@cache.cached(timeout=sys.maxint)
def get_categories():
    """ Returns initial data for the client
        e.g. available categories from providers as well as initially preselected categories from application config
    """
    categories = pois.get_categories()
    config = {k.upper(): v for k, v in config_ini.items('CLIENT')}
    default_category_ids, weights = zip(*[c.strip().split(':') for c in config['CATEGORIES'].split(',')])
    config['CATEGORIES'] = default_category_ids
    config['WEIGHTS'] = map(int, weights)

    for k in ('HOURS', 'MINUTES', 'STAY_TIME'):
        config[k] = int(config[k])

    return jsonify({
        'config': config,
        'categories':
        [{
            'id': c.id,
            'display_name': c.display_name,
            'description': c.description,
        } for c in categories]})
