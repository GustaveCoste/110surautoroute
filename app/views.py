from datetime import timedelta

from flask import Flask, request, render_template, url_for, redirect
from geoalchemy2 import func
import polyline

app = Flask(__name__)
app.config.from_object('config')

from app.forms import RouteForm
from app.utils import OpenRouteServiceRouter
from app.models import Waypoint, Motorway, db
from app.constants import PROJECTED_CRS_SRID, WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD, DEFAULT_NON_MOTORWAY_CONSUMPTION, \
    DEFAULT_MOTORWAY_110KMH_CONSUMPTION, DEFAULT_MOTORWAY_130KMH_CONSUMPTION, CONSUMPTION_REDUCTION_FACTOR_110_130

router = OpenRouteServiceRouter()


@app.route('/')
@app.route('/index/')
def index():
    form = RouteForm(request.args)

    if form.validate():
        return redirect(url_for('route', **request.args))
    return render_template('index.html',
                           form=form,
                           consumption_reduction_factor_110_130=CONSUMPTION_REDUCTION_FACTOR_110_130,
                           start_lat=request.args.get('start_lat') or 'undefined',
                           start_lon=request.args.get('start_lon') or 'undefined',
                           end_lat=request.args.get('end_lat') or 'undefined',
                           end_lon=request.args.get('end_lon') or 'undefined')


@app.route('/route/')
def route():
    start_lon, start_lat = request.args.get('start_lon'), request.args.get('start_lat')
    end_lon, end_lat = request.args.get('end_lon'), request.args.get('end_lat')

    route = router.get_route(start_lat=start_lat,
                             start_lon=start_lon,
                             end_lat=end_lat,
                             end_lon=end_lon)

    total_duration = timedelta(seconds=route[0]['summary']['duration'])
    total_distance = route[0]['summary']['distance']
    waypoints = polyline.decode(route[0]['geometry'], 5)
    segments = route[0]['segments'][0]['steps']

    # Filtering segments on motorways (> 90km/h)
    motorway_segments = [segment for segment in segments
                         if segment['duration']
                         and (3.6 * segment['distance'] / segment['duration'] >= 90)]

    # Getting duration and distance of the non-motorway part of the route
    non_motorway_segments = [x for x in segments if x not in motorway_segments]
    non_motorway_travel_time = timedelta(seconds=sum([x['duration'] for x in non_motorway_segments]))
    non_motorway_distance = sum([x['distance'] for x in non_motorway_segments])

    # Getting the motorway elements in the database corresponding to this segment
    distance_130kmh = distance_110kmh = 0

    db.session.begin()
    motorway_waypoints = []
    for motorway_segment in motorway_segments:
        motorway_waypoints += [Waypoint(latitude=coords[0], longitude=coords[1])
                               for coords
                               in waypoints[motorway_segment['way_points'][0]
                                            :motorway_segment['way_points'][1]]]

    # Adding waypoints to the database
    db.session.add_all(motorway_waypoints)
    app.logger.info(f"{len(motorway_waypoints)} motorway waypoints identified.")

    # Removing waypoints that are on a motorway link (to avoid selection of a wrong motorway element if a waypoint
    # is on a motorway link over an undesired motorway element)
    ids_to_delete = Waypoint.query \
        .join(Motorway,
              Motorway.geometry.ST_Intersects(
                  func.ST_Buffer(
                      func.ST_Transform(Waypoint.geometry,
                                        PROJECTED_CRS_SRID),
                      WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD,
                      10)
              )) \
        .filter((Motorway.highway_type == 'motorway_link')) \
        .group_by(Waypoint) \
        .with_entities(Waypoint.id)

    nb_deleted_waypoints = Waypoint.query.filter(Waypoint.id.in_(ids_to_delete)).delete(synchronize_session=False)
    app.logger.info(f"{nb_deleted_waypoints} deleted waypoints.")

    # Getting every motorway element close to a route waypoint
    motorway_query = Motorway.query \
        .with_entities(Motorway.length,
                       Motorway.maxspeed,
                       func.ST_AsGeoJSON(func.ST_Transform(Motorway.geometry, 4326)).label('geojson_geometry')) \
        .join(Waypoint,
              Motorway.geometry.ST_Intersects(
                  func.ST_Buffer(
                      func.ST_Transform(Waypoint.geometry,
                                        PROJECTED_CRS_SRID),
                      WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD,
                      10)
              )) \
        .filter((Motorway.highway_type == 'motorway')) \
        .group_by(Motorway)

    distance_130kmh += sum([x.length for x in motorway_query if x.maxspeed == '130'])
    distance_110kmh += sum([x.length for x in motorway_query if x.maxspeed == '110'])
    motorways_geometries = [x.geojson_geometry for x in motorway_query]
    app.logger.info(f"{motorway_query.count()} motorway elements identified.")

    # Removing waypoints from the database
    db.session.rollback()

    # Calculating travelled time at different speeds
    motorway_travel_time_110 = timedelta(hours=(((distance_130kmh + distance_110kmh) / 1000) / 110))
    motorway_travel_time_130 = timedelta(hours=((distance_130kmh / 1000) / 130) + ((distance_110kmh / 1000) / 110))

    # Calculating consumption difference
    non_motorway_consumption = float(request.args.get('non_motorway_consumption',
                                                      DEFAULT_NON_MOTORWAY_CONSUMPTION))
    motorway_110kmh_consumption = float(request.args.get('motorway_110kmh_consumption',
                                                         DEFAULT_MOTORWAY_110KMH_CONSUMPTION))
    motorway_130kmh_consumption = float(request.args.get('motorway_130kmh_consumption',
                                                         DEFAULT_MOTORWAY_130KMH_CONSUMPTION))

    non_motorway_consumed_fuel = non_motorway_consumption * (non_motorway_distance / 100000)
    motorway_consumed_fuel_130 = (motorway_110kmh_consumption * (distance_110kmh / 100000)) \
                                 + (motorway_130kmh_consumption * (distance_130kmh / 100000))
    motorway_consumed_fuel_110 = motorway_110kmh_consumption * ((distance_110kmh + distance_130kmh) / 100000)

    return render_template('result.html',
                           motorway_travel_time_110=motorway_travel_time_110,
                           motorway_travel_time_130=motorway_travel_time_130,
                           non_motorway_travel_time=non_motorway_travel_time,
                           non_motorway_consumed_fuel=non_motorway_consumed_fuel,
                           motorway_consumed_fuel_130=motorway_consumed_fuel_130,
                           motorway_consumed_fuel_110=motorway_consumed_fuel_110,
                           route_geometry=route[0]['geometry'].replace('\\', '\\\\'),
                           motorways_geometries=motorways_geometries
                           )
