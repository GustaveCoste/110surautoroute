import logging as lg

from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry

from .views import app
from .constants import PROJECTED_CRS_SRID

db = SQLAlchemy(app)


class Motorway(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    osm_id = db.Column(db.Integer)
    highway_type = db.Column('highway', db.Text)
    maxspeed = db.Column(db.Integer, nullable=True)
    length = db.Column(db.Float)
    geometry = db.Column(Geometry(geometry_type='LINESTRING', srid=PROJECTED_CRS_SRID))


class Waypoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))

    def __init__(self, latitude: float, longitude: float):
        self.geometry = f"POINT({longitude} {latitude})"


def init_db():
    db.drop_all()
    db.create_all()

    with app.open_resource('static/motorway.sql') as file:
        db.engine.execute(file.read().decode('utf8'))

    lg.warning('Database initialized!')
