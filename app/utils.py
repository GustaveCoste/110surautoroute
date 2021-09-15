from abc import ABC
import json

import googlemaps
import requests

from config import GOOGLEMAPS_API_KEY, ORS_API_KEY, ORS_API_URL
from app.views import app


def check_coordinates(f):
    """ Decorator that checks coordinates given as start_lat, start_lon, end_lat, end_lon in the function arguments """

    def wrapper(*args, **kwargs):
        if (float(kwargs['start_lat']) > 90) or (float(kwargs['start_lat']) < -90):
            raise Exception('start_lat must be in [-90, 90]')
        if (float(kwargs['end_lat']) > 90) or (float(kwargs['end_lat']) < -90):
            raise Exception('end_lat must be in [-90, 90]')
        if (float(kwargs['start_lon']) > 180) or (float(kwargs['start_lon']) < -180):
            raise Exception('start_lon must be in [-180, 180]')
        if (float(kwargs['end_lon']) > 180) or (float(kwargs['end_lon']) < -180):
            raise Exception('end_lon must be in [-180, 180]')
        return f(*args, **kwargs)

    return wrapper


class Router(ABC):

    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        pass


# TODO: make all classes return the same object with get_route

class GoogleMapsAPIRouter(Router):
    gmaps = googlemaps.Client(key=GOOGLEMAPS_API_KEY)

    @check_coordinates
    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        return self.gmaps.directions(origin=f'{start_lat},{start_lon}',
                                     destination=f'{end_lat},{end_lon}',
                                     mode='driving')


class OpenRouteServiceRouter(Router):
    ors_request_header = {'Authorization': ORS_API_KEY}

    @check_coordinates
    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        response = requests.post(ORS_API_URL,
                                 headers=self.ors_request_header,
                                 json={"coordinates": ((start_lon, start_lat), (end_lon, end_lat)),
                                       "radiuses": -1})

        if response.status_code == 200:
            app.logger.info('Route request successful.')
        else:
            app.logger.warning(response.content)
        return json.loads(response.content.decode('utf-8'))['routes']
