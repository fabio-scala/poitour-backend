"""
HTTP endpoints for JSON API

:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import sys

from flask import request, jsonify

from app import category_service, cache
from app.structures.tour import Tour, Point

from . import api


@api.errorhandler(400)
def bad_request(e):
    return jsonify(error=400, text='Bad Request. Please check your request parameters.'), 400


@api.route('/tour')
def tour():
    """
    .. http:get:: /tour

        :synopsis: Returns a possible tour that maximizes visited points depending on the specified request parameters

    **Example request**:

    .. sourcecode:: http

        GET <api url>/tour?start=47.376921,8.539824&end=47.376921,8.539824&time_s=10000&stay_time_s=300&point=47.372677,8.535189&point=47.374508,8.539288&point=47.371268,8.538708&point=47.367751,8.512744&point=47.376223,8.541862 HTTP/1.1

    **Example response**

    .. sourcecode:: http

        {
          "distance_m": 6822,
          "path": {
            "coordinates": [
              [
                8.539787,
                47.376928
              ],
              [
                8.539902,
                47.377126
              ],
              ...
            ],
            "type": "LineString"
          },
          "points": {
            "features": [
              {
                "geometry": {
                  "coordinates": [
                    8.539824,
                    47.376921
                  ],
                  "type": "Point"
                },
                "id": "start",
                "properties": {},
                "type": "Feature"
              },
              {
                "geometry": {
                  "coordinates": [
                    8.541862,
                    47.376223
                  ],
                  "type": "Point"
                },
                "id": 4,
                "properties": {},
                "type": "Feature"
              },
              {
                "geometry": {
                  "coordinates": [
                    8.539288,
                    47.374508
                  ],
                  "type": "Point"
                },
                "id": 1,
                "properties": {},
                "type": "Feature"
              },

              ...

              {
                "geometry": {
                  "coordinates": [
                    8.539824,
                    47.376921
                  ],
                  "type": "Point"
                },
                "id": "start",
                "properties": {},
                "type": "Feature"
              }
            ],
            "type": "FeatureCollection"
          },
        "time_s": 7818,
        "time_total_s": 9018
        }

    :query string start: The starting point as as lat,lon (e.g. 47.32,8.34)
    :query string end: The end point as as lat,lon (e.g. 47.32,8.34)
    :query int time_s: The maximum travel time in seconds.
    :query int stay_time_s: The desired stay time per point in seconds.
    :query list point: A list of possible points to be visited as lat,lon

    :statuscode 200: no error
    :statuscode 400: bad or missing request parameters
    :resheader Content-Type: application/json
    """
    points = [Point.from_string(point, id=i) for i, point in enumerate(request.args.getlist('point'))]
    time = int(request.values['time_s'])
    stay_time = int(request.values['stay_time_s'])
    start = Point.from_string(request.values['start'], id='start')
    end = Point.from_string(request.values['end'], id='end')
    tour = Tour.from_points(start, end, time, stay_time, points)

    tour_result = tour.calculate()
    return jsonify(tour_result.to_jsonable())


@api.route('/poi-tour')
@cache.cached(timeout=600)
def poitour():
    """
    .. http:get:: /poi-tour

        :synopsis: Returns a possible tour that maximizes visited points depending on the specified request parameters

    **Example request**:

    .. sourcecode:: http

        GET <api url>/poi-tour?categories=attraction,fountain&end=47.378058,8.5398226&start=47.378058,8.5398226&stay_time_s=900&time_s=9000&weights=5,5 HTTP/1.1

    **Example response**

    .. sourcecode:: http

    {
      "distance_m": 2660,
      "path": {
        "coordinates": [
          [
            8.539781,
            47.377978999999996
          ],
          [
            8.540326,
            47.377767
          ],
          ...
        ],
        "type": "LineString"
      },
      "points": {
        "features": [
      {
        "geometry": {
          "coordinates": [
            8.5398226,
            47.378058
          ],
          "type": "Point"
        },
        "id": "start",
        "properties": {},
        "type": "Feature"
      },
      {
        "geometry": {
          "coordinates": [
            8.5396406615385,
            47.3746913163422
          ],
          "type": "Point"
        },
        "id": null,
        "properties": {
          "description": "",
          "name": "Brunnen ohne Namen",
          "url": "http://www.openstreetmap.org/node/693318521"
        },
        "type": "Feature"
      },

      ...

      {
        "geometry": {
          "coordinates": [
            8.5398226,
            47.378058
          ],
          "type": "Point"
        },
        "id": "start",
        "properties": {},
        "type": "Feature"
      }
    ],
    "type": "FeatureCollection"
      },
      "time_s": 2790,
      "time_total_s": 8954
    }

    :query string start: The starting point as as lat,lon (e.g. 47.32,8.34)
    :query string end: The end point as as lat,lon (e.g. 47.32,8.34)
    :query int time_s: The maximum travel time in seconds.
    :query int stay_time_s: The desired stay time per point in seconds.
    :query string categories: A comma spearated list of interest/POI categories to be visited (e.g. attraction,fountain)
    :query string weights: A comma spearated list of weights (to express preference) per category in the same order as the categories

    :statuscode 200: no error
    :statuscode 400: bad or missing request parameters
    :resheader Content-Type: application/json
    """
    categories = request.values['categories'].split(',')
    weights = map(int, request.values['weights'].split(','))
    assert len(weights) == len(categories)
    time = int(request.values['time_s'])
    stay_time = int(request.values['stay_time_s'])
    start = Point.from_string(request.values['start'], id='start')
    end = Point.from_string(request.values['end'], id='end')

    tour = Tour.from_categories(start, end, time, stay_time, categories, weights)
    tour_result = tour.calculate()

    return jsonify(tour_result.to_jsonable())


# cache by url including parameters
def make_cache_key():
    return request.url

poitour.make_cache_key = make_cache_key
