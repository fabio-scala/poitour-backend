"""
:Author: Fabio Scala <fabio.scala@gmail.com>
"""

import contextlib
import json
import logging
import urllib2


class OsrmService(object):

    """ Service wrapper for OSRM API calls
    :param base_url: OSRM base url including trailing slash
    :type base_url: str
    """

    DEMO_BASE_URL = 'http://router.project-osrm.org/'

    def __init__(self, base_url=None):
        self.base_url = base_url

    def set_base_url(self, base_url):
        self.base_url = base_url

    def _get_url(self):
        if not self.base_url:
            url = self.DEMO_BASE_URL
            logging.warn('Using demo OSRM at ' + url)
        else:
            url = self.base_url

        return url

    @classmethod
    def _urlencode_params(self, **kw):
        return ''.join(('&{}={}'.format(param, json.dumps(value)) for param, value in kw.iteritems()))

    def distance_matrix(self, points, **kw):
        """ Wrapper for OSRMs "table" (distance matrix) API

        :param points: Points to calculate the distance matrix for
        :type points: list of list[lat, lon]

        :param **kw: Other GET parameters that will be passed to the call
        """
        url = self._get_url() + 'table?' + '&'.join(('loc={},{}'.format(*loc) for loc in points))
        if kw:
            url += self._urlencode_params(**kw)
        logging.debug('OSRM table request ' + url)
        with contextlib.closing(urllib2.urlopen(url)) as response:
            return json.load(response)['distance_table']

    def viaroute(self, viapoints, **kw):
        """ Wrapper for OSRMs "viaroute" (routing from A to B via points) API

        :param viapoints: List of ordered points to calculate the route for
        :type viapoints: list of list[lat, lon]

        :param **kw: Other GET parameters that will be passed to the call
        """
        url = self._get_url() + 'viaroute?' + '&'.join(('loc={},{}'.format(*loc) for loc in viapoints))
        if kw:
            url += self._urlencode_params(**kw)
        logging.debug('OSRM viaroute request ' + url)
        with contextlib.closing(urllib2.urlopen(url)) as response:
            return json.load(response)


# provide default instance
osrm = OsrmService()
