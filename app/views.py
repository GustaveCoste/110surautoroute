import uuid

from flask import Flask, request
from geoalchemy2 import func
import polyline

app = Flask(__name__)
app.config.from_object('config')

from .utils import OpenRouteServiceRouter
from .models import Waypoint, Motorway, db
from .constants import PROJECTED_CRS_SRID, WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD

router = OpenRouteServiceRouter()


@app.route('/')
def index():
    return 'coucou'


# test url
# http://127.0.0.1:5000/route?start_lat=43.876972&start_lon=5.412461&end_lat=44.555107&end_lon=6.068406

@app.route('/route')
def route():
    # Creating a session id used to distinguish database objects of each concurrent users
    session_id = str(uuid.uuid4())

    start_lon, start_lat = request.args.get('start_lon'), request.args.get('start_lat')
    end_lon, end_lat = request.args.get('end_lon'), request.args.get('end_lat')

    # TODO: tester coords

    route = router.get_route(start_lat=start_lat,
                             start_lon=start_lon,
                             end_lat=end_lat,
                             end_lon=end_lon)

    total_duration = route[0]['summary']['duration']
    total_distance = route[0]['summary']['distance']
    waypoints = polyline.decode(route[0]['geometry'], 5)
    segments = route[0]['segments'][0]['steps']

    # Filtering segments on motorways (> 90km/h)
    motorway_segments = [segment for segment in segments
                         if segment['duration']
                         and (3.6 * segment['distance'] / segment['duration'] >= 90)]

    # Getting the motorway elements in the database corresponding to this segment
    for motorway_segment in motorway_segments:
        segment_distance = motorway_segment['distance']
        segment_duration = motorway_segment['duration']
        segment_speed = 3.6 * segment_distance / segment_duration

        segment_waypoints = [Waypoint(latitude=coords[0], longitude=coords[1], session_id=session_id)
                             for coords
                             in waypoints[motorway_segment['way_points'][0]:motorway_segment['way_points'][1]]]

        # Adding waypoints to the database
        db.session.add_all(segment_waypoints)
        db.session.commit()

        # TODO: make sure that no motoway element from the other side of the motorway is selected

        # Getting every motorway element close to a route waypoint
        query = db.session.query(Motorway.maxspeed, Motorway.length) \
            .join(Waypoint,
                  Motorway.geometry.ST_Intersects(
                      func.ST_Buffer(
                          func.ST_Transform(Waypoint.geometry,
                                            PROJECTED_CRS_SRID),
                          WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD,
                          10)
                  )
                  ).filter((Motorway.highway_type == 'motorway')
                           & (Waypoint.session_id == session_id))

        # TODO: Wrong result
        distance_130kmh = sum([x.length for x in query if x.maxspeed == '130'])
        distance_110kmh = sum([x.length for x in query if x.maxspeed == '110'])

    # Removing waypoints from the database
    Waypoint.query.filter(Waypoint.session_id == session_id).delete()
    db.session.commit()

    return str(route)
