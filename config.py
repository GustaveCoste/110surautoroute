import os

DEBUG = os.environ['DEBUG']

# Protecting against CSRF attacks
SECRET_KEY = os.environ['SECRET_KEY']

# OpenRouteService API
ORS_API_KEY = os.environ['ORS_API_KEY']
ORS_API_URL = 'https://api.openrouteservice.org/v2/directions/driving-car'

# Mapbox API
MAPBOX_API_KEY = os.environ['MAPBOX_API_KEY']

# Database initialization
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://")

TITLE = "110 km/h sur l'autoroute"
