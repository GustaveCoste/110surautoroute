from datetime import datetime, timedelta

from flask import Flask, request, render_template, url_for, redirect
from sassutils.wsgi import SassMiddleware
from geoalchemy2 import func
from geoalchemy2.types import to_shape
import polyline
from shapely.geometry import LineString
from geomet import wkt

app = Flask(__name__)

app.config.from_object('config')

# Building CSS files at each request
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'app': ('static/scss', 'static/css', '/static/css')
})

from app.forms import RouteForm
from app.utils import OpenRouteServiceRouter, get_fuel_prices
from app.models import Waypoint, Motorway, CalculationRequest, CalculationResponse, db
from app.constants import PROJECTED_CRS_SRID, WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD, \
    CONSUMPTION_REDUCTION_FACTOR_110_130, FUEL_CO2_EMISSIONS, DEFAULT_FUEL_CONSUMPTION_PER_VEHICLE, \
    CONSUMPTION_FACTOR_130, CONSUMPTION_FACTOR_110

app.config['DEFAULT_FUEL_CONSUMPTION_PER_VEHICLE'] = DEFAULT_FUEL_CONSUMPTION_PER_VEHICLE
app.config['CONSUMPTION_FACTOR_130'] = CONSUMPTION_FACTOR_130
app.config['CONSUMPTION_FACTOR_110'] = CONSUMPTION_FACTOR_110

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
                           end_lon=request.args.get('end_lon') or 'undefined',
                           fuel_prices=get_fuel_prices())


@app.route('/route/')
def route():
    start_time = datetime.now()
    calculation_request = CalculationRequest(start_latitude=request.args.get('start_lat'),
                                             start_longitude=request.args.get('start_lon'),
                                             end_latitude=request.args.get('end_lat'),
                                             end_longitude=request.args.get('end_lon'),
                                             vehicle_type=request.args.get('vehicle_type'),
                                             fuel_type=request.args.get('fuel_type'),
                                             non_motorway_consumption=request.args.get('non_motorway_consumption'),
                                             motorway_consumption_110=request.args.get('motorway_consumption_110'),
                                             motorway_consumption_130=request.args.get('motorway_consumption_130'),
                                             client_platform=request.user_agent.platform,
                                             user_agent=request.user_agent.string)
    db.session.add(calculation_request)
    db.session.commit()

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

    db.session.begin()
    motorway_waypoints = []
    for segment_index, motorway_segment in enumerate(motorway_segments):
        motorway_waypoints += [Waypoint(latitude=coords[0], longitude=coords[1], rank=rank, segment=segment_index)
                               for rank, coords
                               in enumerate(waypoints[motorway_segment['way_points'][0]
                                                      :motorway_segment['way_points'][1]])]

    # Adding waypoints to the database
    db.session.add_all(motorway_waypoints)
    app.logger.info(f"{len(motorway_waypoints)} motorway waypoints identified.")

    # Getting every waypoint over a 130 km/h or 110 km/h motorway element
    # For some reason, it is faster to query separately according to the max speed rather than to add the max speed to
    # the queried fields and to remove filter.
    categorized_motorway_waypoints = dict()
    for max_speed in (110, 130):
        query = Waypoint.query \
            .with_entities(Waypoint.segment,
                           Waypoint.rank,
                           Waypoint.geometry,
                           func.ST_Transform(Waypoint.geometry, PROJECTED_CRS_SRID).label('projected_geometry')) \
            .join(Motorway,
                  Motorway.geometry.ST_Intersects(
                      func.ST_Buffer(
                          func.ST_Transform(Waypoint.geometry,
                                            PROJECTED_CRS_SRID),
                          WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD,
                          10)
                  )) \
            .filter(Motorway.maxspeed == max_speed)

        for waypoint in query:
            if waypoint.segment not in categorized_motorway_waypoints:
                categorized_motorway_waypoints[waypoint.segment] = []

            categorized_motorway_waypoints[waypoint.segment].append({'rank': waypoint.rank,
                                                                     'maxspeed': max_speed,
                                                                     'geometry': to_shape(waypoint.geometry),
                                                                     'projected_geometry': to_shape(
                                                                         waypoint.projected_geometry)})

    # Removing waypoints from the database
    db.session.rollback()

    # For each segment, sorting the waypoints and computing the distance between them separately according if they are
    # at 110 km/h or 130 km/h
    distances = {110: 0,
                 130: 0}

    for motorway_segment_waypoints in categorized_motorway_waypoints.values():
        motorway_segment_waypoints.sort(key=lambda x: x['rank'])

        # Looping on each waypoint to add the distance between itself and the next one to the appropriate distance field
        start_geom = motorway_segment_waypoints[0]['projected_geometry']
        for waypoint in motorway_segment_waypoints[1:]:
            end_geom = waypoint['projected_geometry']
            distances[waypoint['maxspeed']] += start_geom.distance(end_geom)
            start_geom = end_geom

    distance_110kmh = distances[110]
    distance_130kmh = distances[130]

    # Creating linestring geometries for each segment by joining the waypoints
    motorways_geometries = [wkt.loads(LineString([wp['geometry'] for wp in segment]).wkt)
                            for segment in categorized_motorway_waypoints.values()]

    # Calculating travelled time at different speeds
    motorway_travel_time_110 = timedelta(hours=(((distance_130kmh + distance_110kmh) / 1000) / 110))
    motorway_travel_time_130 = timedelta(hours=((distance_130kmh / 1000) / 130) + ((distance_110kmh / 1000) / 110))

    # Calculating consumption difference
    non_motorway_consumption = float(request.args['non_motorway_consumption'])
    motorway_110kmh_consumption = float(request.args['motorway_consumption_110'])
    motorway_130kmh_consumption = float(request.args['motorway_consumption_130'])

    non_motorway_consumed_fuel = non_motorway_consumption * (non_motorway_distance / 100000)
    motorway_consumed_fuel_130 = (motorway_110kmh_consumption * (distance_110kmh / 100000)) \
                                 + (motorway_130kmh_consumption * (distance_130kmh / 100000))
    motorway_consumed_fuel_110 = motorway_110kmh_consumption * ((distance_110kmh + distance_130kmh) / 100000)
    co2_emissions_difference = (motorway_consumed_fuel_130 - motorway_consumed_fuel_110) \
                               * FUEL_CO2_EMISSIONS[request.args['fuel_type']]

    saved_money = (motorway_consumed_fuel_130 - motorway_consumed_fuel_110) * float(request.args['fuel_price'])

    calculation_response = CalculationResponse(calculation_request=calculation_request,
                                               response_time=datetime.now() - start_time,
                                               motorway_travel_time_110=motorway_travel_time_110,
                                               motorway_travel_time_130=motorway_travel_time_130,
                                               non_motorway_travel_time=non_motorway_travel_time,
                                               non_motorway_consumed_fuel=non_motorway_consumed_fuel,
                                               motorway_consumed_fuel_130=motorway_consumed_fuel_130,
                                               motorway_consumed_fuel_110=motorway_consumed_fuel_110,
                                               saved_money=saved_money)
    db.session.add(calculation_response)
    db.session.commit()

    return render_template('result.html',
                           motorway_travel_time_110=motorway_travel_time_110,
                           motorway_travel_time_130=motorway_travel_time_130,
                           non_motorway_travel_time=non_motorway_travel_time,
                           non_motorway_consumed_fuel=non_motorway_consumed_fuel,
                           motorway_consumed_fuel_130=motorway_consumed_fuel_130,
                           motorway_consumed_fuel_110=motorway_consumed_fuel_110,
                           route_geometry=route[0]['geometry'].replace('\\', '\\\\'),
                           motorways_geometries=motorways_geometries,
                           co2_emissions_difference=co2_emissions_difference,
                           saved_money=saved_money)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/references/')
def references():
    return render_template('references.html')
