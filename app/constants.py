PROJECTED_CRS_SRID = 2154
WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD = 1  # Maximum distance to attach a motorway element to the route in meter

# Fuel consumptions modification factors
CONSUMPTION_REDUCTION_FACTOR_110_130 = 0.25
CONSUMPTION_FACTOR_130 = 1.1
CONSUMPTION_FACTOR_110 = (1 - CONSUMPTION_REDUCTION_FACTOR_110_130) * CONSUMPTION_FACTOR_130

# Consumption bounds for data validation (in l/100km)
MINIMUM_CONSUMPTION = 1
MAXIMUM_CONSUMPTION = 30

VEHICLE_TYPES = ['Moto', 'Citadine', 'Compacte', 'Berline', 'SUV', 'Familiale']
FUEL_TYPES = ['Diesel', 'Essence']
# kg of CO2 emitted per liter of fuel
# source: https://www.bilans-ges.ademe.fr/documentation/UPLOAD_DOC_FR/index.htm?new_liquides.htm
FUEL_CO2_EMISSIONS = {
    'Diesel': 3.10,
    'Essence': 2.75
}

# Fuel consumption per fuel type and vehicle type in l/100km
DEFAULT_FUEL_CONSUMPTION_PER_VEHICLE = {
    'Moto': {
        'Diesel': 4.5,
        'Essence': 5.4
    },
    'Citadine': {
        'Diesel': 4.8,
        'Essence': 5.4
    },
    'Compacte': {
        'Diesel': 6.0,
        'Essence': 6.7
    },
    'Berline': {
        'Diesel': 6.7,
        'Essence': 8.0
    },
    'SUV': {
        'Diesel': 7.3,
        'Essence': 8.2
    },
    'Familiale': {
        'Diesel': 7.4,
        'Essence': 8.5
    }
}
