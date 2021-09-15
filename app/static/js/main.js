function formMap(map_id, form_field_lat_id, form_field_lon_id, lat, lon, marker_style) {
    // Initializing the map
	var map = L.map(map_id).setView([47.15, 2.25], 5);

    // Loading the tiles
	L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=' + mapbox_api_key, {
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

    var geocoder = L.control.geocoder(ors_api_key, geocoderOptions);
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
    }


    // If coordinates are given, add a marker and update the form field
    if ((lat !== undefined) && ((lon !== undefined))) {
        setMarker(lat, lon)
        map.setView([lat, lon], 10)
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
    polyline.setStyle({"color": "#E8AE68", "weight": 4})
    polyline.addTo(map);
    map.fitBounds(polyline.getBounds());

    // Loading the motorway parts geometries
    motorways_geometries.forEach(motorway_geometry => {
        L.geoJSON(JSON.parse(motorway_geometry), {"color": "#DB5A42", "weight": 4}).addTo(map)
    });

    // Loading the tiles
    L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=' + mapbox_api_key, {
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
                    color: "#E8AE68",
                    fillColor: "#E8AE68",
                    weight: 4,
                    layers: polyline
                },{
                    label: "-  Autoroute",
                    type: "polyline",
                    color: "#DB5A42",
                    fillColor: "#DB5A42",
                    weight: 4,
                    layers: polyline
                }]
            })
            .addTo(map);
}