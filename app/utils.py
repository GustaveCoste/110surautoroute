from abc import ABC
import json

import googlemaps
import requests

from config import googlemaps_api_key, ors_api_key, ors_api_url


def check_coordinates(f):
    """ Decorator that checks coordinates given as start_lat, start_lon, end_lat, end_lon in the function arguments """

    def wrapper(*args, **kw):
        if (float(kw['start_lat']) > 90) or (float(kw['start_lat']) < -90):
            raise Exception('start_lat must be in [-90, 90]')
        if (float(kw['end_lat']) > 90) or (float(kw['end_lat']) < -90):
            raise Exception('end_lat must be in [-90, 90]')
        if (float(kw['start_lon']) > 180) or (float(kw['start_lon']) < -180):
            raise Exception('start_lon must be in [-180, 180]')
        if (float(kw['end_lon']) > 180) or (float(kw['end_lon']) < -180):
            raise Exception('end_lon must be in [-180, 180]')

    return wrapper


class Router(ABC):

    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        pass


# TODO: make all classes return the same object with get_route

class GoogleMapsAPIRouter(Router):
    gmaps = googlemaps.Client(key=googlemaps_api_key)

    @check_coordinates
    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        return self.gmaps.directions(origin=f'{start_lat},{start_lon}',
                                     destination=f'{end_lat},{end_lon}',
                                     mode='driving')


class OpenRouteServiceRouter(Router):
    ors_request_header = {'Authorization': ors_api_key}

    @check_coordinates
    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        response = requests.post(ors_api_url,
                                 headers=self.ors_request_header,
                                 json={"coordinates": ((start_lon, start_lat), (end_lon, end_lat))})
        return json.loads(response.content.decode('utf-8'))['routes']
