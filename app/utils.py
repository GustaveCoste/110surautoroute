from abc import ABC
import json
from datetime import datetime, timedelta
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import os
from xml.etree import ElementTree
from statistics import mean

import requests

from config import ORS_API_KEY, ORS_API_URL, FUEL_PRICE_API_URL
from app.constants import FUEL_TYPES, FUEL_PRICES_EXPIRATION, FUEL_NAMES_IN_PRICES_FILE
from app.models import FuelPrice, db
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


def get_fuel_prices():
    """ Returns a dictionary containing the average price of each fuel for the day in France. """
    fuel_prices = dict()
    for fuel_type in FUEL_TYPES:
        fuel_price_query = FuelPrice.query.filter(FuelPrice.fuel_type == fuel_type)

        # If the price is not in the database or if it is outdated, recalculate it
        if (fuel_price_query.count() == 0) \
                or ((datetime.now() - fuel_price_query[0].last_update.replace(tzinfo=None))
                    > timedelta(days=FUEL_PRICES_EXPIRATION)):
            update_fuel_prices()

        fuel_prices[fuel_type] = fuel_price_query[0].price

    return fuel_prices


def update_fuel_prices():
    # Downloading the fuel prices xml file
    http_response = urlopen(FUEL_PRICE_API_URL)
    zipfile = ZipFile(BytesIO(http_response.read()))
    zipfile.extractall(path=os.path.join('app', 'static', 'temp', 'fuel_prices'))

    # Parsing the xml to get the average fuel price
    fuel_prices_distribution = {fuel_type: [] for fuel_type in FUEL_TYPES}
    tree = ElementTree.parse(os.path.join('app', 'static', 'temp', 'fuel_prices',
                                          'PrixCarburants_instantane.xml'))
    root = tree.getroot()
    for pdv in root:
        for price in pdv.iter('prix'):
            if price.attrib['nom'] in FUEL_NAMES_IN_PRICES_FILE:
                fuel_prices_distribution[FUEL_NAMES_IN_PRICES_FILE[price.attrib['nom']]].append(float(price.attrib['valeur']))

    for fuel_type in FUEL_TYPES:
        fuel_price_query = FuelPrice.query.filter(FuelPrice.fuel_type == fuel_type)

        if fuel_price_query.count() == 0:
            fuel_price = FuelPrice(fuel_type=fuel_type, price=mean(fuel_prices_distribution[fuel_type]))
        else:
            fuel_price = fuel_price_query[0]
            fuel_price.price = mean(fuel_prices_distribution[fuel_type])
        db.session.add(fuel_price)
    db.session.commit()
