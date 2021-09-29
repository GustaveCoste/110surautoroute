function updateFuelConsumption(){
    var vehicleType = document.getElementById('vehicle_type').value;
    var fuelType = document.getElementById('fuel_type').value;

    document.getElementById('non_motorway_consumption').value = defaultFuelConsumptionPerVehicle[vehicleType][fuelType];
    document.getElementById('motorway_consumption_130').value =
        Math.round(defaultFuelConsumptionPerVehicle[vehicleType][fuelType] * consumptionFactor130 * 10) / 10;
    document.getElementById('motorway_consumption_110').value =
        Math.round(defaultFuelConsumptionPerVehicle[vehicleType][fuelType] * consumptionFactor110 * 10) / 10;
}

function enableSubmitButton(button_id){
    if ((document.getElementById('start_lat').value !== '')
        && (document.getElementById('start_lon').value !== '')
        && (document.getElementById('end_lat').value !== '')
        && (document.getElementById('end_lon').value !== '')) {
        document.getElementById(button_id).disabled=false;
    }
}

function formMap(map_id, form_field_lat_id, form_field_lon_id, marker_style) {
    // Initializing the map
	var map = L.map(map_id)
        .setView([47.15, 2.25], 5)
        .setMaxBounds([[42.19, 8.5], [51.5, -5]]);

    // Loading the tiles
	L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=' + mapboxApiKey, {
		maxZoom: 18,
		minZoom: 5,
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		id: 'mapbox/streets-v11',
		tileSize: 512,
		zoomOffset: -1
	}).addTo(map);

    // Loading the geocoder
    var geocoderOptions  = {
        url: "https://api.openrouteservice.org/geocode/",
        params: {
        'boundary.country': 'FRA'
        },
        position: 'topright',
        markers: false
        }

    var geocoder = L.control.geocoder(orsApiKey, geocoderOptions);
    geocoder.addTo(map);

    var markers = L.layerGroup();
    map.addLayer(markers);

    function setMarker(lat, lon){
        markers.clearLayers();
        var marker = L.marker([lat, lon]).addTo(map);
        if (marker_style == 'start'){marker._icon.classList.add("start_marker")}
        else if (marker_style == 'end'){marker._icon.classList.add("end_marker")};
        markers.addLayer(marker);

        document.getElementById(form_field_lat_id).value = lat;
        document.getElementById(form_field_lon_id).value = lon;

        enableSubmitButton('submit')
    }

    // If coordinates are given, add a marker and update the form field
    if ((document.getElementById(form_field_lat_id).value !== '')
                && (document.getElementById(form_field_lon_id).value !== '')) {
        setMarker(document.getElementById(form_field_lat_id).value,
                    document.getElementById(form_field_lon_id).value)
        map.setView([document.getElementById(form_field_lat_id).value,
                    document.getElementById(form_field_lon_id).value], 10)
    }

    // If a geocoding result is selected, add a marker and update the form field
    geocoder.on('select', function (e) {
        var latlng = e.latlng
        setMarker(latlng.lat, latlng.lng)
    });

    // On click, add a marker and update the form field
    map.on('click',
        (e)=>{
            var lat = (e.latlng.lat);
            var lon = (e.latlng.lng);

            setMarker(lat, lon)
        }
    );
}

function resultMap(map_id, route_geometry, motorways_geometries) {
    var map = L.map(map_id);

    // Loading the route geometry
    var polyline = L.Polyline.fromEncoded(route_geometry);
    polyline.setStyle({className: 'non-motorway'})
    polyline.addTo(map);
    map.fitBounds(polyline.getBounds());

    // Loading the motorway parts geometries
    motorways_geometries.forEach(motorway_geometry => {
        L.geoJSON(motorway_geometry, {className: 'motorway'}).addTo(map)
    });

    // Loading the tiles
    L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=' + mapboxApiKey, {
        maxZoom: 18,
        minZoom: 5,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
            'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        id: 'mapbox/streets-v11',
        tileSize: 512,
        zoomOffset: -1
    }).addTo(map);

    // Loading the legend
    L.control.Legend({
                title: ' ',
                position: "bottomleft",
                collapsed: true,
                symbolWidth: 24,
                opacity: 0.8,
                column: 1,
                legends: [{
                    label: "-  Hors autoroute",
                    type: "polyline",
                    color: "#7389AE",
                    fillColor: "#7389AE",
                    weight: 4,
                    layers: polyline
                },{
                    label: "-  Autoroute",
                    type: "polyline",
                    color: "#81D2C7",
                    fillColor: "#81D2C7",
                    weight: 4,
                    layers: polyline
                }]
            })
            .addTo(map);
}