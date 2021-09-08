from flask import Flask, request

from .utils import GoogleMapsAPIRouter, OpenRouteServiceRouter

app = Flask(__name__)

# router = OpenRouteServiceRouter()
router = GoogleMapsAPIRouter()


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

    return str(route)
