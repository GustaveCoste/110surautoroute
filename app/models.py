import logging as lg

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
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


class CalculationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))
    end_geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))
    vehicle_type = db.Column(db.Text)
    fuel_type = db.Column(db.Text)
    non_motorway_consumption = db.Column(db.Float)
    motorway_consumption_130 = db.Column(db.Float)
    motorway_consumption_110 = db.Column(db.Float)
    client_platform = db.Column(db.Text)
    user_agent = db.Column(db.Text)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())

    calculation_response = db.relationship("CalculationResponse", back_populates="calculation_request")

    def __init__(self,
                 start_latitude: float,
                 start_longitude: float,
                 end_latitude: float,
                 end_longitude: float,
                 vehicle_type: str,
                 fuel_type: str,
                 non_motorway_consumption: float,
                 motorway_consumption_130: float,
                 motorway_consumption_110: float,
                 client_platform: str,
                 user_agent: str):
        self.start_geometry = f"SRID=4326;POINT({start_longitude} {start_latitude})"
        self.end_geometry = f"SRID=4326;POINT({end_longitude} {end_latitude})"
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.non_motorway_consumption = non_motorway_consumption
        self.motorway_consumption_130 = motorway_consumption_130
        self.motorway_consumption_110 = motorway_consumption_110
        self.client_platform = client_platform
        self.user_agent = user_agent


class CalculationResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    calculation_request_id = db.Column(db.Integer, db.ForeignKey('calculation_request.id'))
    response_time = db.Column(db.Interval)
    non_motorway_travel_time = db.Column(db.Interval)
    motorway_travel_time_130 = db.Column(db.Interval)
    motorway_travel_time_110 = db.Column(db.Interval)
    non_motorway_consumed_fuel = db.Column(db.Float)
    motorway_consumed_fuel_130 = db.Column(db.Float)
    motorway_consumed_fuel_110 = db.Column(db.Float)

    calculation_request = db.relationship("CalculationRequest", back_populates="calculation_response")


def init_db():
    db.drop_all()
    db.create_all()

    with app.open_resource('static/motorway.sql') as file:
        db.engine.execute(file.read().decode('utf8'))

    lg.warning('Database initialized!')
