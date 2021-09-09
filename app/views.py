from flask import Flask, request
from geoalchemy2 import func
import polyline

app = Flask(__name__)
app.config.from_object('config')

from .utils import GoogleMapsAPIRouter, OpenRouteServiceRouter
from .models import Waypoint, Motorway

router = OpenRouteServiceRouter()


@app.route('/')
def index():
    return 'coucou'


# test url
# http://127.0.0.1:5000/route?start_lat=43.876972&start_lon=5.412461&end_lat=44.555107&end_lon=6.068406

@app.route('/route')
def route():
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

    # Filtering segments on highways (> 90km/h)
    highway_segments = [segment for segment in segments
                        if segment['duration']
                        and (3.6 * segment['distance'] / segment['duration'] >= 90)]

    for highway_segment in highway_segments:
        segment_distance = highway_segment['distance']
        segment_duration = highway_segment['duration']
        segment_speed = 3.6 * segment_distance / segment_duration
        segment_waypoints = [Waypoint(coords[0], coords[1])
                             for coords in waypoints[highway_segment['way_points'][0]:highway_segment['way_points'][1]]]

    return str(route)
