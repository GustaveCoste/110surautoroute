from abc import ABC
import json

import googlemaps
import requests

from config import googlemaps_api_key, ors_api_key, ors_api_url


class Router(ABC):

    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        pass


# TODO: make all classes return the same object with get_route

class GoogleMapsAPIRouter(Router):
    gmaps = googlemaps.Client(key=googlemaps_api_key)

    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        return self.gmaps.directions(origin=f'{start_lat},{start_lon}',
                                     destination=f'{end_lat},{end_lon}',
                                     mode='driving')


class OpenRouteServiceRouter(Router):
    ors_request_header = {'Authorization': ors_api_key}

    def get_route(self, start_lat, start_lon, end_lat, end_lon):
        response = requests.post(ors_api_url,
                                 headers=self.ors_request_header,
                                 json={"coordinates": ((start_lon, start_lat), (end_lon, end_lat))})
        return json.loads(response.content.decode('utf-8'))['routes']
